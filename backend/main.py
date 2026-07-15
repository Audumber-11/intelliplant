import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any, TypeVar, Generic
import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

from config import settings
from database import (
    engine, AsyncSessionLocal, get_db, init_db, close_db,
    chroma_client, get_chroma_collection, init_chroma,
    check_db_health, check_chroma_health
)
from models import Base
from schemas import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import ingestion and RAG modules
from ingestion import (
    ingest_document, get_all_documents,
    delete_document, get_collection_stats
)
from rag_engine import query_knowledge_base, get_entity_relationships

# ==================== NEW AGENT INITIALIZATION ====================
# Global singleton agent instances (stateful agents)
from agents.cctv import CCTVAgent
from agents.iot_gateway import IoTGateway
from agents.knowledge_graph import KnowledgeGraphBuilder
from agents.knowledge_graph.schemas import NodeType as KGNodeType, EdgeType as KGEdgeType
from agents.orchestrator import AgentOrchestrator, MonitoringConfig

cctv_agent = CCTVAgent(use_mock=True)
iot_gateway = IoTGateway()
kg_builder = KnowledgeGraphBuilder()
orchestrator = AgentOrchestrator(MonitoringConfig(interval_seconds=60))


async def seed_knowledge_graph():
    """Seed the knowledge graph from existing database data."""
    from sqlalchemy import select, text

    try:
        async with AsyncSessionLocal() as db:
            from models import PlantAsset, Permit, Incident, Sensor, RiskZone, User

            result = await db.execute(select(PlantAsset))
            assets = result.scalars().all()
            for a in assets:
                zone_name = getattr(a, "zone", None) or getattr(a, "area", None) or "unknown"
                kg_builder.add_equipment(
                    str(a.id) if hasattr(a, "id") else str(a.asset_id) if hasattr(a, "asset_id") else "unknown",
                    getattr(a, "name", "Unknown Asset") or "Unknown",
                    {"type": getattr(a, "asset_type", None), "status": getattr(a, "status", None)},
                )
                if zone_name:
                    kg_builder.add_zone(zone_name, zone_name)
                    kg_builder.add_relation("eq", str(a.id), "zone", zone_name, KGEdgeType.LOCATED_IN)

            result = await db.execute(select(RiskZone))
            zones = result.scalars().all()
            for z in zones:
                zone_id = getattr(z, "zone_id", None) or str(z.id) if hasattr(z, "id") else "unknown"
                zone_name = getattr(z, "name", None) or getattr(z, "zone_id", None) or "unknown"
                risk = getattr(z, "risk_level", None) or "low"
                kg_builder.add_zone(zone_id, zone_name, risk)

            result = await db.execute(select(Permit))
            permits = result.scalars().all()
            for p in permits:
                zone = getattr(p, "location", None) or getattr(p, "zone", None) or None
                kg_builder.add_permit(
                    str(p.id) if hasattr(p, "id") else "unknown",
                    getattr(p, "title", getattr(p, "work_description", "Unknown Permit")) or "Unknown",
                    zone,
                    {"status": getattr(p, "status", None), "type": getattr(p, "permit_type", None)},
                )

            result = await db.execute(select(Incident))
            incidents = result.scalars().all()
            for i in incidents:
                zone = getattr(i, "location", None) or getattr(i, "zone", None) or None
                kg_builder.add_incident(
                    str(i.id) if hasattr(i, "id") else "unknown",
                    getattr(i, "title", "Unknown Incident") or "Unknown",
                    getattr(i, "severity", "medium") or "medium",
                    zone,
                    {"status": getattr(i, "status", None), "category": getattr(i, "category", None)},
                )

            result = await db.execute(select(Sensor))
            sensors = result.scalars().all()
            for s in sensors:
                zone = getattr(s, "location", None) or getattr(s, "zone", None) or None
                kg_builder.add_sensor(
                    str(s.id) if hasattr(s, "id") else "unknown",
                    getattr(s, "name", "Unknown Sensor") or "Unknown",
                    zone,
                    {"type": getattr(s, "sensor_type", None), "status": getattr(s, "status", None)},
                )

            result = await db.execute(select(User))
            users = result.scalars().all()
            for u in users:
                kg_builder.add_personnel(
                    str(u.id) if hasattr(u, "id") else "unknown",
                    getattr(u, "full_name", getattr(u, "username", "Unknown")) or "Unknown",
                    getattr(u, "role", "operator") or "operator",
                )

        logger.info(f"Knowledge graph seeded: {kg_builder.get_stats().total_nodes} nodes, {kg_builder.get_stats().total_edges} edges")
    except Exception as e:
        logger.warning(f"Knowledge graph seed partial: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IntelliPlant Safety Intelligence Platform...")
    await init_db()
    await init_chroma()
    
    stats = get_collection_stats()
    logger.info(f"Documents: {stats['total_documents']} | Chunks: {stats['total_chunks']}")
    logger.info(f"API Key configured: {'YES' if settings.anthropic_api_key else 'NO'}")

    # Start new agents
    try:
        await cctv_agent.start_monitoring(use_webcam=False)
        await iot_gateway.start()
        await seed_knowledge_graph()
        logger.info("New agents initialized: CCTV, IoT Gateway, Knowledge Graph")
    except Exception as e:
        logger.warning(f"Agent initialization partial: {e}")

    logger.info("Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    cctv_agent.stop()
    await iot_gateway.stop()
    orchestrator.stop()
    await close_db()
    logger.info("Platform stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Industrial Safety Intelligence Platform - AI-Powered Zero-Harm Operations",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HEALTH CHECK ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    db_healthy = await check_db_health()
    chroma_healthy = await check_chroma_health()
    
    return HealthResponse(
        status="healthy" if db_healthy and chroma_healthy else "degraded",
        version=settings.app_version,
        database="connected" if db_healthy else "disconnected",
        chromadb="connected" if chroma_healthy else "disconnected",
        redis="connected",  # TODO: Add Redis check
        timestamp=datetime.utcnow()
    )


# ==================== DOCUMENT INGESTION (Existing) ====================

@app.post("/upload", response_model=FileUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted")
    
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File too large (max 20MB)")
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        result = ingest_document(tmp_path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        result["document_name"] = file.filename
        return FileUploadResponse(
            filename=file.filename,
            size=len(contents),
            content_type="application/pdf",
            document_id=result.get("document_name")
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(req: KnowledgeQuery):
    """Query the knowledge base using RAG."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    try:
        return query_knowledge_base(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """List all indexed documents."""
    return {"documents": get_all_documents(), "stats": get_collection_stats()}


@app.get("/knowledge-graph")
async def get_knowledge_graph():
    """Get knowledge graph of documents and equipment."""
    return get_entity_relationships()


@app.post("/ingest-samples")
async def ingest_sample_documents():
    """Ingest all sample documents from sample_docs folder."""
    sample_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sample_docs")
    )
    if not os.path.isdir(sample_dir):
        raise HTTPException(
            status_code=404,
            detail="sample_docs folder not found. Run: python3 create_sample_docs.py"
        )
    
    pdfs = [f for f in os.listdir(sample_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        raise HTTPException(
            status_code=404,
            detail="No PDFs found. Run: python3 create_sample_docs.py"
        )
    
    ingested = []
    total_chunks = 0
    for pdf in sorted(pdfs):
        r = ingest_document(os.path.join(sample_dir, pdf))
        if "error" not in r:
            ingested.append(pdf)
            total_chunks += r.get("chunks_created", 0)
    
    return {
        "ingested": ingested,
        "total_chunks": total_chunks,
        "message": f"Indexed {len(ingested)} of {len(pdfs)} documents"
    }


@app.delete("/documents/{document_name:path}")
async def delete_document_endpoint(document_name: str):
    """Delete a document and all its chunks."""
    if not delete_document(document_name):
        raise HTTPException(status_code=404, detail=f"Document not found: {document_name}")
    return {"success": True, "message": f"Deleted {document_name}"}


# ==================== ASSETS API ====================

@app.get("/api/assets", response_model=PaginatedResponse[AssetResponse])
async def list_assets(
    asset_type: Optional[AssetType] = None,
    unit_area: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_critical: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List plant assets with filtering."""
    from sqlalchemy import select, func
    from models import PlantAsset
    
    query = select(PlantAsset)
    
    if asset_type:
        query = query.where(PlantAsset.asset_type == asset_type)
    if unit_area:
        query = query.where(PlantAsset.unit_area == unit_area)
    if is_active is not None:
        query = query.where(PlantAsset.is_active == is_active)
    if is_critical is not None:
        query = query.where(PlantAsset.is_critical == is_critical)
    if search:
        query = query.where(
            (PlantAsset.tag.ilike(f"%{search}%")) |
            (PlantAsset.name.ilike(f"%{search}%"))
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return PaginatedResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/assets/{asset_id}", response_model=AssetWithRelations)
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get asset with full details including sensors, permits, incidents."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models import PlantAsset, Sensor, Permit, Incident
    
    query = select(PlantAsset).options(
        selectinload(PlantAsset.sensors),
        selectinload(PlantAsset.permits),
        selectinload(PlantAsset.incidents),
    ).where(PlantAsset.id == asset_id)
    
    result = await db.execute(query)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Count active permits and open incidents
    active_permits = sum(1 for p in asset.permits if p.status in [PermitStatus.APPROVED, PermitStatus.ACTIVE])
    open_incidents = sum(1 for i in asset.incidents if i.status != IncidentStatus.CLOSED)
    
    # TODO: Get current risk level from risk engine
    risk_level = RiskLevel.LOW
    
    return AssetWithRelations(
        **AssetResponse.model_validate(asset).model_dump(),
        sensors=[SensorResponse.model_validate(s) for s in asset.sensors],
        active_permits=active_permits,
        open_incidents=open_incidents,
        current_risk_level=risk_level
    )


@app.post("/api/assets", response_model=AssetResponse, status_code=201)
async def create_asset(asset: AssetCreate, db: AsyncSession = Depends(get_db)):
    """Create a new plant asset."""
    from models import PlantAsset
    
    db_asset = PlantAsset(**asset.model_dump())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return AssetResponse.model_validate(db_asset)


@app.patch("/api/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: UUID, asset_update: AssetUpdate, db: AsyncSession = Depends(get_db)):
    """Update an asset."""
    from sqlalchemy import select
    from models import PlantAsset
    
    result = await db.execute(select(PlantAsset).where(PlantAsset.id == asset_id))
    db_asset = result.scalar_one_or_none()
    
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    db_asset.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_asset)
    return AssetResponse.model_validate(db_asset)


# ==================== SENSORS API ====================

@app.get("/api/sensors", response_model=PaginatedResponse[SensorResponse])
async def list_sensors(
    asset_id: Optional[UUID] = None,
    sensor_type: Optional[SensorType] = None,
    is_active: Optional[bool] = None,
    is_safety_critical: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List sensors with filtering."""
    from sqlalchemy import select, func
    from models import Sensor
    
    query = select(Sensor)
    
    if asset_id:
        query = query.where(Sensor.asset_id == asset_id)
    if sensor_type:
        query = query.where(Sensor.sensor_type == sensor_type)
    if is_active is not None:
        query = query.where(Sensor.is_active == is_active)
    if is_safety_critical is not None:
        query = query.where(Sensor.is_safety_critical == is_safety_critical)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    sensors = result.scalars().all()
    
    return PaginatedResponse(
        items=[SensorResponse.model_validate(s) for s in sensors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.post("/api/sensors/readings/bulk")
async def ingest_sensor_readings_bulk(
    readings: SensorReadingBulk,
    db: AsyncSession = Depends(get_db)
):
    """Bulk ingest sensor readings - called by IoT gateway."""
    from models import SensorReading
    
    db_readings = [
        SensorReading(**r.model_dump()) for r in readings.readings
    ]
    db.add_all(db_readings)
    await db.commit()
    
    # TODO: Trigger risk evaluation for new readings
    # This would publish to Kafka/Redis for the risk engine to consume
    
    return {"success": True, "count": len(db_readings)}


@app.get("/api/sensors/{sensor_id}/readings", response_model=PaginatedResponse[SensorReadingResponse])
async def get_sensor_readings(
    sensor_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get historical sensor readings."""
    from sqlalchemy import select, func
    from models import SensorReading
    
    query = select(SensorReading).where(SensorReading.sensor_id == sensor_id)
    
    if start_time:
        query = query.where(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.where(SensorReading.timestamp <= end_time)
    
    query = query.order_by(SensorReading.timestamp.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    readings = result.scalars().all()
    
    return PaginatedResponse(
        items=[SensorReadingResponse.model_validate(r) for r in readings],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


# ==================== PERMITS API ====================

@app.get("/api/permits", response_model=PaginatedResponse[PermitResponse])
async def list_permits(
    permit_type: Optional[PermitType] = None,
    status: Optional[PermitStatus] = None,
    asset_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List permits with filtering."""
    from sqlalchemy import select, func
    from models import Permit
    
    query = select(Permit)
    
    if permit_type:
        query = query.where(Permit.permit_type == permit_type)
    if status:
        query = query.where(Permit.status == status)
    if asset_id:
        query = query.where(Permit.asset_id == asset_id)
    if date_from:
        query = query.where(Permit.requested_start >= date_from)
    if date_to:
        query = query.where(Permit.requested_end <= date_to)
    if search:
        query = query.where(
            (Permit.permit_number.ilike(f"%{search}%")) |
            (Permit.title.ilike(f"%{search}%"))
        )
    
    query = query.order_by(Permit.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    permits = result.scalars().all()
    
    return PaginatedResponse(
        items=[PermitResponse.model_validate(p) for p in permits],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/permits/active", response_model=List[PermitResponse])
async def get_active_permits(db: AsyncSession = Depends(get_db)):
    """Get all currently active permits."""
    from sqlalchemy import select
    from models import Permit, PermitStatus
    
    result = await db.execute(
        select(Permit).where(
            Permit.status.in_([PermitStatus.APPROVED, PermitStatus.ACTIVE])
        ).order_by(Permit.requested_start)
    )
    permits = result.scalars().all()
    return [PermitResponse.model_validate(p) for p in permits]


@app.get("/api/permits/{permit_id}", response_model=PermitWithDetails)
async def get_permit(permit_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get permit with full details including conflicts."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models import Permit, PlantAsset, User, GasTest, PermitInspection
    
    query = select(Permit).options(
        selectinload(Permit.asset),
        selectinload(Permit.creator),
        selectinload(Permit.approver),
        selectinload(Permit.gas_tests),
        selectinload(Permit.inspections),
    ).where(Permit.id == permit_id)
    
    result = await db.execute(query)
    permit = result.scalar_one_or_none()
    
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    # Check for conflicts
    conflicts = []  # TODO: Implement conflict detection
    
    return PermitWithDetails(
        **PermitResponse.model_validate(permit).model_dump(),
        asset=AssetResponse.model_validate(permit.asset) if permit.asset else None,
        creator=UserResponse.model_validate(permit.creator) if permit.creator else None,
        approver=UserResponse.model_validate(permit.approver) if permit.approver else None,
        conflicts=conflicts,
        risk_assessment=None  # TODO: Link to risk assessment
    )


@app.post("/api/permits", response_model=PermitResponse, status_code=201)
async def create_permit(permit: PermitCreate, db: AsyncSession = Depends(get_db)):
    """Create a new permit request."""
    from models import Permit, PermitStatus
    from sqlalchemy import select, func
    
    # Generate permit number
    today = datetime.utcnow().strftime("%Y%m%d")
    result = await db.execute(
        select(func.count(Permit.id)).where(
            Permit.permit_number.like(f"PMT-{today}-%")
        )
    )
    count = result.scalar() + 1
    permit_number = f"PMT-{today}-{count:04d}"
    
    db_permit = Permit(
        **permit.model_dump(exclude={"conditions"}),
        permit_number=permit_number,
        status=PermitStatus.DRAFT,
        created_by_id=permit.created_by_id if hasattr(permit, 'created_by_id') else uuid4(),  # TODO: Get from auth
    )
    db.add(db_permit)
    await db.commit()
    await db.refresh(db_permit)
    
    # TODO: Trigger conflict detection
    # TODO: Notify approvers
    
    return PermitResponse.model_validate(db_permit)


@app.post("/api/permits/{permit_id}/approve", response_model=PermitResponse)
async def approve_permit(permit_id: UUID, approval: PermitApproval, db: AsyncSession = Depends(get_db)):
    """Approve a permit."""
    from sqlalchemy import select
    from models import Permit, PermitStatus
    
    result = await db.execute(select(Permit).where(Permit.id == permit_id))
    permit = result.scalar_one_or_none()
    
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    if permit.status != PermitStatus.UNDER_REVIEW:
        raise HTTPException(status_code=400, detail=f"Permit must be under review, current status: {permit.status}")
    
    permit.status = PermitStatus.APPROVED
    permit.approved_by_id = approval.approved_by_id
    permit.approved_at = approval.approved_at
    permit.conditions = [c.model_dump() for c in approval.conditions] if approval.conditions else []
    
    await db.commit()
    await db.refresh(permit)
    
    # TODO: Notify relevant personnel
    # TODO: Check for conflicts with active permits
    
    return PermitResponse.model_validate(permit)


@app.post("/api/permits/{permit_id}/activate", response_model=PermitResponse)
async def activate_permit(permit_id: UUID, db: AsyncSession = Depends(get_db)):
    """Activate an approved permit (start work)."""
    from sqlalchemy import select
    from models import Permit, PermitStatus
    
    result = await db.execute(select(Permit).where(Permit.id == permit_id))
    permit = result.scalar_one_or_none()
    
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    if permit.status != PermitStatus.APPROVED:
        raise HTTPException(status_code=400, detail=f"Permit must be approved, current status: {permit.status}")
    
    # Check gas test validity for hot work
    if permit.permit_type == PermitType.HOT_WORK and permit.gas_test_required:
        # TODO: Check if valid gas test exists
        pass
    
    permit.status = PermitStatus.ACTIVE
    permit.actual_start = datetime.utcnow()
    
    await db.commit()
    await db.refresh(permit)
    
    # TODO: Notify risk engine for real-time monitoring
    # TODO: Update geospatial heatmap
    
    return PermitResponse.model_validate(permit)


@app.post("/api/permits/{permit_id}/close", response_model=PermitResponse)
async def close_permit(permit_id: UUID, db: AsyncSession = Depends(get_db)):
    """Close a permit (work completed)."""
    from sqlalchemy import select
    from models import Permit, PermitStatus
    
    result = await db.execute(select(Permit).where(Permit.id == permit_id))
    permit = result.scalar_one_or_none()
    
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    if permit.status != PermitStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Permit must be active, current status: {permit.status}")
    
    permit.status = PermitStatus.CLOSED
    permit.actual_end = datetime.utcnow()
    
    await db.commit()
    await db.refresh(permit)
    
    return PermitResponse.model_validate(permit)


# ==================== INCIDENTS API ====================

@app.get("/api/incidents", response_model=PaginatedResponse[IncidentResponse])
async def list_incidents(
    severity: Optional[IncidentSeverity] = None,
    status: Optional[IncidentStatus] = None,
    asset_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List incidents with filtering."""
    from sqlalchemy import select, func
    from models import Incident
    
    query = select(Incident)
    
    if severity:
        query = query.where(Incident.severity == severity)
    if status:
        query = query.where(Incident.status == status)
    if asset_id:
        query = query.where(Incident.asset_id == asset_id)
    if date_from:
        query = query.where(Incident.occurred_at >= date_from)
    if date_to:
        query = query.where(Incident.occurred_at <= date_to)
    if search:
        query = query.where(
            (Incident.incident_number.ilike(f"%{search}%")) |
            (Incident.title.ilike(f"%{search}%")) |
            (Incident.description.ilike(f"%{search}%"))
        )
    
    query = query.order_by(Incident.occurred_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    incidents = result.scalars().all()
    
    return PaginatedResponse(
        items=[IncidentResponse.model_validate(i) for i in incidents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(incident: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new incident report."""
    from models import Incident, IncidentStatus
    from sqlalchemy import select, func
    
    # Generate incident number
    today = datetime.utcnow().strftime("%Y%m%d")
    result = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.incident_number.like(f"INC-{today}-%")
        )
    )
    count = result.scalar() + 1
    incident_number = f"INC-{today}-{count:04d}"
    
    db_incident = Incident(
        **incident.model_dump(),
        incident_number=incident_number,
        status=IncidentStatus.REPORTED,
        reported_at=datetime.utcnow(),
    )
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    
    # TODO: Trigger emergency response if severity >= CRITICAL
    # TODO: Notify safety officers
    # TODO: Create initial investigation task
    
    return IncidentResponse.model_validate(db_incident)


@app.get("/api/incidents/{incident_id}", response_model=IncidentWithDetails)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get incident with full details."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models import Incident, PlantAsset, User, IncidentAttachment
    
    query = select(Incident).options(
        selectinload(Incident.asset),
        selectinload(Incident.assignee),
        selectinload(Incident.investigator),
        selectinload(Incident.attachments),
    ).where(Incident.id == incident_id)
    
    result = await db.execute(query)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # TODO: Find similar incidents using RAG
    similar_incidents = []
    
    return IncidentWithDetails(
        **IncidentResponse.model_validate(incident).model_dump(),
        asset=AssetResponse.model_validate(incident.asset) if incident.asset else None,
        reporter=UserResponse.model_validate(incident.assignee) if incident.assignee else None,
        assignee=UserResponse.model_validate(incident.assignee) if incident.assignee else None,
        similar_incidents=similar_incidents
    )


# ==================== RISK ENGINE API ====================

@app.get("/api/risk/current", response_model=List[RiskEventResponse])
async def get_current_risk_events(
    risk_level: Optional[RiskLevel] = None,
    asset_id: Optional[UUID] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get current active risk events."""
    from sqlalchemy import select
    from models import RiskEvent
    
    query = select(RiskEvent).where(RiskEvent.status == "active")
    
    if risk_level:
        query = query.where(RiskEvent.risk_level == risk_level)
    if asset_id:
        query = query.where(RiskEvent.asset_id == asset_id)
    
    query = query.order_by(RiskEvent.detected_at.desc()).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [RiskEventResponse.model_validate(e) for e in events]


@app.get("/api/risk/history", response_model=PaginatedResponse[RiskEventResponse])
async def get_risk_history(
    risk_level: Optional[RiskLevel] = None,
    event_type: Optional[str] = None,
    asset_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get historical risk events."""
    from sqlalchemy import select, func
    from models import RiskEvent
    
    query = select(RiskEvent)
    
    if risk_level:
        query = query.where(RiskEvent.risk_level == risk_level)
    if event_type:
        query = query.where(RiskEvent.event_type == event_type)
    if asset_id:
        query = query.where(RiskEvent.asset_id == asset_id)
    if date_from:
        query = query.where(RiskEvent.detected_at >= date_from)
    if date_to:
        query = query.where(RiskEvent.detected_at <= date_to)
    
    query = query.order_by(RiskEvent.detected_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    events = result.scalars().all()
    
    return PaginatedResponse(
        items=[RiskEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.post("/api/risk/events/{event_id}/acknowledge", response_model=RiskEventResponse)
async def acknowledge_risk_event(
    event_id: UUID,
    ack: RiskEventAcknowledge,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge a risk event."""
    from sqlalchemy import select
    from models import RiskEvent
    
    result = await db.execute(select(RiskEvent).where(RiskEvent.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")
    
    event.status = "acknowledged"
    event.acknowledged_at = datetime.utcnow()
    event.acknowledged_by_id = ack.acknowledged_by_id
    
    await db.commit()
    await db.refresh(event)
    
    return RiskEventResponse.model_validate(event)


# ==================== RISK ENGINE ANALYSIS API ====================

@app.post("/api/risk/analyze")
async def analyze_asset_risk(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Run compound risk analysis on a specific asset."""
    from sqlalchemy import select, func
    from models import PlantAsset, Sensor, SensorReading, Permit, Incident
    from agents.risk_engine.correlation_engine import CorrelationEngine, SensorReading as CReading
    from agents.risk_engine.data_fusion import DataFusionEngine
    from agents.risk_engine.rules_engine import RulesEngine

    # Get asset
    result = await db.execute(select(PlantAsset).where(PlantAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Get recent sensor readings
    readings_result = await db.execute(
        select(SensorReading)
        .join(Sensor, SensorReading.sensor_id == Sensor.id)
        .where(Sensor.asset_id == asset_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(100)
    )
    readings = readings_result.scalars().all()

    # Get sensor configs
    sensors_result = await db.execute(
        select(Sensor).where(Sensor.asset_id == asset_id)
    )
    sensors = {str(s.id): s for s in sensors_result.scalars().all()}

    # Correlate readings
    ce = CorrelationEngine()
    correlated_risks = []
    for r in readings:
        sensor = sensors.get(str(r.sensor_id))
        if sensor:
            cr = CReading(
                sensor_id=str(sensor.id),
                sensor_type=sensor.sensor_type.value,
                value=r.value,
                timestamp=r.timestamp,
                asset_id=str(asset_id),
                alarm_low=sensor.alarm_low,
                alarm_high=sensor.alarm_high,
                alarm_critical_low=sensor.alarm_critical_low,
                alarm_critical_high=sensor.alarm_critical_high,
            )
            risks = ce.ingest_reading(cr)
            correlated_risks.extend([rr.__dict__ for rr in risks])

    # Fuse data
    fe = DataFusionEngine()
    sensor_data = {}
    for r in readings[:20]:
        sensor = sensors.get(str(r.sensor_id))
        if sensor:
            sensor_data[sensor.sensor_type.value] = r.value

    context = fe.fuse_asset_data(
        str(asset_id),
        sensor_data={"readings": sensor_data},
    )

    # Evaluate rules
    re = RulesEngine()
    rule_context = {**sensor_data}
    rule_results = re.evaluate(rule_context)

    triggered_rules = [rr for rr in rule_results if rr.triggered]

    return {
        "asset_id": str(asset_id),
        "asset_tag": asset.tag,
        "asset_name": asset.name,
        "overall_risk_score": context.overall_risk_score,
        "risk_level": fe.get_risk_level(context.overall_risk_score),
        "risk_factors": context.risk_factors,
        "correlated_risks": correlated_risks,
        "triggered_rules": [
            {
                "rule_id": rr.rule_id,
                "name": rr.rule_name,
                "severity": rr.severity.value,
                "category": rr.category.value,
            }
            for rr in triggered_rules
        ],
        "active_sensors": len(sensors),
        "recent_readings": len(readings),
    }


@app.post("/api/risk/simulate")
async def simulate_risk_scenario(
    scenario: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate a risk scenario for training/planning purposes.
    Pass sensor values and context to see what risks would be detected.
    """
    from agents.risk_engine.correlation_engine import CorrelationEngine
    from agents.risk_engine.data_fusion import DataFusionEngine
    from agents.risk_engine.rules_engine import RulesEngine

    ce = CorrelationEngine()
    fe = DataFusionEngine()
    re = RulesEngine()

    # Simulate sensor readings
    simulated_risks = []
    if "sensor_readings" in scenario:
        from agents.risk_engine.correlation_engine import SensorReading as CReading
        from datetime import datetime

        for reading_data in scenario["sensor_readings"]:
            sr = CReading(
                sensor_id=reading_data.get("sensor_id", "simulated"),
                sensor_type=reading_data.get("type", "unknown"),
                value=reading_data.get("value", 0),
                timestamp=datetime.utcnow(),
                asset_id=scenario.get("asset_id", "simulated"),
                alarm_low=reading_data.get("alarm_low"),
                alarm_high=reading_data.get("alarm_high"),
                alarm_critical_low=reading_data.get("alarm_critical_low"),
                alarm_critical_high=reading_data.get("alarm_critical_high"),
            )
            risks = ce.ingest_reading(sr)
            simulated_risks.extend([r.__dict__ for r in risks])

    # Fuse data
    context = fe.fuse_asset_data(
        scenario.get("asset_id", "simulated"),
        sensor_data={"readings": {r.get("type"): r.get("value") for r in scenario.get("sensor_readings", [])}},
    )

    # Evaluate rules
    rule_context = {r.get("type"): r.get("value") for r in scenario.get("sensor_readings", [])}
    rule_results = re.evaluate(rule_context)
    triggered_rules = [rr for rr in rule_results if rr.triggered]

    return {
        "scenario": scenario.get("name", "Unnamed Scenario"),
        "overall_risk_score": context.overall_risk_score,
        "risk_level": fe.get_risk_level(context.overall_risk_score),
        "correlated_risks": simulated_risks,
        "triggered_rules": [
            {
                "rule_id": rr.rule_id,
                "name": rr.rule_name,
                "severity": rr.severity.value,
                "actions": re.rules[rr.rule_id].actions if rr.rule_id in re.rules else [],
            }
            for rr in triggered_rules
        ],
        "recommended_actions": list(set(
            action
            for rr in triggered_rules
            if rr.rule_id in re.rules
            for action in re.rules[rr.rule_id].actions
        )),
    }


@app.get("/api/risk/rules")
async def list_risk_rules(
    category: Optional[str] = None,
    asset_type: Optional[str] = None,
):
    """List all configured risk rules."""
    from agents.risk_engine.rules_engine import RulesEngine, RuleCategory

    re = RulesEngine()
    cat = RuleCategory(category) if category else None
    rules = re.get_applicable_rules(asset_type=asset_type, category=cat)

    return {
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "category": r.category.value,
                "severity": r.severity.value,
                "description": r.description,
                "condition": r.condition,
                "actions": r.actions,
                "enabled": r.enabled,
                "applicable_asset_types": r.applicable_asset_types,
            }
            for r in rules
        ],
        "total": len(rules),
    }


# ==================== EMERGENCY API ====================

@app.post("/api/emergency/declare", response_model=EmergencyIncidentResponse, status_code=201)
async def declare_emergency(emergency: EmergencyIncidentCreate, db: AsyncSession = Depends(get_db)):
    """Declare an emergency incident and auto-generate ICS response plan."""
    from models import EmergencyIncident
    from sqlalchemy import select, func
    
    # Generate incident number
    today = datetime.utcnow().strftime("%Y%m%d")
    result = await db.execute(
        select(func.count(EmergencyIncident.id)).where(
            EmergencyIncident.incident_number.like(f"EMG-{today}-%")
        )
    )
    count = result.scalar() + 1
    incident_number = f"EMG-{today}-{count:04d}"
    
    db_emergency = EmergencyIncident(
        **emergency.model_dump(),
        incident_number=incident_number,
        declared_at=datetime.utcnow(),
        status="active",
    )
    db.add(db_emergency)
    await db.commit()
    await db.refresh(db_emergency)
    
    # TODO: Auto-generate ICS forms (201, 202, 203, 204)
    # TODO: Trigger emergency response orchestrator
    # TODO: Activate muster points
    # TODO: Notify external agencies
    
    return EmergencyIncidentResponse.model_validate(db_emergency)


@app.get("/api/emergency/active", response_model=List[EmergencyIncidentResponse])
async def get_active_emergencies(db: AsyncSession = Depends(get_db)):
    """Get all active emergencies."""
    from sqlalchemy import select
    from models import EmergencyIncident
    
    result = await db.execute(
        select(EmergencyIncident).where(
            EmergencyIncident.status.in_(["active", "contained"])
        ).order_by(EmergencyIncident.declared_at.desc())
    )
    emergencies = result.scalars().all()
    
    return [EmergencyIncidentResponse.model_validate(e) for e in emergencies]


@app.get("/api/emergency/{emergency_id}", response_model=EmergencyIncidentResponse)
async def get_emergency(emergency_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get emergency incident details."""
    from sqlalchemy import select
    from models import EmergencyIncident
    
    result = await db.execute(
        select(EmergencyIncident).where(EmergencyIncident.id == emergency_id)
    )
    emergency = result.scalar_one_or_none()
    
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    
    return EmergencyIncidentResponse.model_validate(emergency)


# ==================== AUDIT API ====================

@app.post("/api/audits", response_model=AuditResponse, status_code=201)
async def create_audit(audit: AuditCreate, db: AsyncSession = Depends(get_db)):
    """Create a new audit."""
    from models import Audit
    from sqlalchemy import select, func
    
    today = datetime.utcnow().strftime("%Y%m%d")
    result = await db.execute(
        select(func.count(Audit.id)).where(
            Audit.audit_number.like(f"AUD-{today}-%")
        )
    )
    count = result.scalar() + 1
    audit_number = f"AUD-{today}-{count:04d}"
    
    db_audit = Audit(
        **audit.model_dump(),
        audit_number=audit_number,
        status="planned",
        created_at=datetime.utcnow(),
    )
    db.add(db_audit)
    await db.commit()
    await db.refresh(db_audit)
    
    # TODO: Auto-generate checklist based on standard
    
    return AuditResponse.model_validate(db_audit)


@app.get("/api/audits", response_model=PaginatedResponse[AuditResponse])
async def list_audits(
    standard: Optional[AuditStandardType] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List audits."""
    from sqlalchemy import select, func
    from models import Audit
    
    query = select(Audit)
    
    if standard:
        query = query.where(Audit.standard == standard)
    if status:
        query = query.where(Audit.status == status)
    
    query = query.order_by(Audit.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return PaginatedResponse(
        items=[AuditResponse.model_validate(a) for a in audits],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


# ==================== GEOSPATIAL HEATMAP API ====================

@app.get("/api/heatmap/layout")
async def get_plant_layout(db: AsyncSession = Depends(get_db)):
    """Get plant layout as GeoJSON FeatureCollection."""
    from sqlalchemy import select
    from models import PlantAsset, Sensor
    
    assets_result = await db.execute(select(PlantAsset))
    assets = assets_result.scalars().all()
    
    sensors_result = await db.execute(select(Sensor))
    sensors = sensors_result.scalars().all()
    
    features = []
    
    zones = [
        {"name": "Reactor Area", "type": "process_unit", "lat": 28.6142, "lng": 77.2093, "color": "#e74c3c"},
        {"name": "Tank Farm", "type": "storage_tank", "lat": 28.6141, "lng": 77.2102, "color": "#e67e22"},
        {"name": "Compressor Station", "type": "process_unit", "lat": 28.6144, "lng": 77.2082, "color": "#f39c12"},
        {"name": "Control Room", "type": "control_room", "lat": 28.6147, "lng": 77.2105, "color": "#27ae60"},
        {"name": "Muster Point", "type": "muster_point", "lat": 28.6149, "lng": 77.2075, "color": "#2ecc71"},
        {"name": "Fire Hydrant", "type": "fire_hydrant", "lat": 28.6147, "lng": 77.2095, "color": "#e74c3c"},
        {"name": "Workshop", "type": "general", "lat": 28.6136, "lng": 77.2087, "color": "#3498db"},
        {"name": "Parking", "type": "parking", "lat": 28.6131, "lng": 77.2082, "color": "#95a5a6"},
    ]
    
    for z in zones:
        s = 0.0003
        polygon = [
            [z["lng"] - s, z["lat"] - s],
            [z["lng"] + s, z["lat"] - s],
            [z["lng"] + s, z["lat"] + s],
            [z["lng"] - s, z["lat"] + s],
            [z["lng"] - s, z["lat"] - s],
        ]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [polygon]},
            "properties": {"type": "zone", "name": z["name"], "zone_type": z["type"], "color": z["color"]},
        })
    
    for asset in assets:
        lat = asset.latitude or 28.6139
        lng = asset.longitude or 77.209
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {"type": "asset", "id": str(asset.id), "tag": asset.tag, "name": asset.name, "asset_type": asset.asset_type},
        })
    
    for sensor in sensors:
        lat = sensor.latitude or 28.6139
        lng = sensor.longitude or 77.209
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {"type": "sensor", "id": str(sensor.id), "tag": sensor.tag, "sensor_type": sensor.sensor_type},
        })
    
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/heatmap/live")
async def get_live_heatmap(
    grid_size: int = 15,
    db: AsyncSession = Depends(get_db)
):
    """Generate live risk heatmap from current sensor data."""
    from sqlalchemy import select, func
    from models import Sensor, SensorReading, RiskZone, PlantAsset
    from agents.geospatial.heatmap_engine import HeatmapEngine
    
    sensors_result = await db.execute(select(Sensor))
    sensors = sensors_result.scalars().all()
    
    sensor_data = []
    for sensor in sensors:
        latest_query = (
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor.id)
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )
        latest_result = await db.execute(latest_query)
        latest_reading = latest_result.scalar_one_or_none()
        
        value = latest_reading.value if latest_reading else 0.0
        alarm_high = sensor.alarm_high or 100.0
        alarm_critical = sensor.alarm_critical_high or 200.0
        
        if alarm_critical > 0:
            risk_value = min(value / alarm_critical, 1.0)
        elif alarm_high > 0:
            risk_value = min(value / alarm_high, 0.8)
        else:
            risk_value = 0.0
        
        sensor_data.append({
            "sensor_id": str(sensor.id),
            "sensor_tag": sensor.tag,
            "sensor_type": sensor.sensor_type,
            "latitude": sensor.latitude or (28.6139 + hash(sensor.tag) % 50 * 0.00001),
            "longitude": sensor.longitude or (77.209 + hash(sensor.tag + "lng") % 50 * 0.00001),
            "risk_value": round(risk_value, 3),
            "value": value,
        })
    
    engine = HeatmapEngine(grid_size=grid_size)
    heatmap = engine.generate_heatmap(sensor_data)
    
    return heatmap


@app.get("/api/heatmap/zones")
async def get_zone_risks(db: AsyncSession = Depends(get_db)):
    """Get risk assessment for each zone."""
    from sqlalchemy import select
    from models import RiskZone, Sensor, SensorReading
    from agents.geospatial.heatmap_engine import HeatmapEngine
    
    zones_result = await db.execute(select(RiskZone))
    zones = zones_result.scalars().all()
    
    sensors_result = await db.execute(select(Sensor))
    sensors = sensors_result.scalars().all()
    
    engine = HeatmapEngine()
    zone_risks = []
    
    for zone in zones:
        sensor_data = []
        for sensor in sensors:
            latest_query = (
                select(SensorReading)
                .where(SensorReading.sensor_id == sensor.id)
                .order_by(SensorReading.timestamp.desc())
                .limit(1)
            )
            latest_result = await db.execute(latest_query)
            latest_reading = latest_result.scalar_one_or_none()
            
            value = latest_reading.value if latest_reading else 0.0
            alarm_high = sensor.alarm_high or 100.0
            risk_value = min(value / alarm_high, 1.0) if alarm_high > 0 else 0.0
            
            sensor_data.append({
                "sensor_tag": sensor.tag,
                "sensor_type": sensor.sensor_type,
                "latitude": sensor.latitude or 28.6139,
                "longitude": sensor.longitude or 77.209,
                "risk_value": risk_value,
            })
        
        risk_results = engine.generate_sensor_risk_scores(sensor_data, {})
        risk_scores = [r["risk_value"] for r in risk_results] if risk_results else [0.0]
        risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        risk_level = "safe"
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        elif risk_score >= 0.2:
            risk_level = "low"
        
        zone_risks.append({
            "zone_id": str(zone.id),
            "zone_name": zone.name,
            "zone_type": zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type),
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "active_sensors": len(sensors),
            "active_permits": 0,
        })
    
    return zone_risks


@app.get("/api/heatmap/locations")
async def get_asset_locations(db: AsyncSession = Depends(get_db)):
    """Get all asset and personnel locations."""
    from sqlalchemy import select
    from models import PlantAsset
    from agents.geospatial.asset_tracker import AssetTracker
    
    assets_result = await db.execute(select(PlantAsset))
    assets = assets_result.scalars().all()
    
    tracker = AssetTracker()
    asset_locations = tracker.get_asset_locations(assets)
    personnel_locations = tracker.get_personnel_locations()
    
    return {
        "assets": asset_locations,
        "personnel": personnel_locations,
        "zone_occupancy": tracker.get_zone_occupancy(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/heatmap/muster-routes")
async def get_muster_routes():
    """Get emergency muster routes."""
    from agents.geospatial.plant_layout import PlantLayoutManager
    
    manager = PlantLayoutManager()
    routes = manager.generate_muster_routes()
    return routes.model_dump()


@app.websocket("/ws/heatmap")
async def websocket_heatmap(websocket: WebSocket):
    """WebSocket endpoint for real-time heatmap updates."""
    await websocket.accept()
    try:
        while True:
            from sqlalchemy import select
            from models import Sensor, SensorReading
            from agents.geospatial.heatmap_engine import HeatmapEngine
            
            async with AsyncSessionLocal() as db:
                sensors_result = await db.execute(select(Sensor))
                sensors = sensors_result.scalars().all()
                
                sensor_data = []
                for sensor in sensors:
                    latest_query = (
                        select(SensorReading)
                        .where(SensorReading.sensor_id == sensor.id)
                        .order_by(SensorReading.timestamp.desc())
                        .limit(1)
                    )
                    latest_result = await db.execute(latest_query)
                    latest_reading = latest_result.scalar_one_or_none()
                    
                    value = latest_reading.value if latest_reading else 0.0
                    alarm_high = sensor.alarm_high or 100.0
                    risk_value = min(value / alarm_high, 1.0) if alarm_high > 0 else 0.0
                    
                    sensor_data.append({
                        "sensor_tag": sensor.tag,
                        "sensor_type": sensor.sensor_type,
                        "latitude": sensor.latitude or 28.6139,
                        "longitude": sensor.longitude or 77.209,
                        "risk_value": risk_value,
                    })
                
                engine = HeatmapEngine(grid_size=10)
                heatmap = engine.generate_heatmap(sensor_data)
            
            await websocket.send_json(heatmap)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


# ==================== INCIDENT INTELLIGENCE API ====================

@app.get("/api/incidents-analysis/patterns")
async def analyze_incident_patterns(db: AsyncSession = Depends(get_db)):
    """Analyze incident patterns for systemic issues."""
    from sqlalchemy import select
    from models import Incident
    from agents.incident_intel import IncidentPatternEngine
    
    result = await db.execute(select(Incident).order_by(Incident.occurred_at.desc()))
    incidents = result.scalars().all()
    
    incident_dicts = []
    for inc in incidents:
        incident_dicts.append({
            "id": str(inc.id),
            "title": inc.title,
            "description": inc.description or "",
            "category": inc.category or "unknown",
            "severity": inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity),
            "asset_id": str(inc.asset_id) if inc.asset_id else None,
            "occurred_at": inc.occurred_at.isoformat() if inc.occurred_at else None,
            "status": inc.status.value if hasattr(inc.status, 'value') else str(inc.status),
        })
    
    engine = IncidentPatternEngine()
    analysis = engine.analyze_incident_patterns(incident_dicts)
    return analysis


@app.get("/api/incidents/{incident_id}/similar")
async def find_similar_incidents(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    """Find incidents similar to a given incident."""
    from sqlalchemy import select
    from models import Incident
    from agents.incident_intel import IncidentPatternEngine
    
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    all_result = await db.execute(select(Incident).where(Incident.id != incident_id))
    all_incidents = all_result.scalars().all()
    
    target_dict = {
        "title": target.title,
        "category": target.category or "unknown",
        "severity": target.severity.value if hasattr(target.severity, 'value') else str(target.severity),
        "asset_id": str(target.asset_id) if target.asset_id else None,
    }
    
    historical = [{
        "id": str(i.id),
        "title": i.title,
        "category": i.category or "unknown",
        "severity": i.severity.value if hasattr(i.severity, 'value') else str(i.severity),
        "asset_id": str(i.asset_id) if i.asset_id else None,
    } for i in all_incidents]
    
    engine = IncidentPatternEngine()
    similar = engine.find_similar_incidents(target_dict, historical)
    return {"incident_id": str(incident_id), "similar_incidents": similar}


@app.get("/api/incidents-analysis/recurrence-risk")
async def predict_recurrence(db: AsyncSession = Depends(get_db)):
    """Predict recurrence risk for assets with incidents."""
    from sqlalchemy import select
    from models import Incident, PlantAsset
    from agents.incident_intel import IncidentPatternEngine
    
    assets_result = await db.execute(select(PlantAsset))
    assets = assets_result.scalars().all()
    
    engine = IncidentPatternEngine()
    predictions = []
    
    for asset in assets:
        inc_result = await db.execute(
            select(Incident).where(Incident.asset_id == asset.id)
        )
        incidents = inc_result.scalars().all()
        
        if incidents:
            inc_dicts = [{
                "severity": i.severity.value if hasattr(i.severity, 'value') else str(i.severity),
                "occurred_at": i.occurred_at,
            } for i in incidents]
            
            prediction = engine.predict_recurrence_risk(inc_dicts)
            predictions.append({
                "asset_id": str(asset.id),
                "asset_tag": asset.tag,
                "asset_name": asset.name,
                **prediction,
            })
    
    predictions.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return {"predictions": predictions, "analyzed_at": datetime.utcnow().isoformat()}


# ==================== PERMIT INTELLIGENCE API ====================

@app.get("/api/permits-analysis/conflicts")
async def detect_permit_conflicts(db: AsyncSession = Depends(get_db)):
    """Detect conflicts between active permits."""
    from sqlalchemy import select
    from models import Permit
    from agents.permit_agent import PermitIntelligenceEngine
    
    result = await db.execute(select(Permit).where(Permit.status.in_(["approved", "active"])))
    permits = result.scalars().all()
    
    permit_dicts = [{
        "id": str(p.id),
        "permit_number": p.permit_number,
        "title": p.title,
        "asset_id": str(p.asset_id) if p.asset_id else None,
        "zone_id": None,
        "requested_start": p.requested_start.isoformat() if p.requested_start else None,
        "requested_end": p.requested_end.isoformat() if p.requested_end else None,
        "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
        "work_scope": p.work_scope or "",
        "gas_test_required": p.gas_test_required,
        "loto_required": p.loto_required,
    } for p in permits]
    
    engine = PermitIntelligenceEngine()
    conflicts = engine.detect_conflicts(permit_dicts)
    return {"conflicts": conflicts, "checked_at": datetime.utcnow().isoformat()}


@app.get("/api/permits-analysis/risk-assessment")
async def assess_permit_risks(db: AsyncSession = Depends(get_db)):
    """Risk-assess all active permits."""
    from sqlalchemy import select
    from models import Permit
    from agents.permit_agent import PermitIntelligenceEngine
    
    result = await db.execute(select(Permit).where(Permit.status.in_(["approved", "active"])))
    permits = result.scalars().all()
    
    permit_dicts = [{
        "id": str(p.id),
        "permit_number": p.permit_number,
        "title": p.title,
        "work_scope": p.work_scope or "",
        "gas_test_required": p.gas_test_required,
        "loto_required": p.loto_required,
        "requested_start": p.requested_start.isoformat() if p.requested_start else None,
        "requested_end": p.requested_end.isoformat() if p.requested_end else None,
        "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
    } for p in permits]
    
    engine = PermitIntelligenceEngine()
    assessments = []
    for pd in permit_dicts:
        assessment = engine.score_permit_risk(pd, permit_dicts)
        assessments.append({"permit": pd, "risk_assessment": assessment})
    
    analytics = engine.get_permit_analytics(permit_dicts)
    return {"assessments": assessments, "analytics": analytics}


# ==================== EMERGENCY RESPONSE API ====================

@app.get("/api/emergency/{emergency_id}/ics-plan")
async def get_ics_plan(emergency_id: UUID, db: AsyncSession = Depends(get_db)):
    """Generate ICS response plan for an emergency."""
    from sqlalchemy import select
    from models import EmergencyIncident
    from agents.emergency import EmergencyResponseEngine
    
    result = await db.execute(select(EmergencyIncident).where(EmergencyIncident.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    
    emergency_dict = {
        "id": str(emergency.id),
        "category": emergency.emergency_type.value if hasattr(emergency.emergency_type, 'value') else str(emergency.emergency_type),
        "emergency_level": emergency.emergency_level or "level_1",
    }
    
    engine = EmergencyResponseEngine()
    plan = engine.generate_ics_plan(emergency_dict)
    return plan


@app.get("/api/emergency-analysis/metrics")
async def get_emergency_metrics(db: AsyncSession = Depends(get_db)):
    """Get emergency response metrics."""
    from sqlalchemy import select
    from models import EmergencyIncident
    from agents.emergency import EmergencyResponseEngine
    
    result = await db.execute(select(EmergencyIncident))
    emergencies = result.scalars().all()
    
    em_dicts = [{
        "status": e.status.value if hasattr(e.status, 'value') else str(e.status),
        "declared_at": e.declared_at.isoformat() if e.declared_at else None,
        "responded_at": e.responded_at.isoformat() if e.responded_at else None,
    } for e in emergencies]
    
    engine = EmergencyResponseEngine()
    return engine.track_response_metrics(em_dicts)


@app.get("/api/emergency-analysis/muster-plan")
async def get_muster_plan(emergency_type: str = "fire"):
    """Generate muster plan for an emergency type."""
    from agents.emergency import EmergencyResponseEngine
    
    engine = EmergencyResponseEngine()
    return engine.generate_muster_plan({}, emergency_type)


# ==================== COMPLIANCE AUDIT API ====================

@app.get("/api/audits/checklist/{standard}")
async def get_audit_checklist(standard: str):
    """Get compliance checklist for a standard."""
    from agents.compliance_audit import ComplianceAuditEngine
    
    engine = ComplianceAuditEngine()
    checklist = engine.get_checklist(standard)
    return {"standard": standard, "checklist": checklist, "total_items": len(checklist)}


@app.get("/api/audits/compliance-score")
async def calculate_compliance_score(db: AsyncSession = Depends(get_db)):
    """Calculate compliance scores for all audits."""
    from sqlalchemy import select
    from models import Audit
    from agents.compliance_audit import ComplianceAuditEngine
    
    result = await db.execute(select(Audit))
    audits = result.scalars().all()
    
    engine = ComplianceAuditEngine()
    scores = []
    for audit in audits:
        standard = audit.standard.value if hasattr(audit.standard, 'value') else str(audit.standard)
        checklist = engine.get_checklist(standard)
        total_weight = sum(item["weight"] for item in checklist)
        
        major_w = audit.major_findings * 3
        minor_w = audit.minor_findings * 1
        obs_w = audit.observations * 0
        achieved = max(0, total_weight - major_w - minor_w)
        compliance = (achieved / total_weight * 100) if total_weight > 0 else 0
        
        scores.append({
            "audit_id": str(audit.id),
            "audit_number": audit.audit_number,
            "title": audit.title,
            "standard": standard,
            "compliance_score": round(compliance, 1),
            "major_findings": audit.major_findings,
            "minor_findings": audit.minor_findings,
            "observations": audit.observations,
            "overall_result": audit.overall_result or "pending",
        })
    
    return {"audits": scores, "calculated_at": datetime.utcnow().isoformat()}


# ==================== DASHBOARD API ====================

@app.get("/api/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(db: AsyncSession = Depends(get_db)):
    """Get dashboard KPIs."""
    from sqlalchemy import select, func, and_
    from models import Permit, Incident, PlantAsset, EmergencyIncident
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Active permits
    active_permits_result = await db.execute(
        select(func.count(Permit.id)).where(
            Permit.status.in_(["approved", "active"])
        )
    )
    active_permits = active_permits_result.scalar() or 0
    
    # Active risk events by level
    from models import RiskEvent
    risk_events_result = await db.execute(
        select(RiskEvent.risk_level, func.count(RiskEvent.id))
        .where(RiskEvent.status == "active")
        .group_by(RiskEvent.risk_level)
    )
    risk_by_level = {level.value: 0 for level in RiskLevel}
    for level, count in risk_events_result.all():
        risk_by_level[level.value] = count
    
    # Open incidents
    open_incidents_result = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.status != "closed"
        )
    )
    open_incidents = open_incidents_result.scalar() or 0
    
    # Overdue inspections (assets)
    overdue_inspections_result = await db.execute(
        select(func.count(PlantAsset.id)).where(
            (PlantAsset.is_active == True) & (PlantAsset.next_inspection_due < now)
        )
    )
    overdue_inspections = overdue_inspections_result.scalar() or 0
    
    # Personnel on site (placeholder)
    personnel_on_site = 0  # TODO: Integrate with badge system
    muster_points_ready = 0  # TODO: Check muster point status
    
    return DashboardKPIs(
        active_permits=active_permits,
        active_risk_events=risk_by_level,
        open_incidents=open_incidents,
        overdue_inspections=overdue_inspections,
        personnel_on_site=personnel_on_site,
        muster_points_ready=muster_points_ready
    )


@app.get("/api/dashboard/risk-trend", response_model=List[RiskTrendPoint])
async def get_risk_trend(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get risk trend over time."""
    from sqlalchemy import select, func, and_
    from models import RiskEvent
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    
    # Group by hour and risk level
    result = await db.execute(
        select(
            func.date_trunc('hour', RiskEvent.detected_at).label('hour'),
            RiskEvent.risk_level,
            func.count(RiskEvent.id).label('count')
        )
        .where(
            and_(
                RiskEvent.detected_at >= start,
                RiskEvent.detected_at <= now
            )
        )
        .group_by('hour', RiskEvent.risk_level)
        .order_by('hour')
    )
    
    # Aggregate by hour
    hourly_data = {}
    for hour, level, count in result.all():
        hour_str = hour.isoformat()
        if hour_str not in hourly_data:
            hourly_data[hour_str] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        hourly_data[hour_str][level.value] = count
    
    return [
        RiskTrendPoint(
            timestamp=datetime.fromisoformat(hour),
            low=data["low"],
            medium=data["medium"],
            high=data["high"],
            critical=data["critical"]
        )
        for hour, data in sorted(hourly_data.items())
    ]


@app.get("/api/dashboard/permit-trend", response_model=List[PermitTrendPoint])
async def get_permit_trend(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get permit trend over time."""
    from sqlalchemy import select, func, and_
    from models import Permit
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(Permit.created_at).label('date'),
            Permit.status,
            func.count(Permit.id).label('count')
        )
        .where(
            and_(
                Permit.created_at >= start,
                Permit.created_at <= now
            )
        )
        .group_by('date', Permit.status)
        .order_by('date')
    )
    
    daily_data = {}
    for date, status, count in result.all():
        date_str = date.isoformat()
        if date_str not in daily_data:
            daily_data[date_str] = {"created": 0, "approved": 0, "active": 0, "closed": 0}
        daily_data[date_str][status.value] = count
    
    return [
        PermitTrendPoint(
            date=date,
            created=data["created"],
            approved=data["approved"],
            active=data["active"],
            closed=data["closed"]
        )
        for date, data in sorted(daily_data.items())
    ]


# ==================== CCTV ANALYTICS ENDPOINTS ====================

@app.get("/api/cctv/summary")
async def cctv_summary():
    """Get CCTV system summary."""
    return cctv_agent.get_summary()


@app.get("/api/cctv/alerts")
async def cctv_alerts(severity: Optional[str] = None):
    """Get active CCTV alerts, optionally filtered by severity."""
    from agents.cctv.schemas import DetectionSeverity
    sev = DetectionSeverity(severity) if severity else None
    return cctv_agent.get_active_alerts(sev)


@app.post("/api/cctv/alerts/{alert_id}/acknowledge")
async def cctv_acknowledge(alert_id: str, user: str = "operator"):
    """Acknowledge a CCTV alert."""
    success = cctv_agent.acknowledge_alert(alert_id, user)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id, "user": user}


@app.get("/api/cctv/detections")
async def cctv_detections(limit: int = 50):
    """Get recent CCTV detections."""
    return cctv_agent.detection_history[-limit:]


@app.get("/api/cctv/heatmap")
async def cctv_heatmap():
    """Get CCTV alert heatmap data by zone."""
    return cctv_agent.get_heatmap_data()


@app.post("/api/cctv/process")
async def cctv_process_all():
    """Process all camera feeds and generate detections."""
    results = await cctv_agent.process_all_cameras()
    return {"cameras_processed": len(results), "detections": sum(len(v) for v in results.values())}


# ==================== IoT / SCADA GATEWAY ENDPOINTS ====================

@app.get("/api/iot/metrics")
async def iot_metrics():
    """Get IoT gateway metrics."""
    return iot_gateway.get_metrics()


@app.get("/api/iot/devices")
async def iot_devices():
    """List registered IoT devices."""
    return [
        {
            "device_id": d.device_id,
            "name": d.device_name,
            "type": d.device_type.value,
            "protocol": d.protocol.value,
            "topic": d.topic,
            "interval": d.interval_seconds,
        }
        for d in iot_gateway.devices.values()
    ]


@app.get("/api/iot/recent")
async def iot_recent(limit: int = 50):
    """Get recent IoT telemetry messages."""
    return iot_gateway.get_recent_messages(limit)


@app.post("/api/iot/stream")
async def iot_stream_batch(count: int = 10):
    """Ingest a batch of simulated IoT sensor readings."""
    messages = await iot_gateway.ingest_batch(count)
    return {"ingested": len(messages), "messages": messages}


# ==================== KNOWLEDGE GRAPH ENDPOINTS ====================

@app.get("/api/knowledge-graph/data")
async def kg_data():
    """Get the full knowledge graph."""
    return kg_builder.to_serializable()


@app.get("/api/knowledge-graph/stats")
async def kg_stats():
    """Get knowledge graph statistics."""
    return kg_builder.get_stats()


@app.get("/api/knowledge-graph/related/{node_id}")
async def kg_related(node_id: str, depth: int = 2):
    """Get nodes related to a given node."""
    result = kg_builder.get_related(node_id, max_depth=depth)
    if not result.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@app.post("/api/knowledge-graph/risk-propagation")
async def kg_risk_propagation(source_type: str, source_id: str, max_depth: int = 4):
    """Propagate risk from a source node through the graph."""
    from agents.knowledge_graph.schemas import NodeType
    try:
        node_type = NodeType(source_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid node type: {source_type}")
    try:
        result = kg_builder.propagate_risk(node_type, source_id, max_depth)
        if not result:
            raise HTTPException(status_code=404, detail="Source node not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk propagation failed: {str(e)}")


@app.post("/api/knowledge-graph/paths")
async def kg_find_paths(source_type: str, source_id: str, target_type: str, target_id: str):
    """Find paths between two entities in the knowledge graph."""
    from agents.knowledge_graph.schemas import NodeType
    try:
        src_type = NodeType(source_type)
        tgt_type = NodeType(target_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    paths = kg_builder.find_paths(src_type, source_id, tgt_type, target_id)
    return {"paths": paths, "count": len(paths)}


# ==================== ORCHESTRATOR ENDPOINTS ====================

@app.get("/api/orchestrator/status")
async def orchestrator_status():
    """Get the orchestrator system status."""
    return orchestrator.get_system_status()


@app.get("/api/orchestrator/decisions")
async def orchestrator_decisions(limit: int = 10):
    """Get recent orchestrator decisions."""
    return orchestrator.get_recent_decisions(limit)


@app.post("/api/orchestrator/start")
async def orchestrator_start():
    """Start the autonomous background monitoring loop (non-blocking)."""
    if orchestrator._running:
        return {"status": "already_running"}
    import asyncio
    asyncio.create_task(orchestrator.start_background_monitoring())
    return {"status": "started"}


@app.post("/api/orchestrator/stop")
async def orchestrator_stop():
    """Stop the autonomous monitoring loop."""
    orchestrator.stop()
    return {"status": "stopped"}


@app.get("/api/orchestrator/agents")
async def orchestrator_agents():
    """Get detailed status of all agents."""
    return [
        {
            "agent": h.agent_id.value,
            "status": h.status.value,
            "last_active": h.last_active.isoformat() if h.last_active else None,
            "tasks": h.task_count,
            "errors": h.error_count,
            "avg_response_ms": h.avg_response_time_ms,
        }
        for h in orchestrator.agent_health.values()
    ]


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)