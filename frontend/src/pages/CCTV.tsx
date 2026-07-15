import { useEffect, useState } from 'react';
import { Camera, AlertTriangle, ShieldAlert, Activity, Eye, CheckCircle } from 'lucide-react';
import { endpoints } from '../api';

interface CameraStatus {
  camera_id: string;
  camera_name: string;
  online: boolean;
  fps_current: number;
  last_frame_at: string | null;
  detections_last_hour: number;
  alerts_generated: number;
}

interface CVSummary {
  total_cameras: number;
  online_cameras: number;
  active_alerts: number;
  detections_last_hour: number;
  ppe_violations_today: number;
  critical_events_today: number;
  most_common_violation: string | null;
  cameras: CameraStatus[];
}

interface CVAlert {
  alert_id: string;
  detection_id: string;
  alert_type: string;
  severity: string;
  camera_id: string;
  zone: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  escalated_to_emergency: boolean;
}

const severityColors: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
};

export default function CCTV() {
  const [summary, setSummary] = useState<CVSummary | null>(null);
  const [alerts, setAlerts] = useState<CVAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    try {
      const [s, a] = await Promise.all([endpoints.cctvSummary(), endpoints.cctvAlerts()]);
      setSummary(s.data);
      setAlerts(a.data);
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

  const processAll = async () => {
    setProcessing(true);
    try {
      await endpoints.cctvProcess();
      await load();
    } finally {
      setProcessing(false);
    }
  };

  const acknowledge = async (id: string) => {
    try {
      await endpoints.cctvAck(id);
      await load();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading CCTV analytics...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: '#f8fafc', fontSize: 24, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Camera color="#f59e0b" /> CCTV Analytics & Computer Vision
          </h1>
          <p style={{ color: '#94a3b8', marginTop: 4 }}>Real-time PPE detection, fire/smoke recognition, and unauthorized access monitoring</p>
        </div>
        <button
          onClick={processAll}
          disabled={processing}
          style={{
            background: '#f59e0b', color: '#0f172a', border: 'none', padding: '10px 18px',
            borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 14,
          }}
        >
          {processing ? 'Processing...' : '🔄 Process Feeds'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card label="Cameras Online" value={`${summary?.online_cameras || 0}/${summary?.total_cameras || 0}`} icon={<Camera color="#22c55e" />} />
        <Card label="Active Alerts" value={summary?.active_alerts || 0} icon={<AlertTriangle color="#ef4444" />} />
        <Card label="PPE Violations" value={summary?.ppe_violations_today || 0} icon={<ShieldAlert color="#f59e0b" />} />
        <Card label="Critical Events" value={summary?.critical_events_today || 0} icon={<Activity color="#f97316" />} />
        <Card label="Detections/Hr" value={summary?.detections_last_hour || 0} icon={<Eye color="#3b82f6" />} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Section title="Camera Status">
          {summary?.cameras.map((c) => (
            <div key={c.camera_id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 16px', background: '#1e293b', borderRadius: 8, marginBottom: 8, border: '1px solid #334155',
            }}>
              <div>
                <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 14 }}>{c.camera_name}</div>
                <div style={{ color: '#94a3b8', fontSize: 12 }}>
                  {c.detections_last_hour} detections/hr · {c.alerts_generated} alerts · {c.fps_current} fps
                </div>
              </div>
              <span style={{
                padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600,
                background: c.online ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                color: c.online ? '#22c55e' : '#ef4444',
              }}>
                {c.online ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
          ))}
        </Section>

        <Section title={`Active Alerts (${alerts.length})`}>
          {alerts.length === 0 && <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>No active alerts</div>}
          {alerts.slice(0, 12).map((a) => (
            <div key={a.alert_id} style={{
              padding: '12px 16px', background: '#1e293b', borderRadius: 8, marginBottom: 8, border: '1px solid #334155',
              borderLeft: `4px solid ${severityColors[a.severity] || '#94a3b8'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 14 }}>{a.alert_type.replace(/_/g, ' ')}</div>
                <span style={{ color: severityColors[a.severity], fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>
                  {a.severity}
                </span>
              </div>
              <div style={{ color: '#94a3b8', fontSize: 12, margin: '4px 0' }}>{a.message}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#64748b', fontSize: 11 }}>{a.zone} · {new Date(a.timestamp).toLocaleTimeString()}</span>
                {a.acknowledged ? (
                  <span style={{ color: '#22c55e', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle size={12} /> Ack
                  </span>
                ) : (
                  <button onClick={() => acknowledge(a.alert_id)} style={{
                    background: 'transparent', border: '1px solid #334155', color: '#94a3b8',
                    padding: '3px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                  }}>
                    Acknowledge
                  </button>
                )}
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
      <div style={{ color: '#f8fafc', fontSize: 28, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#0f172a', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
      <h2 style={{ color: '#f8fafc', fontSize: 16, margin: '0 0 16px' }}>{title}</h2>
      {children}
    </div>
  );
}
