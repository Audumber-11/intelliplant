import { useEffect, useState, useRef } from 'react';
import { endpoints } from '../api';

export default function Heatmap() {
  const [layout, setLayout] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [locations, setLocations] = useState<any>(null);
  const [tab, setTab] = useState<'layout' | 'heatmap' | 'zones'>('heatmap');
  const [loading, setLoading] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    Promise.all([
      endpoints.heatmapLayout(),
      endpoints.heatmapLive(20),
      endpoints.heatmapLocations(),
    ]).then(([l, h, loc]) => {
      setLayout(l.data);
      setHeatmap(h.data);
      setLocations(loc.data);
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!canvasRef.current || !heatmap) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cells = heatmap.cells || [];
    if (cells.length === 0) return;

    const bounds = heatmap.bounds;
    const latRange = bounds.north - bounds.south;
    const lngRange = bounds.east - bounds.west;

    cells.forEach((cell: any) => {
      const x = ((cell.lng - bounds.west) / lngRange) * canvas.width;
      const y = ((bounds.north - cell.lat) / latRange) * canvas.height;
      const cellW = canvas.width / heatmap.resolution;
      const cellH = canvas.height / heatmap.resolution;

      const score = cell.risk_score;
      let r: number, g: number, b: number;
      if (score < 0.2) { r = 34; g = 197; b = 94; }
      else if (score < 0.4) { r = 132; g = 204; b = 22; }
      else if (score < 0.6) { r = 234; g = 179; b = 8; }
      else if (score < 0.8) { r = 249; g = 115; b = 22; }
      else { r = 239; g = 68; b = 68; }

      ctx.fillStyle = `rgba(${r},${g},${b},${0.3 + score * 0.5})`;
      ctx.fillRect(x - cellW / 2, y - cellH / 2, cellW, cellH);
    });

    if (layout) {
      layout.features?.forEach((f: any) => {
        if (f.properties.type === 'zone') {
          const coords = f.geometry.coordinates[0];
          ctx.strokeStyle = f.properties.color || '#64748b';
          ctx.lineWidth = 2;
          ctx.beginPath();
          coords.forEach((c: number[], i: number) => {
            const px = ((c[0] - bounds.west) / lngRange) * canvas.width;
            const py = ((bounds.north - c[1]) / latRange) * canvas.height;
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
          });
          ctx.closePath();
          ctx.stroke();
          const center = coords.reduce((acc: number[], c: number[]) => [acc[0] + c[0] / coords.length, acc[1] + c[1] / coords.length], [0, 0]);
          const cx = ((center[0] - bounds.west) / lngRange) * canvas.width;
          const cy = ((bounds.north - center[1]) / latRange) * canvas.height;
          ctx.fillStyle = '#f8fafc';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(f.properties.name, cx, cy);
        }
      });
    }

    if (locations?.assets) {
      locations.assets.forEach((a: any) => {
        const x = ((a.lng - bounds.west) / lngRange) * canvas.width;
        const y = ((bounds.north - a.lat) / latRange) * canvas.height;
        ctx.fillStyle = '#3b82f6';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    if (locations?.personnel) {
      locations.personnel.forEach((p: any) => {
        const x = ((p.lng - bounds.west) / lngRange) * canvas.width;
        const y = ((bounds.north - p.lat) / latRange) * canvas.height;
        ctx.fillStyle = '#22c55e';
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }, [heatmap, layout, locations, tab]);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40 }}>Loading heatmap...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ color: '#f8fafc', fontSize: 24, fontWeight: 700 }}>Safety Heatmap</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {(['layout', 'heatmap', 'zones'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '6px 16px',
              borderRadius: 6,
              border: 'none',
              background: tab === t ? '#f59e0b' : '#334155',
              color: tab === t ? '#0f172a' : '#94a3b8',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 13,
            }}>{t === 'layout' ? 'Layout' : t === 'heatmap' ? 'Risk Heatmap' : 'Zones'}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>
        <div style={{ background: '#1e293b', borderRadius: 12, border: '1px solid #334155', overflow: 'hidden' }}>
          <canvas
            ref={canvasRef}
            style={{ width: '100%', height: 500, display: 'block' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 16, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 14, marginBottom: 12 }}>Legend</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[{ label: 'Safe', color: '#22c55e' }, { label: 'Low', color: '#84cc16' }, { label: 'Medium', color: '#eab308' }, { label: 'High', color: '#f97316' }, { label: 'Critical', color: '#ef4444' }].map(l => (
                <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 16, height: 16, borderRadius: 3, background: l.color, opacity: 0.7 }} />
                  <span style={{ color: '#94a3b8', fontSize: 12 }}>{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 16, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 14, marginBottom: 12 }}>Heatmap Stats</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>Avg Risk</span>
                <span style={{ color: '#f8fafc', fontSize: 12, fontWeight: 600 }}>{heatmap?.avg_risk || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>Max Risk</span>
                <span style={{ color: '#f8fafc', fontSize: 12, fontWeight: 600 }}>{heatmap?.max_risk || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>Critical Cells</span>
                <span style={{ color: '#ef4444', fontSize: 12, fontWeight: 600 }}>{heatmap?.critical_cells || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>Total Cells</span>
                <span style={{ color: '#f8fafc', fontSize: 12, fontWeight: 600 }}>{heatmap?.cells?.length || 0}</span>
              </div>
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: 16, border: '1px solid #334155' }}>
            <h3 style={{ color: '#f8fafc', fontSize: 14, marginBottom: 12 }}>Personnel</h3>
            <div style={{ color: '#94a3b8', fontSize: 12 }}>
              {locations?.personnel?.length || 0} personnel on site
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
