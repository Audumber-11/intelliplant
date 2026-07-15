import { useEffect, useState } from 'react';
import { endpoints } from '../api';
import { AlertTriangle, TrendingUp } from 'lucide-react';

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e',
  };
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 600,
      color: '#fff',
      background: colors[severity] || '#64748b',
      textTransform: 'uppercase',
    }}>{severity}</span>
  );
}

export default function Incidents() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [patterns, setPatterns] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'list' | 'patterns' | 'recurrence'>('list');

  useEffect(() => {
    Promise.all([
      endpoints.incidents(),
      endpoints.incidentPatterns(),
    ]).then(([i, p]) => {
      setIncidents(i.data.items || []);
      setPatterns(p.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading incidents...</div>;

  return (
    <div>
      <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Incident Intelligence</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['list', 'patterns'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', borderRadius: 6, border: 'none',
            background: tab === t ? '#f59e0b' : '#334155',
            color: tab === t ? '#0f172a' : '#94a3b8',
            cursor: 'pointer', fontWeight: 600, fontSize: 13,
          }}>{t === 'list' ? 'Incidents' : 'Pattern Analysis'}</button>
        ))}
      </div>

      {tab === 'list' && (
        <div style={{ background: '#1e293b', borderRadius: 12, border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                {['Number', 'Title', 'Severity', 'Status', 'Category', 'Date'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc: any) => (
                <tr key={inc.id} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '10px 16px', color: '#3b82f6', fontSize: 13 }}>{inc.incident_number}</td>
                  <td style={{ padding: '10px 16px', color: '#f8fafc', fontSize: 13 }}>{inc.title}</td>
                  <td style={{ padding: '10px 16px' }}><SeverityBadge severity={inc.severity} /></td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{inc.status}</td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{inc.category || '-'}</td>
                  <td style={{ padding: '10px 16px', color: '#64748b', fontSize: 12 }}>{inc.occurred_at?.split('T')[0] || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'patterns' && patterns && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle size={18} color="#f59e0b" /> Detected Patterns
            </h3>
            {patterns.patterns?.length === 0 ? (
              <div style={{ color: '#64748b' }}>No patterns detected</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {patterns.patterns?.map((p: any, i: number) => (
                  <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#f8fafc', fontSize: 13, fontWeight: 500 }}>{p.type.replace(/_/g, ' ')}</span>
                      <SeverityBadge severity={p.severity} />
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: 12 }}>{p.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingUp size={18} color="#3b82f6" /> Recommendations
            </h3>
            {patterns.recommendations?.length === 0 ? (
              <div style={{ color: '#64748b' }}>No recommendations</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {patterns.recommendations?.map((r: any, i: number) => (
                  <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8 }}>
                    <div style={{ color: '#f8fafc', fontSize: 13, fontWeight: 500, marginBottom: 4 }}>{r.action}</div>
                    <div style={{ color: '#94a3b8', fontSize: 12 }}>{r.rationale}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
