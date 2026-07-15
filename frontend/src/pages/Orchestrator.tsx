import { useEffect, useState } from 'react';
import { Bot, Brain, Network, Activity, Play, Square, Cpu } from 'lucide-react';
import { endpoints } from '../api';

interface AgentHealth {
  agent: string;
  status: string;
  last_active: string | null;
  tasks: number;
  errors: number;
  avg_response_ms: number;
}

interface SystemStatus {
  overall_status: string;
  agents: AgentHealth[];
  active_decisions: number;
  messages_in_queue: number;
  uptime_hours: number;
  last_orchestration: string | null;
  critical_alerts_active: number;
  llm_enabled: boolean;
}

interface OrchestratorDecision {
  decision_id: string;
  timestamp: string;
  trigger: string;
  reasoning: string;
  actions: Array<Record<string, unknown>>;
  confidence: number;
  requires_human_approval: boolean;
}

const statusColors: Record<string, string> = {
  idle: '#94a3b8',
  running: '#22c55e',
  error: '#ef4444',
  degraded: '#f59e0b',
};

export default function Orchestrator() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [decisions, setDecisions] = useState<OrchestratorDecision[]>([]);
  const [agents, setAgents] = useState<AgentHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = async () => {
    try {
      const [s, d, a] = await Promise.all([endpoints.orchStatus(), endpoints.orchDecisions(10), endpoints.orchAgents()]);
      setStatus(s.data);
      setDecisions(d.data);
      setAgents(a.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggle = async () => {
    try {
      if (running) {
        await endpoints.orchStop();
        setRunning(false);
      } else {
        await endpoints.orchStart();
        setRunning(true);
      }
      await load();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Initializing orchestrator...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: '#f8fafc', fontSize: 24, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Bot color="#f59e0b" /> Agent Orchestrator
          </h1>
          <p style={{ color: '#94a3b8', marginTop: 4 }}>LLM-powered multi-agent coordination with autonomous background monitoring</p>
        </div>
        <button
          onClick={toggle}
          style={{
            background: running ? '#ef4444' : '#22c55e', color: '#0f172a', border: 'none', padding: '10px 18px',
            borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          {running ? <><Square size={14} /> Stop</> : <><Play size={14} /> Start</>}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card label="System Status" value={status?.overall_status.toUpperCase() || 'N/A'} icon={<Activity color="#22c55e" />} />
        <Card label="Active Agents" value={status?.agents.length || 0} icon={<Bot color="#3b82f6" />} />
        <Card label="Decisions" value={status?.active_decisions || 0} icon={<Brain color="#f59e0b" />} />
        <Card label="Msg Queue" value={status?.messages_in_queue || 0} icon={<Network color="#a855f7" />} />
        <Card label="Uptime (hrs)" value={(status?.uptime_hours || 0).toFixed(1)} icon={<Cpu color="#06b6d4" />} />
        <Card label="LLM" value={status?.llm_enabled ? 'ON' : 'OFF'} icon={<Brain color="#ec4899" />} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Section title="Agent Fleet">
          {agents.map((a) => (
            <div key={a.agent} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 16px', background: '#1e293b', borderRadius: 8, marginBottom: 8, border: '1px solid #334155',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: statusColors[a.status] || '#94a3b8' }} />
                <div>
                  <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 14, textTransform: 'capitalize' }}>{a.agent.replace(/_/g, ' ')}</div>
                  <div style={{ color: '#94a3b8', fontSize: 11 }}>{a.tasks} tasks · {a.errors} errors</div>
                </div>
              </div>
              <span style={{
                padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                background: (statusColors[a.status] || '#94a3b8') + '22', color: statusColors[a.status] || '#94a3b8',
              }}>
                {a.status}
              </span>
            </div>
          ))}
        </Section>

        <Section title={`Recent Decisions (${decisions.length})`}>
          {decisions.length === 0 && <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>No decisions yet</div>}
          {decisions.map((d) => (
            <div key={d.decision_id} style={{
              padding: '12px 16px', background: '#1e293b', borderRadius: 8, marginBottom: 8, border: '1px solid #334155',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13 }}>{d.trigger}</span>
                <span style={{
                  color: d.confidence > 0.8 ? '#22c55e' : '#f59e0b', fontSize: 12, fontWeight: 700,
                }}>
                  {(d.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 6 }}>{d.reasoning}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {d.actions.map((a, i) => (
                  <span key={i} style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 10, background: 'rgba(245,158,11,0.12)',
                    color: '#f59e0b', textTransform: 'capitalize',
                  }}>
                    {(a.agent as string) || 'agent'} · {(a.action as string) || 'action'}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </Section>
      </div>
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
      <div style={{ color: '#f8fafc', fontSize: 22, fontWeight: 700 }}>{value}</div>
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
