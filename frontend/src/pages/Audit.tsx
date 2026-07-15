import { useEffect, useState } from 'react';
import { endpoints } from '../api';
import { ClipboardCheck } from 'lucide-react';

export default function Audit() {
  const [audits, setAudits] = useState<any[]>([]);
  const [checklist, setChecklist] = useState<any>(null);
  const [compliance, setCompliance] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'list' | 'checklist' | 'compliance'>('compliance');

  useEffect(() => {
    Promise.all([
      endpoints.audits(),
      endpoints.auditChecklist('oisd_116'),
      endpoints.auditCompliance(),
    ]).then(([a, c, comp]) => {
      setAudits(a.data.items || []);
      setChecklist(c.data);
      setCompliance(comp.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading audit data...</div>;

  return (
    <div>
      <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Compliance Audit</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['compliance', 'checklist', 'list'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', borderRadius: 6, border: 'none',
            background: tab === t ? '#f59e0b' : '#334155',
            color: tab === t ? '#0f172a' : '#94a3b8',
            cursor: 'pointer', fontWeight: 600, fontSize: 13,
          }}>{t === 'compliance' ? 'Compliance Score' : t === 'checklist' ? 'OISD-116 Checklist' : 'Audits'}</button>
        ))}
      </div>

      {tab === 'compliance' && compliance && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {compliance.audits?.map((a: any) => (
            <div key={a.audit_id} style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <div style={{ color: '#f8fafc', fontSize: 16, fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: '#64748b', fontSize: 12 }}>{a.audit_number} | {a.standard}</div>
                </div>
                <div style={{
                  fontSize: 28, fontWeight: 700,
                  color: a.compliance_score >= 90 ? '#22c55e' : a.compliance_score >= 70 ? '#eab308' : '#ef4444',
                }}>{a.compliance_score}%</div>
              </div>

              <div style={{ background: '#0f172a', borderRadius: 8, height: 8, marginBottom: 16 }}>
                <div style={{
                  width: `${a.compliance_score}%`, height: '100%', borderRadius: 8,
                  background: a.compliance_score >= 90 ? '#22c55e' : a.compliance_score >= 70 ? '#eab308' : '#ef4444',
                }} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8 }}>
                {[
                  ['Major', a.major_findings, '#ef4444'],
                  ['Minor', a.minor_findings, '#f97316'],
                  ['Obs', a.observations, '#eab308'],
                  ['Good', a.good_practices || 0, '#22c55e'],
                ].map(([label, count, color]) => (
                  <div key={label as string} style={{ textAlign: 'center', padding: 8, background: '#0f172a', borderRadius: 6 }}>
                    <div style={{ color: color as string, fontSize: 20, fontWeight: 700 }}>{count}</div>
                    <div style={{ color: '#64748b', fontSize: 11 }}>{label}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'checklist' && checklist && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: '#f8fafc', fontSize: 16, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <ClipboardCheck size={18} color="#3b82f6" /> {checklist.standard.toUpperCase()} Checklist ({checklist.total_items} items)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {checklist.checklist?.map((item: any) => (
              <div key={item.id} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px',
                background: '#0f172a', borderRadius: 6,
              }}>
                <span style={{ color: '#64748b', fontSize: 11, minWidth: 60 }}>{item.id}</span>
                <span style={{ color: '#94a3b8', fontSize: 11, minWidth: 100 }}>{item.category}</span>
                <span style={{ color: '#f8fafc', fontSize: 13, flex: 1 }}>{item.item}</span>
                <span style={{ color: '#f59e0b', fontSize: 11, fontWeight: 600 }}>W:{item.weight}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'list' && (
        <div style={{ background: '#1e293b', borderRadius: 12, border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                {['Number', 'Title', 'Standard', 'Status', 'Result', 'Major', 'Minor'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {audits.map((a: any) => (
                <tr key={a.id} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '10px 16px', color: '#3b82f6', fontSize: 13 }}>{a.audit_number}</td>
                  <td style={{ padding: '10px 16px', color: '#f8fafc', fontSize: 13 }}>{a.title}</td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{a.standard}</td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{a.status}</td>
                  <td style={{ padding: '10px 16px' }}>
                    <span style={{
                      display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                      color: '#fff',
                      background: a.overall_result === 'conformance' ? '#22c55e' : a.overall_result === 'major_nc' ? '#ef4444' : '#eab308',
                    }}>{a.overall_result || 'pending'}</span>
                  </td>
                  <td style={{ padding: '10px 16px', color: '#ef4444', fontSize: 13 }}>{a.major_findings}</td>
                  <td style={{ padding: '10px 16px', color: '#f97316', fontSize: 13 }}>{a.minor_findings}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
