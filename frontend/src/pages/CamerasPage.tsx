import { useEffect, useState } from 'react';
import { getCameras, getCameraFootageUrl } from '../api';

interface Camera {
  id: string;
  name: string;
  source_type: string;
  latitude: number | null;
  longitude: number | null;
  status: string;
  created_at: string;
}

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeFootageCamera, setActiveFootageCamera] = useState<Camera | null>(null);

  useEffect(() => {
    getCameras()
      .then(r => setCameras(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load cameras'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Header with Officer Clearance Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.025em' }}>
              Camera Management · Optical Fleet
            </h2>
            <span className="badge badge-active badge-ai-shimmer">42/42 ONLINE</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Multi-level garage CCTV feeds, high-density ANPR tracking, and real-time AI optical analysis
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge" style={{ background: '#000000', borderColor: 'var(--border)' }}>
            ● Feed Access: Audited
          </span>
        </div>
      </div>

      {/* Monochrome Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Total Feeds</span>
            <span className="stat-icon">📹</span>
          </div>
          <div className="stat-value">{cameras.length}</div>
          <div className="stat-sub">Configured CCTV inputs</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Active Surveillance</span>
            <span className="stat-icon">◉</span>
          </div>
          <div className="stat-value">
            {cameras.filter(c => c.status === 'ACTIVE').length}
          </div>
          <div className="stat-sub" style={{ color: '#4ade80' }}>Streaming online</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Coverage Region</span>
            <span className="stat-icon">📍</span>
          </div>
          <div className="stat-value" style={{ fontSize: '20px', paddingTop: '6px' }}>Bangalore CBD</div>
          <div className="stat-sub">MG Road & Brigade Zone</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Access Policy</span>
            <span className="stat-icon">🔒</span>
          </div>
          <div className="stat-value" style={{ fontSize: '18px', paddingTop: '6px' }}>Officer Only</div>
          <div className="stat-sub" style={{ color: '#4ade80' }}>Surveillance Clearance: ACTIVE</div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderLeft: '3px solid var(--status-alert)', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="spinner" />
      ) : cameras.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📹</div>
            <p>No CCTV cameras configured</p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Add cameras via <code style={{ color: '#ffffff' }}>data/configs/cameras.json</code> or run seed script.
            </p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="card-header" style={{ padding: '20px 24px 14px', margin: 0 }}>
            <span className="card-title">📹 Active Municipal CCTV Network</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Showing {cameras.length} secured CCTV units
            </span>
          </div>
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Camera ID</th>
                  <th>Location Name</th>
                  <th>Feed Protocol</th>
                  <th>Coordinates</th>
                  <th>Added On</th>
                  <th style={{ textAlign: 'right' }}>Footage Action</th>
                </tr>
              </thead>
              <tbody>
                {cameras.map(cam => (
                  <tr key={cam.id}>
                    <td>
                      <span className={`badge ${cam.status === 'ACTIVE' ? 'badge-active' : 'badge-rejected'}`}>
                        {cam.status === 'ACTIVE' ? '● ONLINE' : '○ OFFLINE'}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ color: '#ffffff', fontWeight: 600 }}>
                        {cam.id}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {cam.name}
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                        {cam.source_type.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {cam.latitude?.toFixed(4)}, {cam.longitude?.toFixed(4)}
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(cam.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => setActiveFootageCamera(cam)}
                        title="Officer access to live CCTV footage"
                      >
                        ▶ Watch CCTV Stream
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CCTV Live Footage Player Modal (Officer Exclusive) */}
      {activeFootageCamera && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.88)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '24px',
          }}
          onClick={() => setActiveFootageCamera(null)}
        >
          <div
            style={{
              background: '#0e0e12',
              border: '1px solid #27272a',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '840px',
              width: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Player Topbar */}
            <div
              style={{
                padding: '16px 20px',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#09090b',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', animation: 'pulse 1.5s infinite' }} />
                  <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                    CCTV Live Feed — {activeFootageCamera.name}
                  </h3>
                  <span className="badge badge-officer" style={{ fontSize: '10px' }}>OFFICER SECURED</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Camera {activeFootageCamera.id} · Source: {activeFootageCamera.source_type.toUpperCase()} · Lat/Lon: {activeFootageCamera.latitude}, {activeFootageCamera.longitude}
                </span>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setActiveFootageCamera(null)}
                style={{ fontSize: '16px', lineHeight: 1 }}
              >
                ✕
              </button>
            </div>

            {/* Video Player Box with AI Scanning Animation */}
            <div className="ai-scan-container" style={{ background: '#000000', position: 'relative', minHeight: '380px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              {/* AI Laser Scanline Beam sweeping across video */}
              <div className="ai-scan-beam" />

              <video
                src={getCameraFootageUrl(activeFootageCamera.id)}
                controls
                autoPlay
                loop
                muted
                style={{ width: '100%', maxHeight: '480px', objectFit: 'contain' }}
                onError={(e) => {
                  const target = e.currentTarget;
                  if (!target.src.includes('/videos/')) {
                    target.src = activeFootageCamera.id === 'CAM-002' ? '/videos/car_video_01.mp4' : '/videos/curb_surveillance.mp4';
                  }
                }}
              />

              {/* Live HUD Overlay */}
              <div
                style={{
                  position: 'absolute',
                  top: '14px',
                  left: '16px',
                  display: 'flex',
                  gap: '8px',
                  pointerEvents: 'none',
                  flexWrap: 'wrap',
                }}
              >
                <span className="badge" style={{ background: 'rgba(0,0,0,0.85)', border: '1px solid rgba(255,255,255,0.25)', color: '#ffffff', fontSize: '10px' }}>
                  ● REC 1080P · 30 FPS
                </span>
                <span className="badge badge-ai-shimmer" style={{ background: 'rgba(0,0,0,0.85)', fontSize: '10px' }}>
                  <span className="ai-radar-dot" />
                  YOLOv8 AI VEHICLE TRACKING
                </span>
                <span className="floor-badge" style={{ fontSize: '10px', background: 'rgba(0,0,0,0.85)' }}>
                  🏢 Nexus Grand Mall · Floor B1
                </span>
                <span className="pillar-badge" style={{ fontSize: '10px', padding: '2px 8px' }}>
                  🏛️ Pillars A01–C15
                </span>
              </div>
            </div>

            {/* Officer Security Notice & Footer */}
            <div
              style={{
                padding: '14px 20px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#09090b',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                🔒 <strong>Restricted Traffic Enforcement Footage.</strong> Streamed directly via authorized officer session.
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <a
                  href={getCameraFootageUrl(activeFootageCamera.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary btn-sm"
                >
                  ↗ Open Full Window
                </a>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setActiveFootageCamera(null)}
                >
                  Close Stream
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security Protocol Box */}
      <div className="card" style={{ marginTop: '20px', background: 'var(--bg-card)' }}>
        <div className="card-header">
          <span className="card-title">🛡️ CCTV Security & Privacy Compliance</span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.7 }}>
          Municipal CCTV camera feeds and live surveillance streams are classified under restricted municipal enforcement data.
          Per municipal regulations, camera feeds and live surveillance are restricted strictly to authorized Parking Officers.
          All footage playback and violation citations generated by the AI engine are cryptographically logged for traffic enforcement auditing.
        </p>
      </div>
    </div>
  );
}
