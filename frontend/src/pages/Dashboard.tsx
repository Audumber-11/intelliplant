import { useEffect, useState } from 'react';
import { endpoints } from '../api';
import { Shield, AlertTriangle, Siren, TrendingUp, Activity } from 'lucide-react';

function StatCard({ icon: Icon, label, value, color, sub }: { icon: any; label: string; value: string | number; color: string; sub?: string }) {
  return (
    <div style={{
      background: '#1e293b',
      borderRadius: 12,
      padding: 20,
      border: '1px solid #334155',
      flex: 1,
      minWidth: 200,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <div style={{ background: `${color}20`, borderRadius: 8, padding: 8 }}>
          <Icon size={20} color={color} />
        </div>
        <span style={{ color: '#94a3b8', fontSize: 13 }}>{label}</span>
      </div>
      <div style={{ color: '#f8fafc', fontSize: 28, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', safe: '#22c55e',
  };
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 600,
      color: '#fff',
      background: colors[level] || '#64748b',
      textTransform: 'uppercase',
    }}>{level}</span>
  );
}

export default function Dashboard() {
  const [kpis, setKpis] = useState<any>(null);
  const [risks, setRisks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      endpoints.dashboardKpis(),
      endpoints.riskCurrent(),
    ]).then(([k, r]) => {
      setKpis(k.data);
      setRisks(r.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading dashboard...</div>;

  return (
    <div>
      <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Safety Intelligence Dashboard
      </h1>
      <p style={{ color: '#64748b', marginBottom: 24 }}>Real-time plant safety monitoring</p>

      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <StatCard icon={Shield} label="Active Permits" value={kpis?.active_permits || 0} color="#3b82f6" />
        <StatCard icon={AlertTriangle} label="Open Incidents" value={kpis?.open_incidents || 0} color="#ef4444" />
        <StatCard icon={TrendingUp} label="Risk Events" value={risks.length} color="#f59e0b" sub={`${kpis?.active_risk_events?.critical || 0} critical`} />
        <StatCard icon={Siren} label="Overdue Inspections" value={kpis?.overdue_inspections || 0} color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Activity size={18} color="#f59e0b" /> Active Risk Events
          </h3>
          {risks.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: 20 }}>No active risk events</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {risks.map((risk: any) => (
                <div key={risk.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 12px',
                  background: '#0f172a',
                  borderRadius: 8,
                }}>
                  <div>
                    <div style={{ color: '#f8fafc', fontSize: 13, fontWeight: 500 }}>{risk.title}</div>
                    <div style={{ color: '#64748b', fontSize: 11 }}>{risk.source}</div>
                  </div>
                  <RiskBadge level={risk.risk_level} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16 }}>Risk Distribution</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Object.entries(kpis?.active_risk_events || {}).map(([level, count]) => (
              <div key={level} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <RiskBadge level={level} />
                <div style={{ flex: 1, background: '#0f172a', borderRadius: 4, height: 8 }}>
                  <div style={{
                    width: `${Math.min(((count as number) / Math.max(risks.length, 1)) * 100, 100)}%`,
                    height: '100%',
                    borderRadius: 4,
                    background: level === 'critical' ? '#ef4444' : level === 'high' ? '#f97316' : level === 'medium' ? '#eab308' : '#22c55e',
                  }} />
                </div>
                <span style={{ color: '#94a3b8', fontSize: 13, minWidth: 20, textAlign: 'right' }}>{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
