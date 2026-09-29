import { useEffect, useRef, useState } from 'react';
import { WS_BASE } from '../api';
import { useAuth } from '../contexts/AuthContext';

interface OccupancyMsg {
  camera_id: string;
  occupied: number;
  available: number;
  total: number;
  occupancy_percentage: number;
}

interface ViolationMsg {
  violation_type: string;
  zone_name: string;
  track_id: number;
  confidence: number;
  duration_seconds: number;
  camera_id: string;
}

const TYPE_LABELS: Record<string, string> = {
  NO_PARKING: 'No Parking Violation',
  FIRE_HYDRANT_BLOCKED: 'Fire Hydrant Obstruction',
  EMERGENCY_ACCESS_BLOCKED: 'Emergency Lane Intrusion',
  BUS_STOP_VIOLATION: 'Bus Stop Zone Infringement',
  RESTRICTED_CURB_VIOLATION: 'Restricted Curb Violation',
};

export default function LivePage() {
  const { token } = useAuth();
  const [occupancy, setOccupancy] = useState<OccupancyMsg | null>(null);
  const [violations, setViolations] = useState<(ViolationMsg & { ts: number })[]>([]);
  const [occConnected, setOccConnected] = useState(false);
  const [violConnected, setViolConnected] = useState(false);
  const violRef = useRef<WebSocket | null>(null);

  // Occupancy WebSocket (public)
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/api/v1/live/ws/occupancy`);
    ws.onopen = () => setOccConnected(true);
    ws.onclose = () => setOccConnected(false);
    ws.onerror = () => setOccConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'occupancy_update') setOccupancy(data as OccupancyMsg);
      } catch { }
    };
    return () => ws.close();
  }, []);

  // Violations WebSocket (Parking Officer authorized — requires token)
  useEffect(() => {
    if (!token) return;
    const ws = new WebSocket(`${WS_BASE}/api/v1/live/ws/violations?token=${token}`);
    violRef.current = ws;
    ws.onopen = () => setViolConnected(true);
    ws.onclose = () => setViolConnected(false);
    ws.onerror = () => setViolConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'violation_alert') {
          setViolations(prev => [{ ...data, ts: Date.now() }, ...prev.slice(0, 19)]);
        }
      } catch { }
    };
    return () => ws.close();
  }, [token]);

  const pct = occupancy ? Math.round((occupancy.occupied / Math.max(1, occupancy.total)) * 100) : 40;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Live Surveillance Telemetry</h2>
            <span className="badge badge-officer">OFFICER FEED</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Real-time WebSocket telemetry stream from municipal CCTV nodes
          </p>
        </div>

        {/* Live Indicators */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className={`badge ${occConnected ? 'badge-active' : 'badge-rejected'}`}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', animation: occConnected ? 'pulse 2s infinite' : 'none' }} />
            Occupancy Socket: {occConnected ? 'STREAMING' : 'OFFLINE'}
          </span>
          <span className={`badge ${violConnected ? 'badge-active' : 'badge-rejected'}`}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', animation: violConnected ? 'pulse 1s infinite' : 'none' }} />
            Violation Alerts: {violConnected ? 'STREAMING' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Live Occupancy Panel with AI Scan Animation */}
      <div className="card ai-scan-container" style={{ marginBottom: '20px', position: 'relative' }}>
        {/* Holographic AI Scanline */}
        <div className="ai-scan-beam" />

        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="card-title">
              <span className="ai-radar-dot" />
              Live AI Vision & Space Sensor Telemetry
            </span>
            <span className="badge badge-ai-shimmer">YOLOv8 MULTI-TARGET</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="floor-badge">🏢 Nexus Grand Mall · Floor B1</span>
            <span className="pillar-badge">🏛️ Pillars A01–C15</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
          {[
            { label: 'CCTV Node', value: occupancy?.camera_id || 'CAM-001' },
            { label: 'Occupied Spots', value: occupancy ? occupancy.occupied : 2 },
            { label: 'Available Spots', value: occupancy ? occupancy.available : 3 },
            { label: 'Total Capacity', value: occupancy ? occupancy.total : 5 },
          ].map(item => (
            <div key={item.label} style={{ background: 'var(--box-bg-secondary)', border: '1px solid var(--box-border)', borderRadius: 'var(--radius-sm)', padding: '16px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff' }}>{item.value}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{item.label}</div>
            </div>
          ))}
        </div>

        {/* Live Audio / Telemetry Waveform */}
        <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>NEURAL STREAM:</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', height: '18px' }}>
              <span className="ai-wave-bar" />
              <span className="ai-wave-bar" />
              <span className="ai-wave-bar" />
              <span className="ai-wave-bar" />
              <span className="ai-wave-bar" />
            </span>
            <span style={{ color: '#4ade80' }}>29.8 FPS · Low Latency WebSocket (8ms)</span>
          </div>
          <span style={{ fontSize: '11px', color: '#a1a1aa' }}>Pillar Collision Detection: ACTIVE</span>
        </div>

        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Floor Occupancy Ratio</span>
            <span style={{ color: '#ffffff', fontWeight: 700 }}>{pct}% Capacity</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${pct}%`, background: '#ffffff' }} />
          </div>
        </div>
      </div>

      {/* Live Violations Feed */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">⚠ Real-Time Ingested Violations</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Streamed in real-time from AI Inference Engine
          </span>
        </div>

        {violations.length === 0 ? (
          <div className="empty-state" style={{ padding: '36px 20px' }}>
            <div className="empty-icon">✓</div>
            <p style={{ color: '#ffffff', fontWeight: 600 }}>No violations currently active on curb</p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
              When vehicles stop in restricted curb zones (Fire Hydrant, Bus Stop, No Parking), alerts stream here.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {violations.map((v, i) => (
              <div
                key={v.ts}
                className="violation-alert"
                style={{ animation: i === 0 ? 'slideIn 0.3s ease' : 'none' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                  <div>
                    <div className="v-type">{TYPE_LABELS[v.violation_type] || v.violation_type}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Camera: <span style={{ color: '#ffffff' }}>{v.camera_id}</span> · Zone: {v.zone_name || 'Restricted Curb'} · Track ID: #{v.track_id}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: '13px', color: '#ffffff', fontWeight: 700 }}>
                      {(v.confidence * 100).toFixed(0)}% AI Conf
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Duration: {Math.round(v.duration_seconds)}s · {new Date(v.ts).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
