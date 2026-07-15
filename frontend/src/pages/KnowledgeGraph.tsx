import { useEffect, useState } from 'react';
import { Share2, Network, GitBranch, AlertTriangle, Boxes } from 'lucide-react';
import { endpoints } from '../api';

interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  edge_types: Record<string, number>;
  density: number;
  high_risk_nodes: number;
  zones_covered: string[];
}

interface GraphNode {
  id: string;
  type: string;
  label: string;
  properties: Record<string, unknown>;
  risk_score: number | null;
  zone: string | null;
}

interface GraphEdge {
  source_id: string;
  target_id: string;
  type: string;
  weight: number;
  properties: Record<string, unknown>;
}

interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const nodeColors: Record<string, string> = {
  equipment: '#3b82f6',
  permit: '#f59e0b',
  incident: '#ef4444',
  sensor: '#22c55e',
  personnel: '#a855f7',
  zone: '#06b6d4',
  document: '#64748b',
  regulation: '#ec4899',
  hazard: '#f97316',
  action: '#14b8a6',
};

export default function KnowledgeGraph() {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const load = async () => {
    try {
      const [s, g] = await Promise.all([endpoints.kgStats(), endpoints.kgData()]);
      setStats(s.data);
      setGraph(g.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Building knowledge graph...</div>;

  const selected = graph?.nodes.find((n) => n.id === selectedNode);
  const connectedEdges = graph?.edges.filter((e) => e.source_id === selectedNode || e.target_id === selectedNode) || [];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: '#f8fafc', fontSize: 24, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Share2 color="#f59e0b" /> Knowledge Graph
        </h1>
        <p style={{ color: '#94a3b8', marginTop: 4 }}>Equipment-permit-risk relationships powered by NetworkX graph intelligence</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card label="Total Nodes" value={stats?.total_nodes || 0} icon={<Boxes color="#3b82f6" />} />
        <Card label="Relationships" value={stats?.total_edges || 0} icon={<GitBranch color="#f59e0b" />} />
        <Card label="Graph Density" value={(stats?.density || 0).toFixed(3)} icon={<Network color="#22c55e" />} />
        <Card label="High-Risk Nodes" value={stats?.high_risk_nodes || 0} icon={<AlertTriangle color="#ef4444" />} />
        <Card label="Zones Covered" value={(stats?.zones_covered || []).length} icon={<Share2 color="#06b6d4" />} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Section title="Entity Types">
          {Object.entries(stats?.node_types || {}).map(([type, count]) => (
            <div key={type} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 14px', background: '#1e293b', borderRadius: 8, marginBottom: 6, border: '1px solid #334155',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColors[type] || '#64748b' }} />
                <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{type}</span>
              </div>
              <span style={{ color: '#94a3b8', fontSize: 14 }}>{count}</span>
            </div>
          ))}
        </Section>

        <Section title="Relationship Types">
          {Object.entries(stats?.edge_types || {}).map(([type, count]) => (
            <div key={type} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 14px', background: '#1e293b', borderRadius: 8, marginBottom: 6, border: '1px solid #334155',
            }}>
              <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{type.replace(/_/g, ' ')}</span>
              <span style={{ color: '#94a3b8', fontSize: 14 }}>{count}</span>
            </div>
          ))}
        </Section>
      </div>

      <Section title="Graph Explorer">
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
          <div style={{ maxHeight: 400, overflow: 'auto' }}>
            {graph?.nodes.map((n) => (
              <div
                key={n.id}
                onClick={() => setSelectedNode(n.id)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 14px', background: selectedNode === n.id ? 'rgba(245,158,11,0.1)' : '#1e293b',
                  borderRadius: 8, marginBottom: 6, border: `1px solid ${selectedNode === n.id ? '#f59e0b' : '#334155'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColors[n.type] || '#64748b' }} />
                  <div>
                    <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13 }}>{n.label}</div>
                    <div style={{ color: '#64748b', fontSize: 11 }}>{n.type} · {n.id}</div>
                  </div>
                </div>
                {n.risk_score !== null && (
                  <span style={{
                    padding: '3px 8px', borderRadius: 10, fontSize: 11, fontWeight: 700,
                    background: n.risk_score > 0.6 ? 'rgba(239,68,68,0.15)' : n.risk_score > 0.4 ? 'rgba(245,158,11,0.15)' : 'rgba(34,197,94,0.15)',
                    color: n.risk_score > 0.6 ? '#ef4444' : n.risk_score > 0.4 ? '#f59e0b' : '#22c55e',
                  }}>
                    RISK {(n.risk_score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            ))}
          </div>

          <div style={{ background: '#1e293b', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
            {selected ? (
              <>
                <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{selected.label}</div>
                <div style={{ color: '#64748b', fontSize: 11, marginBottom: 12 }}>{selected.type} · {selected.id}</div>
                {selected.zone && (
                  <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>Zone: {selected.zone}</div>
                )}
                <div style={{ color: '#f59e0b', fontSize: 13, fontWeight: 600, margin: '12px 0 8px' }}>
                  Connections ({connectedEdges.length})
                </div>
                {connectedEdges.map((e, i) => (
                  <div key={i} style={{ color: '#94a3b8', fontSize: 12, padding: '4px 0', borderTop: '1px solid #334155' }}>
                    {e.type.replace(/_/g, ' ')} → {e.target_id === selected.id ? e.source_id : e.target_id}
                  </div>
                ))}
              </>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', padding: 20 }}>
                Select a node to view its relationships
              </div>
            )}
          </div>
        </div>
      </Section>
    </div>
  );
}

function Card({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div style={{ background: '#1e293b', borderRadius: 10, padding: 16, border: '1px solid #334155' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ color: '#94a3b8', fontSize: 12 }}>{label}</span>
        {icon}
      </div>
      <div style={{ color: '#f8fafc', fontSize: 28, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#0f172a', borderRadius: 12, padding: 20, border: '1px solid #334155', marginBottom: 24 }}>
      <h2 style={{ color: '#f8fafc', fontSize: 16, margin: '0 0 16px' }}>{title}</h2>
      {children}
    </div>
  );
}
