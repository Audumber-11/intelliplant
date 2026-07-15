import uuid
import re
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime

import networkx as nx

from .schemas import (
    GraphNode, GraphEdge, KnowledgeGraph, PathResult, GraphStats,
    GraphQuery, RiskPropagationResult, NodeType, EdgeType
)


class KnowledgeGraphBuilder:
    """Builds and queries a NetworkX knowledge graph from domain data."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._node_map: Dict[str, GraphNode] = {}

    def add_equipment(self, equipment_id: str, name: str, properties: Dict[str, Any] = None):
        node = GraphNode(
            id=f"eq_{equipment_id}",
            type=NodeType.EQUIPMENT,
            label=name,
            properties=properties or {},
        )
        self._add_node(node)

    def add_permit(self, permit_id: str, title: str, zone: str = None, properties: Dict[str, Any] = None):
        node = GraphNode(
            id=f"permit_{permit_id}",
            type=NodeType.PERMIT,
            label=title,
            properties=properties or {},
            zone=zone,
        )
        self._add_node(node)
        if zone:
            zone_id = f"zone_{zone}"
            if self.graph.has_node(zone_id):
                self._add_edge(
                    source_id=node.id,
                    target_id=zone_id,
                    edge_type=EdgeType.LOCATED_IN,
                    weight=1.0,
                    properties={"permit_id": permit_id},
                )

    def add_incident(self, incident_id: str, title: str, severity: str, zone: str = None, properties: Dict[str, Any] = None):
        risk = {"low": 0.3, "medium": 0.5, "high": 0.7, "critical": 0.9, "fatality": 1.0}.get(severity, 0.5)
        node = GraphNode(
            id=f"inc_{incident_id}",
            type=NodeType.INCIDENT,
            label=title,
            properties=properties or {},
            risk_score=risk,
            zone=zone,
        )
        self._add_node(node)
        if zone:
            zone_id = f"zone_{zone}"
            if self.graph.has_node(zone_id):
                self._add_edge(
                    source_id=node.id, target_id=zone_id,
                    edge_type=EdgeType.LOCATED_IN, weight=risk,
                )

    def add_sensor(self, sensor_id: str, name: str, zone: str = None, properties: Dict[str, Any] = None):
        node = GraphNode(
            id=f"sensor_{sensor_id}",
            type=NodeType.SENSOR,
            label=name,
            properties=properties or {},
            zone=zone,
        )
        self._add_node(node)
        if zone:
            zone_id = f"zone_{zone}"
            if self.graph.has_node(zone_id):
                self._add_edge(
                    source_id=node.id, target_id=zone_id,
                    edge_type=EdgeType.LOCATED_IN, weight=1.0,
                    properties={"sensor_id": sensor_id},
                )

    def add_personnel(self, person_id: str, name: str, role: str, zone: str = None):
        node = GraphNode(
            id=f"person_{person_id}",
            type=NodeType.PERSONNEL,
            label=name,
            properties={"role": role},
            zone=zone,
        )
        self._add_node(node)

    def add_zone(self, zone_id: str, name: str, risk_level: str = "low"):
        risk = {"low": 0.2, "medium": 0.4, "high": 0.6, "critical": 0.8}.get(risk_level, 0.3)
        node = GraphNode(
            id=f"zone_{zone_id}",
            type=NodeType.ZONE,
            label=name,
            properties={"risk_level": risk_level},
            risk_score=risk,
        )
        self._add_node(node)
        return node

    def add_relation(self, source_type: str, source_id: str,
                     target_type: str, target_id: str,
                     relation: EdgeType, weight: float = 1.0,
                     properties: Dict[str, Any] = None):
        src = f"{source_type}_{source_id}"
        tgt = f"{target_type}_{target_id}"
        if self.graph.has_node(src) and self.graph.has_node(tgt):
            self._add_edge(src, tgt, relation, weight, properties or {})

    def _add_node(self, node: GraphNode):
        self.graph.add_node(node.id, data=node)
        self._node_map[node.id] = node

    def _add_edge(self, source_id: str, target_id: str, edge_type: EdgeType,
                  weight: float = 1.0, properties: Dict[str, Any] = None):
        edge = GraphEdge(
            source_id=source_id, target_id=target_id,
            type=edge_type, weight=weight, properties=properties or {},
        )
        self.graph.add_edge(source_id, target_id, key=str(uuid.uuid4()), data=edge)

    def get_related(self, node_id: str, max_depth: int = 2, edge_types: List[EdgeType] = None) -> KnowledgeGraph:
        if not self.graph.has_node(node_id):
            return KnowledgeGraph()
        nodes = {node_id}
        edges = []
        current = {node_id}
        for _ in range(max_depth):
            if not current:
                break
            next_nodes = set()
            for n in current:
                for _, neighbor, data in self.graph.edges(n, data=True):
                    edge = data.get("data")
                    if edge and (not edge_types or edge.type in edge_types):
                        nodes.add(neighbor)
                        edges.append(edge)
                        next_nodes.add(neighbor)
                for neighbor, _, data in self.graph.in_edges(n, data=True):
                    edge = data.get("data")
                    if edge and (not edge_types or edge.type in edge_types):
                        nodes.add(neighbor)
                        edges.append(edge)
                        next_nodes.add(neighbor)
            current = next_nodes
        return KnowledgeGraph(
            nodes=[self._node_map[n] for n in nodes if n in self._node_map],
            edges=list({e.type.value + e.source_id + e.target_id: e for e in edges}.values()),
        )

    def find_paths(self, source_type: NodeType, source_value: str,
                   target_type: NodeType, target_value: str,
                   max_depth: int = 5) -> List[PathResult]:
        src = f"{source_type.value}_{source_value}"
        tgt = f"{target_type.value}_{target_value}"
        if not self.graph.has_node(src) or not self.graph.has_node(tgt):
            return []

        results = []
        try:
            paths = nx.all_simple_paths(self.graph, src, tgt, cutoff=max_depth)
            for path in paths:
                path_nodes = [self._node_map[n] for n in path if n in self._node_map]
                path_edges = []
                total_risk = 0.0
                for i in range(len(path) - 1):
                    edges_data = self.graph.get_edge_data(path[i], path[-1])
                    if edges_data:
                        for key, data in edges_data.items():
                            edge = data.get("data")
                            if edge:
                                path_edges.append(edge)
                                total_risk += edge.weight * 0.2
                results.append(PathResult(
                    path=path_nodes, edges=path_edges,
                    total_risk=min(total_risk, 1.0),
                ))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
        return results

    def find_risk_connections(self, zone: str, min_risk: float = 0.3) -> KnowledgeGraph:
        zone_id = f"zone_{zone}"
        if not self.graph.has_node(zone_id):
            return KnowledgeGraph()
        related = self.get_related(zone_id, max_depth=3)
        high_risk = [
            n for n in related.nodes
            if n.risk_score is not None and n.risk_score >= min_risk
        ]
        high_risk_ids = {n.id for n in high_risk}
        return KnowledgeGraph(
            nodes=high_risk + [n for n in related.nodes if n.id == zone_id],
            edges=[e for e in related.edges
                   if e.source_id in high_risk_ids | {zone_id}
                   or e.target_id in high_risk_ids | {zone_id}],
        )

    def propagate_risk(self, source_type: NodeType, source_value: str,
                       max_depth: int = 4) -> RiskPropagationResult:
        src = f"{source_type.value}_{source_value}"
        if not self.graph.has_node(src):
            return None

        source_node = self._node_map.get(src)
        affected = []
        paths = []

        try:
            for target in self.graph.nodes:
                if target == src:
                    continue
                try:
                    path = nx.shortest_path(self.graph, src, target, cutoff=max_depth)
                    risk_accum = 0.0
                    for i in range(len(path) - 1):
                        edges_data = self.graph.get_edge_data(path[i], path[i + 1])
                        if edges_data:
                            for data in edges_data.values():
                                edge = data.get("data")
                                if edge:
                                    risk_accum += edge.weight * 0.15
                    if path and len(path) > 1:
                        affected.append({
                            "node_id": target,
                            "risk": min(risk_accum, 1.0),
                            "distance": len(path) - 1,
                        })
                        path_nodes = [self._node_map[n] for n in path if n in self._node_map]
                        path_edges = []
                        for i in range(len(path) - 1):
                            edges_data = self.graph.get_edge_data(path[i], path[i + 1])
                            if edges_data:
                                for data in edges_data.values():
                                    edge = data.get("data")
                                    if edge:
                                        path_edges.append(edge)
                        paths.append(PathResult(
                            path=path_nodes, edges=path_edges,
                            total_risk=min(risk_accum, 1.0),
                        ))
                except (nx.NetworkXNoPath, nx.NodeNotFound, nx.NetworkXError):
                    continue
        except Exception:
            pass

        overall = sum(a["risk"] for a in affected) / max(len(affected), 1) if affected else 0.0
        return RiskPropagationResult(
            source_node=source_node,
            affected_nodes=sorted(affected, key=lambda x: -x["risk"])[:20],
            propagation_paths=sorted(paths, key=lambda p: -p.total_risk)[:5],
            overall_risk_impact=round(overall, 3),
        )

    def get_stats(self) -> GraphStats:
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        for node_id in self.graph.nodes:
            node = self._node_map.get(node_id)
            if node:
                node_types[node.type.value] += 1
        for _, _, data in self.graph.edges(data=True):
            edge = data.get("data")
            if edge:
                edge_types[edge.type.value] += 1

        n = self.graph.number_of_nodes()
        density = nx.density(self.graph) if n > 1 else 0.0
        high_risk = len([n for n in self._node_map.values()
                        if n.risk_score and n.risk_score >= 0.5])
        zones = list({n.zone for n in self._node_map.values() if n.zone})

        return GraphStats(
            total_nodes=n,
            total_edges=self.graph.number_of_edges(),
            node_types=dict(node_types),
            edge_types=dict(edge_types),
            density=round(density, 4),
            high_risk_nodes=high_risk,
            zones_covered=zones,
        )

    def to_serializable(self) -> KnowledgeGraph:
        nodes = list(self._node_map.values())
        edges = []
        seen = set()
        for _, _, data in self.graph.edges(data=True):
            edge = data.get("data")
            if edge:
                key = f"{edge.type.value}:{edge.source_id}->{edge.target_id}"
                if key not in seen:
                    seen.add(key)
                    edges.append(edge)
        return KnowledgeGraph(nodes=nodes, edges=edges)

    def infer_relationships(self, text: str, source_id: str):
        equipment_pattern = re.findall(r'\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b', text)
        for eq in equipment_pattern:
            eq_id = f"eq_{eq}"
            if self.graph.has_node(eq_id):
                self._add_edge(
                    source_id=source_id,
                    target_id=eq_id,
                    edge_type=EdgeType.RELATED_TO,
                    weight=0.7,
                )

        risk_patterns = [
            (r'\b(pressure|temperature|flow|level)\s+(high|low|abnormal)', EdgeType.TRIGGERED),
            (r'\b(safety|critical|emergency)\b', EdgeType.REQUIRES),
            (r'\b(inspect|maintain|repair|replace)\b', EdgeType.CONNECTED_TO),
        ]
        for pattern, edge_type in risk_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self._add_edge(
                    source_id=source_id,
                    target_id=source_id,
                    edge_type=edge_type,
                    weight=0.5,
                )
