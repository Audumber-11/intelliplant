import { NavLink, Outlet } from 'react-router-dom';
import { Shield, Map, AlertTriangle, FileCheck, Siren, ClipboardCheck, LayoutDashboard, Camera, Cpu, Share2, Bot } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/heatmap', icon: Map, label: 'Heatmap' },
  { to: '/incidents', icon: AlertTriangle, label: 'Incidents' },
  { to: '/permits', icon: FileCheck, label: 'Permits' },
  { to: '/emergency', icon: Siren, label: 'Emergency' },
  { to: '/audit', icon: ClipboardCheck, label: 'Audit' },
  { to: '/cctv', icon: Camera, label: 'CCTV Vision' },
  { to: '/iot', icon: Cpu, label: 'IoT / SCADA' },
  { to: '/knowledge-graph', icon: Share2, label: 'Knowledge Graph' },
  { to: '/orchestrator', icon: Bot, label: 'Orchestrator' },
];

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      <aside style={{
        width: 240,
        background: '#1e293b',
        borderRight: '1px solid #334155',
        padding: '20px 0',
        flexShrink: 0,
      }}>
        <div style={{ padding: '0 20px 20px', borderBottom: '1px solid #334155', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Shield size={28} color="#f59e0b" />
            <div>
              <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: 16 }}>IntelliPlant</div>
              <div style={{ color: '#94a3b8', fontSize: 11 }}>Safety Intelligence</div>
            </div>
          </div>
        </div>
        <nav>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 20px',
                color: isActive ? '#f59e0b' : '#94a3b8',
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: isActive ? 600 : 400,
                background: isActive ? 'rgba(245,158,11,0.1)' : 'transparent',
                borderRight: isActive ? '3px solid #f59e0b' : '3px solid transparent',
                transition: 'all 0.15s',
              })}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, overflow: 'auto', padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
