import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import OverviewPage from './pages/OverviewPage';
import ParkingPage from './pages/ParkingPage';
import CamerasPage from './pages/CamerasPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';
import { getFleetStatus } from './api';
import './index.css';

// ── Verbatim Navigation Configuration ─────────────────────────────────────────
interface NavConfig {
  to: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavConfig[] = [
  { to: '/',          label: 'Overview',            icon: '▦' },
  { to: '/zones',     label: 'Level Zones',         icon: '🏢' },
  { to: '/analytics', label: 'Analytics',           icon: '📊' },
  { to: '/cameras',   label: 'Camera Management',   icon: '📹' },
  { to: '/settings',  label: 'System Settings',     icon: '⚙' },
];

// ── Left Navigation Sidebar ──────────────────────────────────────────────────
function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="sidebar">
      {/* MallPark AI Logo */}
      <div className="sidebar-header">
        <div className="mallpark-logo-icon">M</div>
        <div>
          <div className="mallpark-title">MallPark AI</div>
          <div className="mallpark-subtitle">Floor-Level Command</div>
        </div>
      </div>

      {/* Verbatim Navigation Rail */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Profile for 'ANNA L.', Operator with Avatar */}
      <div className="sidebar-footer">
        <div className="operator-card">
          <div className="operator-avatar">AL</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="operator-name">ANNA L.</div>
            <div className="operator-role">Operator</div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontSize: '14px',
              padding: '4px',
            }}
          >
            ⏻
          </button>
        </div>
      </div>
    </aside>
  );
}

// ── Live Real-Time Clock ──────────────────────────────────────────────────────
function LiveClock() {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      let hours = now.getHours();
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      const strHours = String(hours).padStart(2, '0');

      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const year = now.getFullYear();

      setTimeStr(`${strHours}:${minutes}:${seconds} ${ampm} - ${month}/${day}, ${year}`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return <div className="top-timestamp" title="Live System Real-Time Clock">{timeStr}</div>;
}

// ── Dynamic Fleet Status Indicator ───────────────────────────────────────────
function FleetStatusPill() {
  const [fleet, setFleet] = useState({ online: 2, total: 2, pct: 100 });

  useEffect(() => {
    getFleetStatus()
      .then(res => {
        if (res.data) {
          setFleet({
            online: res.data.online_cameras ?? 2,
            total: res.data.total_cameras ?? 2,
            pct: res.data.fleet_percentage ?? 100,
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="fleet-status-pill" title={`${fleet.online}/${fleet.total} AI Optical Nodes Online`}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', boxShadow: '0 0 8px #4ade80', display: 'inline-block', animation: 'pulse 1.8s infinite' }} />
      {fleet.pct.toFixed(1)}% Fleet Online ({fleet.online}/{fleet.total})
    </div>
  );
}

// ── Global Top Bar ────────────────────────────────────────────────────────────
function TopBar({
  selectedFloor,
  onSelectFloor,
}: {
  selectedFloor: string;
  onSelectFloor: (fl: string) => void;
}) {
  const [audioEnabled, setAudioEnabled] = useState(true);

  return (
    <header className="top-bar">
      {/* Far Left Brand Text */}
      <div className="top-left-brand">
        <span style={{ color: '#ffffff' }}>MALLPARK AI:</span> FLOOR-LEVEL COMMAND DASHBOARD
      </div>

      {/* Centered Page Title with Active L2 Dropdown */}
      <div className="top-center-title">
        <span>OVERVIEW DASHBOARD - ZONE B [FLOOR SELECTION:</span>
        <select
          value={selectedFloor}
          onChange={e => onSelectFloor(e.target.value)}
          className="floor-select-dropdown"
        >
          <option value="L2">L2</option>
          <option value="L1">L1</option>
          <option value="B1">B1</option>
          <option value="B2">B2</option>
          <option value="L3">L3</option>
        </select>
        <span>]</span>
      </div>

      {/* Far Right: Live Real-Time Clock, Dynamic Fleet Online & Audio Toggle */}
      <div className="top-right-meta">
        <LiveClock />

        <FleetStatusPill />

        <button
          onClick={() => setAudioEnabled(!audioEnabled)}
          className={`audio-toggle-btn ${audioEnabled ? 'active' : ''}`}
          title="Toggle Audio Incident Alerts"
        >
          <span>{audioEnabled ? '🔊' : '🔇'}</span>
          <span>{audioEnabled ? 'Audio Alert: ON' : 'Audio Alert: OFF'}</span>
        </button>
      </div>
    </header>
  );
}

// ── Dashboard Layout Shell ───────────────────────────────────────────────────
function DashboardLayout() {
  const [selectedFloor, setSelectedFloor] = useState('L2');

  return (
    <div className="app-container">
      <Sidebar />
      <div className="content-area">
        <TopBar selectedFloor={selectedFloor} onSelectFloor={setSelectedFloor} />
        <main className="main-viewport">
          <Routes>
            <Route path="/"            element={<OverviewPage selectedFloor={selectedFloor} />} />
            <Route path="/zones"       element={<ParkingPage />} />
            <Route path="/parking"     element={<ParkingPage />} />
            <Route path="/analytics"   element={<AnalyticsPage />} />
            <Route path="/cameras"     element={<CamerasPage />} />
            <Route path="/settings"    element={<SettingsPage />} />
            <Route path="*"            element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

// ── Route Guard ──────────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

// ── Root Application ─────────────────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
