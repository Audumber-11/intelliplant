"""
Alert Dispatcher — routes risk events to appropriate notification channels
based on severity, type, and recipient roles. Supports WebSocket, database
persistence, and external notification hooks.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class AlertChannel(str, Enum):
    WEBSOCKET = "websocket"
    DATABASE = "database"
    EMAIL = "email"
    SMS = "sms"
    PAGER = "pager"
    EXTERNAL_HOOK = "external_hook"


class AlertPriority(str, Enum):
    IMMEDIATE = "immediate"  # Send now
    URGENT = "urgent"  # Send within 1 minute
    NORMAL = "normal"  # Send within 5 minutes
    LOW = "low"  # Batch send


@dataclass
class AlertRecipient:
    user_id: str
    role: str
    channels: List[AlertChannel]
    is_on_duty: bool = True


@dataclass
class Alert:
    alert_id: str = field(default_factory=lambda: str(uuid4()))
    risk_event_id: str = ""
    severity: str = "medium"
    title: str = ""
    description: str = ""
    asset_id: Optional[str] = None
    zone_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    recommended_actions: List[str] = field(default_factory=list)
    recipients: List[AlertRecipient] = field(default_factory=list)
    channels_sent: Dict[str, bool] = field(default_factory=dict)
    priority: AlertPriority = AlertPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


# Type for async WebSocket send function
WebSocketSend = Callable[[str], Awaitable[None]]


class AlertDispatcher:
    """
    Dispatches risk alerts through multiple channels with role-based routing
    and priority-based delivery. Manages alert lifecycle from creation to
    acknowledgment.
    """

    # Severity to priority mapping
    SEVERITY_PRIORITY = {
        "critical": AlertPriority.IMMEDIATE,
        "high": AlertPriority.URGENT,
        "medium": AlertPriority.NORMAL,
        "low": AlertPriority.LOW,
    }

    # Role-based channel routing
    ROLE_CHANNELS = {
        "plant_manager": [AlertChannel.WEBSOCKET, AlertChannel.DATABASE, AlertChannel.EMAIL],
        "safety_officer": [
            AlertChannel.WEBSOCKET,
            AlertChannel.DATABASE,
            AlertChannel.EMAIL,
            AlertChannel.SMS,
        ],
        "emergency_coordinator": [
            AlertChannel.WEBSOCKET,
            AlertChannel.DATABASE,
            AlertChannel.EMAIL,
            AlertChannel.SMS,
            AlertChannel.PAGER,
        ],
        "supervisor": [AlertChannel.WEBSOCKET, AlertChannel.DATABASE],
        "operator": [AlertChannel.WEBSOCKET, AlertChannel.DATABASE],
        "auditor": [AlertChannel.DATABASE],
    }

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.websocket_connections: List[WebSocketSend] = []
        self.external_hooks: List[Callable[[Alert], Awaitable[None]]] = []
        self.db_session_factory: Optional[Any] = None

    def register_websocket(self, send_fn: WebSocketSend):
        """Register a WebSocket send function for real-time alerts."""
        self.websocket_connections.append(send_fn)

    def unregister_websocket(self, send_fn: WebSocketSend):
        """Unregister a WebSocket send function."""
        if send_fn in self.websocket_connections:
            self.websocket_connections.remove(send_fn)

    def register_external_hook(self, hook: Callable[[Alert], Awaitable[None]]):
        """Register an external notification hook."""
        self.external_hooks.append(hook)

    def set_db_session_factory(self, factory):
        """Set the database session factory for persistence."""
        self.db_session_factory = factory

    async def dispatch_risk_event(
        self,
        risk_event: Dict[str, Any],
        recipients: Optional[List[AlertRecipient]] = None,
    ) -> Alert:
        """
        Dispatch a risk event as an alert through appropriate channels.
        """
        severity = risk_event.get("severity", "medium")
        priority = self.SEVERITY_PRIORITY.get(severity, AlertPriority.NORMAL)

        # Create alert
        alert = Alert(
            risk_event_id=risk_event.get("event_id", ""),
            severity=severity,
            title=risk_event.get("title", "Risk Event Detected"),
            description=risk_event.get("description", ""),
            asset_id=risk_event.get("asset_id"),
            zone_id=risk_event.get("zone_id"),
            latitude=risk_event.get("latitude"),
            longitude=risk_event.get("longitude"),
            recommended_actions=risk_event.get("recommended_actions", []),
            priority=priority,
            recipients=recipients or [],
        )

        # Auto-assign recipients based on severity
        if not alert.recipients:
            alert.recipients = self._get_default_recipients(severity)

        # Dispatch through channels
        await self._dispatch(alert)

        # Store in active alerts
        self.active_alerts[alert.alert_id] = alert

        return alert

    async def dispatch_emergency(
        self,
        emergency: Dict[str, Any],
        recipients: Optional[List[AlertRecipient]] = None,
    ) -> Alert:
        """
        Dispatch an emergency alert through all channels immediately.
        """
        alert = Alert(
            risk_event_id=emergency.get("incident_id", ""),
            severity="critical",
            title=f"EMERGENCY: {emergency.get('emergency_type', 'Unknown')}",
            description=emergency.get("description", ""),
            asset_id=emergency.get("asset_id"),
            zone_id=emergency.get("zone_id"),
            latitude=emergency.get("latitude"),
            longitude=emergency.get("longitude"),
            recommended_actions=[
                "Activate emergency response plan",
                "Muster all personnel",
                "Notify external agencies",
                "Establish incident command",
            ],
            priority=AlertPriority.IMMEDIATE,
            recipients=recipients or self._get_all_duty_personnel(),
        )

        # Emergency goes through ALL channels
        await self._dispatch_emergency(alert)

        self.active_alerts[alert.alert_id] = alert
        return alert

    async def acknowledge_alert(
        self, alert_id: str, user_id: str, comments: Optional[str] = None
    ) -> bool:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False

        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        # Persist acknowledgment
        if self.db_session_factory:
            await self._persist_acknowledgment(alert)

        return True

    async def resolve_alert(
        self, alert_id: str, resolution: str, user_id: str
    ) -> bool:
        """Resolve and close an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False

        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        return True

    async def _dispatch(self, alert: Alert):
        """Dispatch alert through configured channels."""
        tasks = []

        for recipient in alert.recipients:
            for channel in recipient.channels:
                if channel == AlertChannel.WEBSOCKET:
                    tasks.append(self._send_websocket(alert))
                elif channel == AlertChannel.DATABASE:
                    tasks.append(self._persist_alert(alert))
                elif channel == AlertChannel.EMAIL:
                    tasks.append(self._send_email(alert, recipient))
                elif channel == AlertChannel.SMS:
                    tasks.append(self._send_sms(alert, recipient))
                elif channel == AlertChannel.PAGER:
                    tasks.append(self._send_pager(alert, recipient))
                elif channel == AlertChannel.EXTERNAL_HOOK:
                    for hook in self.external_hooks:
                        tasks.append(hook(alert))

                alert.channels_sent[f"{channel.value}:{recipient.user_id}"] = True

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _dispatch_emergency(self, alert: Alert):
        """Emergency dispatch — all channels, all recipients."""
        tasks = []

        # WebSocket broadcast
        tasks.append(self._send_websocket(alert))

        # Database persistence
        tasks.append(self._persist_alert(alert))

        # All recipient channels
        for recipient in alert.recipients:
            for channel in [
                AlertChannel.EMAIL,
                AlertChannel.SMS,
                AlertChannel.PAGER,
            ]:
                if channel == AlertChannel.EMAIL:
                    tasks.append(self._send_email(alert, recipient))
                elif channel == AlertChannel.SMS:
                    tasks.append(self._send_sms(alert, recipient))
                elif channel == AlertChannel.PAGER:
                    tasks.append(self._send_pager(alert, recipient))

        # External hooks
        for hook in self.external_hooks:
            tasks.append(hook(alert))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_websocket(self, alert: Alert):
        """Send alert to all connected WebSocket clients."""
        message = json.dumps(
            {
                "type": "risk_alert" if alert.severity != "critical" else "emergency_alert",
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "title": alert.title,
                "description": alert.description,
                "asset_id": alert.asset_id,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "recommended_actions": alert.recommended_actions,
                "timestamp": alert.created_at.isoformat(),
            }
        )

        disconnected = []
        for send_fn in self.websocket_connections:
            try:
                await send_fn(message)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                disconnected.append(send_fn)

        for fn in disconnected:
            self.websocket_connections.remove(fn)

    async def _persist_alert(self, alert: Alert):
        """Persist alert to database."""
        if not self.db_session_factory:
            return

        try:
            async with self.db_session_factory() as session:
                from models import RiskEvent

                risk_event = RiskEvent(
                    event_type="correlated_risk",
                    risk_level=alert.severity,
                    source="risk_engine",
                    source_id=alert.risk_event_id,
                    title=alert.title,
                    description=alert.description,
                    asset_id=alert.asset_id,
                    latitude=alert.latitude,
                    longitude=alert.longitude,
                    status="active",
                    recommended_actions=[
                        {"action": a, "status": "pending"}
                        for a in alert.recommended_actions
                    ],
                )
                session.add(risk_event)
                await session.commit()

                # Update alert with the persisted event ID
                alert.risk_event_id = str(risk_event.id)

        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")

    async def _persist_acknowledgment(self, alert: Alert):
        """Persist alert acknowledgment to database."""
        if not self.db_session_factory or not alert.risk_event_id:
            return

        try:
            async with self.db_session_factory() as session:
                from sqlalchemy import update
                from models import RiskEvent
                import uuid

                await session.execute(
                    update(RiskEvent)
                    .where(RiskEvent.id == uuid.UUID(alert.risk_event_id))
                    .values(
                        status="acknowledged",
                        acknowledged_at=alert.acknowledged_at,
                        acknowledged_by_id=uuid.UUID(alert.acknowledged_by)
                        if alert.acknowledged_by
                        else None,
                    )
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to persist acknowledgment: {e}")

    async def _send_email(self, alert: Alert, recipient: AlertRecipient):
        """Send email notification (placeholder — integrate with email service)."""
        logger.info(
            f"EMAIL to {recipient.user_id}: {alert.title} [{alert.severity}]"
        )
        # TODO: Integrate with SMTP/SendGrid/etc.

    async def _send_sms(self, alert: Alert, recipient: AlertRecipient):
        """Send SMS notification (placeholder — integrate with SMS provider)."""
        logger.info(
            f"SMS to {recipient.user_id}: {alert.title} [{alert.severity}]"
        )
        # TODO: Integrate with Twilio/etc.

    async def _send_pager(self, alert: Alert, recipient: AlertRecipient):
        """Send pager notification (placeholder — integrate with pager system)."""
        logger.info(
            f"PAGER to {recipient.user_id}: {alert.title} [{alert.severity}]"
        )
        # TODO: Integrate with pager system

    def _get_default_recipients(self, severity: str) -> List[AlertRecipient]:
        """Get default recipients based on severity."""
        if severity == "critical":
            return [
                AlertRecipient(
                    user_id="safety_officer_1",
                    role="safety_officer",
                    channels=[
                        AlertChannel.WEBSOCKET,
                        AlertChannel.DATABASE,
                        AlertChannel.EMAIL,
                        AlertChannel.SMS,
                    ],
                ),
                AlertRecipient(
                    user_id="emergency_coordinator_1",
                    role="emergency_coordinator",
                    channels=[
                        AlertChannel.WEBSOCKET,
                        AlertChannel.DATABASE,
                        AlertChannel.EMAIL,
                        AlertChannel.SMS,
                        AlertChannel.PAGER,
                    ],
                ),
                AlertRecipient(
                    user_id="plant_manager_1",
                    role="plant_manager",
                    channels=[
                        AlertChannel.WEBSOCKET,
                        AlertChannel.DATABASE,
                        AlertChannel.EMAIL,
                    ],
                ),
            ]
        elif severity == "high":
            return [
                AlertRecipient(
                    user_id="safety_officer_1",
                    role="safety_officer",
                    channels=[
                        AlertChannel.WEBSOCKET,
                        AlertChannel.DATABASE,
                        AlertChannel.EMAIL,
                    ],
                ),
                AlertRecipient(
                    user_id="supervisor_1",
                    role="supervisor",
                    channels=[AlertChannel.WEBSOCKET, AlertChannel.DATABASE],
                ),
            ]
        else:
            return [
                AlertRecipient(
                    user_id="supervisor_1",
                    role="supervisor",
                    channels=[AlertChannel.WEBSOCKET, AlertChannel.DATABASE],
                ),
            ]

    def _get_all_duty_personnel(self) -> List[AlertRecipient]:
        """Get all on-duty personnel for emergency alerts."""
        return [
            AlertRecipient(
                user_id="plant_manager_1",
                role="plant_manager",
                channels=[
                    AlertChannel.WEBSOCKET,
                    AlertChannel.DATABASE,
                    AlertChannel.EMAIL,
                    AlertChannel.SMS,
                ],
            ),
            AlertRecipient(
                user_id="safety_officer_1",
                role="safety_officer",
                channels=[
                    AlertChannel.WEBSOCKET,
                    AlertChannel.DATABASE,
                    AlertChannel.EMAIL,
                    AlertChannel.SMS,
                    AlertChannel.PAGER,
                ],
            ),
            AlertRecipient(
                user_id="emergency_coordinator_1",
                role="emergency_coordinator",
                channels=[
                    AlertChannel.WEBSOCKET,
                    AlertChannel.DATABASE,
                    AlertChannel.EMAIL,
                    AlertChannel.SMS,
                    AlertChannel.PAGER,
                ],
            ),
            AlertRecipient(
                user_id="supervisor_1",
                role="supervisor",
                channels=[AlertChannel.WEBSOCKET, AlertChannel.DATABASE],
            ),
        ]

    def get_active_alerts(
        self,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if asset_id:
            alerts = [a for a in alerts if a.asset_id == asset_id]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        return {
            "active_count": len(self.active_alerts),
            "by_severity": {
                level: sum(
                    1 for a in self.active_alerts.values() if a.severity == level
                )
                for level in ["low", "medium", "high", "critical"]
            },
            "unacknowledged": sum(
                1 for a in self.active_alerts.values() if not a.acknowledged
            ),
            "total_dispatched": len(self.alert_history) + len(self.active_alerts),
        }
