import { useEffect, useState } from 'react';
import { Cpu, Radio, Activity, Zap, Gauge } from 'lucide-react';
import { endpoints } from '../api';

interface IoTMetrics {
  total_devices: number;
  active_devices: number;
  protocols: Array<{
    protocol: string;
    connected: boolean;
    messages_per_second: number;
    messages_total: number;
    devices_registered: number;
  }>;
  messages_last_hour: number;
  error_rate: number;
  avg_latency_ms: number;
}

interface IoTDevice {
  device_id: string;
  name: string;
  type: string;
  protocol: string;
  topic: string | null;
  interval: number;
}

interface TelemetryMessage {
  device_id: string;
  device_type: string;
  protocol: string;
  sensor_type: string | null;
  value: number;
  unit: string;
  timestamp: string;
  quality: number;
  metadata: Record<string, unknown>;
}

export default function IoT() {
  const [metrics, setMetrics] = useState<IoTMetrics | null>(null);
  const [devices, setDevices] = useState<IoTDevice[]>([]);
  const [messages, setMessages] = useState<TelemetryMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);

  const load = async () => {
    try {
      const [m, d, r] = await Promise.all([endpoints.iotMetrics(), endpoints.iotDevices(), endpoints.iotRecent(20)]);
      setMetrics(m.data);
      setDevices(d.data);
      setMessages(r.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, []);

  const streamBatch = async () => {
    setStreaming(true);
    try {
      await endpoints.iotStream(15);
      await load();
    } finally {
      setStreaming(false);
    }
  };

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Connecting to IoT gateway...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: '#f8fafc', fontSize: 24, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Cpu color="#f59e0b" /> IoT / SCADA Integration
          </h1>
          <p style={{ color: '#94a3b8', marginTop: 4 }}>Real-time sensor telemetry via MQTT, OPC-UA, and Modbus protocols</p>
        </div>
        <button
          onClick={streamBatch}
          disabled={streaming}
          style={{
            background: '#f59e0b', color: '#0f172a', border: 'none', padding: '10px 18px',
            borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 14,
          }}
        >
          {streaming ? 'Streaming...' : '📡 Stream Batch'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card label="Devices" value={`${metrics?.active_devices || 0}/${metrics?.total_devices || 0}`} icon={<Cpu color="#22c55e" />} />
        <Card label="Msgs/Hour" value={metrics?.messages_last_hour || 0} icon={<Radio color="#3b82f6" />} />
        <Card label="Throughput/s" value={(metrics?.protocols[0]?.messages_per_second || 0).toFixed(1)} icon={<Activity color="#f59e0b" />} />
        <Card label="Avg Latency" value={`${(metrics?.avg_latency_ms || 0).toFixed(0)}ms`} icon={<Gauge color="#a855f7" />} />
        <Card label="Error Rate" value={`${((metrics?.error_rate || 0) * 100).toFixed(1)}%`} icon={<Zap color="#ef4444" />} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Section title="Protocol Gateways">
          {metrics?.protocols.map((p) => (
            <div key={p.protocol} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 16px', background: '#1e293b', borderRadius: 8, marginBottom: 8, border: '1px solid #334155',
            }}>
              <div>
                <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 14, textTransform: 'uppercase' }}>{p.protocol}</div>
                <div style={{ color: '#94a3b8', fontSize: 12 }}>{p.devices_registered} devices · {p.messages_total} msgs</div>
              </div>
              <span style={{
                padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600,
                background: p.connected ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                color: p.connected ? '#22c55e' : '#ef4444',
              }}>
                {p.connected ? 'CONNECTED' : 'DOWN'}
              </span>
            </div>
          ))}
        </Section>

        <Section title={`Live Telemetry (${messages.length})`}>
          {messages.length === 0 && <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>No messages yet</div>}
          {messages.slice(0, 14).map((m, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 12px', background: '#1e293b', borderRadius: 6, marginBottom: 6, border: '1px solid #334155',
            }}>
              <div>
                <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13 }}>{m.device_id}</span>
                <span style={{ color: '#64748b', fontSize: 11, marginLeft: 8 }}>{m.sensor_type}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ color: '#f59e0b', fontWeight: 700, fontSize: 14 }}>
                  {m.value} {m.unit}
                </span>
                <span style={{
                  color: m.quality > 0.7 ? '#22c55e' : '#ef4444', fontSize: 11,
                }}>
                  Q:{(m.quality * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </Section>
      </div>

      <Section title="Registered Devices" >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
          {devices.map((d) => (
            <div key={d.device_id} style={{
              padding: '10px 14px', background: '#1e293b', borderRadius: 8, border: '1px solid #334155',
            }}>
              <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13 }}>{d.name}</div>
              <div style={{ color: '#94a3b8', fontSize: 11 }}>
                {d.device_id} · {d.protocol.toUpperCase()} · {d.type}
              </div>
            </div>
          ))}
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
