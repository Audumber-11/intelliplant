import { useEffect, useState } from 'react';
import { endpoints } from '../api';
import { AlertTriangle, Shield } from 'lucide-react';

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', safe: '#22c55e',
  };
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11,
      fontWeight: 600, color: '#fff', background: colors[level] || '#64748b', textTransform: 'uppercase',
    }}>{level}</span>
  );
}

export default function Permits() {
  const [permits, setPermits] = useState<any[]>([]);
  const [conflicts, setConflicts] = useState<any>(null);
  const [riskAssessment, setRiskAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'list' | 'conflicts' | 'risk'>('list');

  useEffect(() => {
    Promise.all([
      endpoints.permits(),
      endpoints.permitConflicts(),
      endpoints.permitRisk(),
    ]).then(([p, c, r]) => {
      setPermits(p.data.items || []);
      setConflicts(c.data);
      setRiskAssessment(r.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading permits...</div>;

  return (
    <div>
      <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Permit Intelligence</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['list', 'conflicts', 'risk'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', borderRadius: 6, border: 'none',
            background: tab === t ? '#f59e0b' : '#334155',
            color: tab === t ? '#0f172a' : '#94a3b8',
            cursor: 'pointer', fontWeight: 600, fontSize: 13,
          }}>{t === 'list' ? 'All Permits' : t === 'conflicts' ? 'Conflicts' : 'Risk Assessment'}</button>
        ))}
      </div>

      {tab === 'list' && (
        <div style={{ background: '#1e293b', borderRadius: 12, border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                {['Number', 'Title', 'Type', 'Status', 'Risk', 'Start', 'End'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {permits.map((p: any) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '10px 16px', color: '#3b82f6', fontSize: 13 }}>{p.permit_number}</td>
                  <td style={{ padding: '10px 16px', color: '#f8fafc', fontSize: 13 }}>{p.title}</td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{p.permit_type}</td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{p.status}</td>
                  <td style={{ padding: '10px 16px' }}><RiskBadge level={p.risk_level || 'low'} /></td>
                  <td style={{ padding: '10px 16px', color: '#64748b', fontSize: 12 }}>{p.requested_start?.split('T')[0] || '-'}</td>
                  <td style={{ padding: '10px 16px', color: '#64748b', fontSize: 12 }}>{p.requested_end?.split('T')[0] || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'conflicts' && conflicts && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={18} color="#f59e0b" /> Permit Conflicts ({conflicts.conflicts?.length || 0})
          </h3>
          {conflicts.conflicts?.length === 0 ? (
            <div style={{ color: '#64748b', padding: 20, textAlign: 'center' }}>No conflicts detected</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {conflicts.conflicts?.map((c: any, i: number) => (
                <div key={i} style={{ padding: 16, background: '#0f172a', borderRadius: 8, borderLeft: `3px solid ${c.severity === 'critical' ? '#ef4444' : '#f97316'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ color: '#f8fafc', fontSize: 14, fontWeight: 600 }}>{c.conflict_type.replace(/_/g, ' ')}</span>
                    <RiskBadge level={c.severity} />
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>{c.description}</div>
                  <div style={{ color: '#3b82f6', fontSize: 12 }}>Recommendation: {c.recommendation}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'risk' && riskAssessment && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} color="#3b82f6" /> Permit Risk Analytics
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 13 }}>Total Permits</span>
                <span style={{ color: '#f8fafc', fontSize: 13, fontWeight: 600 }}>{riskAssessment.analytics?.total || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 13 }}>Avg Risk Score</span>
                <span style={{ color: '#f8fafc', fontSize: 13, fontWeight: 600 }}>{riskAssessment.analytics?.avg_risk || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 13 }}>High Risk Permits</span>
                <span style={{ color: '#ef4444', fontSize: 13, fontWeight: 600 }}>{riskAssessment.analytics?.high_risk_permits || 0}</span>
              </div>
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16 }}>Permit Risk Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 300, overflow: 'auto' }}>
              {riskAssessment.assessments?.map((a: any, i: number) => (
                <div key={i} style={{ padding: 10, background: '#0f172a', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#f8fafc', fontSize: 12 }}>{a.permit.permit_number}</span>
                    <RiskBadge level={a.risk_assessment.risk_level} />
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: 11, marginTop: 4 }}>{a.permit.title}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
