import { useEffect, useState } from 'react';
import { endpoints } from '../api';
import { Siren, Activity, MapPin } from 'lucide-react';

export default function Emergency() {
  const [active, setActive] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [muster, setMuster] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'active' | 'metrics' | 'muster'>('metrics');

  useEffect(() => {
    Promise.all([
      endpoints.emergencyActive(),
      endpoints.emergencyMetrics(),
      endpoints.emergencyMuster('fire'),
    ]).then(([a, m, mu]) => {
      setActive(a.data || []);
      setMetrics(m.data);
      setMuster(mu.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading emergency data...</div>;

  return (
    <div>
      <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Emergency Response</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['active', 'metrics', 'muster'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', borderRadius: 6, border: 'none',
            background: tab === t ? '#f59e0b' : '#334155',
            color: tab === t ? '#0f172a' : '#94a3b8',
            cursor: 'pointer', fontWeight: 600, fontSize: 13,
          }}>{t === 'active' ? 'Active Emergencies' : t === 'metrics' ? 'Response Metrics' : 'Muster Plan'}</button>
        ))}
      </div>

      {tab === 'active' && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          {active.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Siren size={48} color="#22c55e" style={{ marginBottom: 12 }} />
              <div style={{ color: '#22c55e', fontSize: 18, fontWeight: 600 }}>No Active Emergencies</div>
              <div style={{ color: '#64748b', fontSize: 13, marginTop: 8 }}>All systems normal</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {active.map((e: any) => (
                <div key={e.id} style={{ padding: 16, background: '#0f172a', borderRadius: 8, borderLeft: '3px solid #ef4444' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#f8fafc', fontSize: 14, fontWeight: 600 }}>{e.emergency_number}</span>
                    <span style={{ color: '#ef4444', fontSize: 12, fontWeight: 600 }}>{e.emergency_level}</span>
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 4 }}>{e.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'metrics' && metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity size={18} color="#f59e0b" /> Response Statistics
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                ['Total Emergencies', metrics.total],
                ['Resolved', metrics.resolved],
                ['Active', metrics.active],
                ['Avg Response Time', `${metrics.metrics?.avg_response_time_minutes || 0} min`],
                ['Resolution Rate', `${(metrics.metrics?.resolution_rate * 100 || 0).toFixed(1)}%`],
              ].map(([label, value]) => (
                <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8', fontSize: 13 }}>{label}</span>
                  <span style={{ color: '#f8fafc', fontSize: 13, fontWeight: 600 }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16 }}>Response Time Range</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                ['Fastest', `${metrics.metrics?.min_response_time_minutes || 0} min`, '#22c55e'],
                ['Average', `${metrics.metrics?.avg_response_time_minutes || 0} min`, '#eab308'],
                ['Slowest', `${metrics.metrics?.max_response_time_minutes || 0} min`, '#ef4444'],
              ].map(([label, value, color]) => (
                <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#94a3b8', fontSize: 13 }}>{label}</span>
                  <span style={{ color: color as string, fontSize: 13, fontWeight: 600 }}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'muster' && muster && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <MapPin size={18} color="#22c55e" /> Muster Points
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[muster.primary_muster, muster.secondary_muster].map((mp: any, i: number) => (
                <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8 }}>
                  <div style={{ color: '#f8fafc', fontSize: 13, fontWeight: 600 }}>{mp.name}</div>
                  <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>Location: {mp.location}</div>
                  <div style={{ color: '#94a3b8', fontSize: 12 }}>Capacity: {mp.capacity}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16 }}>Evacuation Routes</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {muster.evacuation_routes?.map((r: any, i: number) => (
                <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8 }}>
                  <div style={{ color: '#f8fafc', fontSize: 13 }}>{r.from} → {r.to}</div>
                  <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>Est. time: {r.estimated_time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
