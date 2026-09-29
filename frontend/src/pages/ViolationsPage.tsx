import { useEffect, useState } from 'react';
import { getViolations, updateViolationStatus, getEvidenceUrl, WS_BASE } from '../api';
import { useAuth } from '../contexts/AuthContext';

interface Violation {
  id: number;
  camera_id: string;
  violation_type: string;
  timestamp: string;
  duration_seconds: number;
  confidence: number;
  status: string;
  zone_name: string | null;
  track_id: number | null;
  evidence_reference: string | null;
}

const TYPE_LABELS: Record<string, string> = {
  NO_PARKING: 'No Parking Violation',
  FIRE_HYDRANT_BLOCKED: 'Fire Hydrant Obstruction',
  EMERGENCY_ACCESS_BLOCKED: 'Emergency Lane Intrusion',
  BUS_STOP_VIOLATION: 'Bus Stop Infringement',
  RESTRICTED_CURB_VIOLATION: 'Restricted Curb Violation',
};

export default function ViolationsPage() {
  const { token } = useAuth();
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [liveAlerts, setLiveAlerts] = useState<string[]>([]);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);

  const fetchViolations = async () => {
    try {
      const params: any = {};
      if (filter) params.status = filter;
      const res = await getViolations(params);
      setViolations(res.data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => {
    fetchViolations();
    if (!token) return;
    const ws = new WebSocket(`${WS_BASE}/api/v1/live/ws/violations?token=${token}`);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'violation_alert') {
          setLiveAlerts(a => [
            `⚠ ${TYPE_LABELS[data.violation_type] || data.violation_type} — Zone: ${data.zone_name || 'Restricted Curb'}`,
            ...a.slice(0, 4),
          ]);
          fetchViolations();
        }
      } catch { }
    };
    return () => ws.close();
  }, [filter]);

  const handleStatus = async (id: number, status: string) => {
    try {
      await updateViolationStatus(id, status);
      fetchViolations();
    } catch { }
  };

  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      PENDING_REVIEW: 'badge-pending',
      CONFIRMED: 'badge-confirmed',
      REJECTED: 'badge-rejected',
    };
    return <span className={`badge ${map[s] || 'badge-pending'}`}>{s.replace('_', ' ')}</span>;
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-page-title)', letterSpacing: '-0.025em' }}>
              Violation Review & Evidence Dispatch
            </h2>
            <span className="badge badge-officer">OFFICER AUDIT</span>
          </div>
          <p style={{ color: 'var(--text-page-muted)', fontSize: '13px' }}>
            Verify AI-detected parking violations, floor/pillar obstruction, and inspect annotated evidence photos
          </p>
        </div>

        {/* Status Filter */}
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '180px', height: '40px', background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <option value="">All Review Statuses</option>
          <option value="PENDING_REVIEW">Pending Review</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Live Alert Toast Banner */}
      {liveAlerts.length > 0 && (
        <div style={{ marginBottom: '18px' }}>
          {liveAlerts.map((a, i) => (
            <div key={i} className="violation-alert">
              <div className="v-type">{a}</div>
            </div>
          ))}
        </div>
      )}

      {/* Violations Table */}
      {loading ? (
        <div className="spinner" />
      ) : violations.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">✓</div>
            <p style={{ color: '#ffffff', fontWeight: 600 }}>No violations found</p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              All curb zones are compliant or no events matched the active filter.
            </p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Violation Type</th>
                  <th>Camera</th>
                  <th>Zone Name</th>
                  <th>Duration</th>
                  <th>Confidence</th>
                  <th>Review Status</th>
                  <th>Timestamp</th>
                  <th style={{ textAlign: 'right' }}>Officer Actions</th>
                </tr>
              </thead>
              <tbody>
                {violations.map(v => (
                  <tr key={v.id}>
                    <td className="mono" style={{ color: 'var(--text-muted)' }}>#{v.id}</td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {TYPE_LABELS[v.violation_type] || v.violation_type}
                    </td>
                    <td className="mono" style={{ fontSize: '12px' }}>{v.camera_id}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{v.zone_name || '—'}</td>
                    <td>{Math.round(v.duration_seconds)}s</td>
                    <td>
                      <span style={{ color: v.confidence > 0.8 ? '#ffffff' : 'var(--text-muted)', fontWeight: 600 }}>
                        {(v.confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td>{statusBadge(v.status)}</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(v.timestamp).toLocaleString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        {v.status === 'PENDING_REVIEW' && (
                          <>
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handleStatus(v.id, 'CONFIRMED')}
                            >
                              ✓ Confirm
                            </button>
                            <button
                              className="btn btn-ghost btn-sm"
                              onClick={() => handleStatus(v.id, 'REJECTED')}
                            >
                              ✗ Reject
                            </button>
                          </>
                        )}
                        {v.evidence_reference && (
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => setSelectedViolation(v)}
                            title="Inspect annotated snapshot"
                          >
                            🖼️ Evidence
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Evidence Snapshot Modal */}
      {selectedViolation && (
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
            padding: '20px',
          }}
          onClick={() => setSelectedViolation(null)}
        >
          <div
            style={{
              background: '#0d0d10',
              border: '1px solid #27272a',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '740px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
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
                <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                  {TYPE_LABELS[selectedViolation.violation_type] || selectedViolation.violation_type} Evidence
                </h3>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Violation #{selectedViolation.id} · Camera {selectedViolation.camera_id} · Track ID: #{selectedViolation.track_id}
                </span>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                style={{ fontSize: '16px', lineHeight: 1 }}
                onClick={() => setSelectedViolation(null)}
              >
                ✕
              </button>
            </div>

            {/* Evidence Image */}
            <div style={{ padding: '20px', overflowY: 'auto' }}>
              <div
                style={{
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                  background: '#000000',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  minHeight: '280px',
                }}
              >
                <img
                  src={getEvidenceUrl(selectedViolation.id)}
                  alt={`Violation ${selectedViolation.id} Evidence`}
                  style={{ maxWidth: '100%', maxHeight: '420px', objectFit: 'contain' }}
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                    const fallback = document.getElementById('evidence-fallback');
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
                <div
                  id="evidence-fallback"
                  style={{ display: 'none', flexDirection: 'column', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', padding: '40px' }}
                >
                  <span style={{ fontSize: '32px' }}>📷</span>
                  <span style={{ fontSize: '13px' }}>Evidence image not written or path expired</span>
                </div>
              </div>

              {/* Metrics */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                  marginTop: '16px',
                }}
              >
                <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Duration</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                    {Math.round(selectedViolation.duration_seconds)}s
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>AI Confidence</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                    {(selectedViolation.confidence * 100).toFixed(0)}%
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Status</div>
                  <div style={{ marginTop: '2px' }}>{statusBadge(selectedViolation.status)}</div>
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div
              style={{
                padding: '14px 20px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#09090b',
              }}
            >
              <a
                href={getEvidenceUrl(selectedViolation.id)}
                target="_blank"
                rel="noreferrer"
                className="btn btn-ghost btn-sm"
              >
                ↗ Open Full Resolution
              </a>
              <div style={{ display: 'flex', gap: '8px' }}>
                {selectedViolation.status === 'PENDING_REVIEW' && (
                  <>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={async () => {
                        await handleStatus(selectedViolation.id, 'REJECTED');
                        setSelectedViolation(null);
                      }}
                    >
                      ✗ Reject
                    </button>
                    <button
                      className="btn btn-success btn-sm"
                      onClick={async () => {
                        await handleStatus(selectedViolation.id, 'CONFIRMED');
                        setSelectedViolation(null);
                      }}
                    >
                      ✓ Confirm Violation
                    </button>
                  </>
                )}
                <button className="btn btn-secondary btn-sm" onClick={() => setSelectedViolation(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
