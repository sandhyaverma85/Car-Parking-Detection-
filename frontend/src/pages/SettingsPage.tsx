export default function SettingsPage() {
  const configs = [
    {
      group: 'AI & Computer Vision Pipeline',
      items: [
        { key: 'MODEL_PATH', value: 'yolov8n.pt', desc: 'Pre-trained YOLOv8 weights file' },
        { key: 'CONFIDENCE_THRESHOLD', value: '0.50', desc: 'Minimum object detection confidence threshold' },
        { key: 'IOU_THRESHOLD', value: '0.45', desc: 'Non-maximum suppression IoU threshold' },
        { key: 'FRAME_SKIP', value: '2', desc: 'Process every Nth video frame to conserve GPU/CPU' },
        { key: 'VIOLATION_DURATION_SECONDS', value: '30s', desc: 'Continuous stationary duration before violation event' },
        { key: 'PARKING_OVERLAP_THRESHOLD', value: '0.30', desc: 'Minimum IoU overlap between vehicle and slot polygon' },
      ],
    },
    {
      group: 'Security & Access Control (RBAC)',
      items: [
        { key: 'CCTV_POLICY', value: 'PARKING OFFICER EXCLUSIVE', desc: 'Camera video footage and live surveillance restricted strictly to Parking Officers' },
        { key: 'JWT_ALGORITHM', value: 'HS256', desc: 'Cryptographic token signing algorithm' },
        { key: 'JWT_EXPIRY', value: '30 minutes', desc: 'Access token lifetime before re-authentication' },
        { key: 'PASSWORD_HASH', value: 'Argon2id', desc: 'OWASP-compliant key derivation function' },
        { key: 'RATE_LIMIT_LOGIN', value: '5 / min', desc: 'Brute-force mitigation per client IP' },
      ],
    },
    {
      group: 'Data Storage & Database',
      items: [
        { key: 'DEV_DATABASE', value: 'SQLite + AioSQLite', desc: 'Zero-configuration async local SQL engine' },
        { key: 'PROD_DATABASE', value: 'PostgreSQL + PostGIS', desc: 'Geospatial database with spatial polygon indexing' },
        { key: 'EVIDENCE_DIR', value: 'evidence/', desc: 'Local directory for annotated JPEG violation frames' },
      ],
    },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.025em' }}>
          MallPark AI · System Settings & Parameters
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          YOLOv8 inference thresholds, camera fleet RTSP feeds, and automated e-citation rules
        </p>
      </div>

      {/* Advisory Callout */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderLeft: '3px solid #ffffff',
        borderRadius: 'var(--radius-sm)',
        padding: '16px 20px',
        marginBottom: '24px',
        display: 'flex',
        gap: '14px',
        alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: '20px', flexShrink: 0 }}>ℹ️</span>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff', marginBottom: '2px' }}>
            Central Configuration Authority
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            All thresholds are managed via <code style={{ color: '#ffffff' }}>.env</code>.
            Sensitive keys (JWT secrets, internal AI keys, database credentials) are never exposed via API endpoints.
          </div>
        </div>
      </div>

      {/* Configuration Tables */}
      {configs.map(group => (
        <div key={group.group} className="card" style={{ marginBottom: '20px', padding: 0 }}>
          <div className="card-header" style={{ padding: '16px 20px', margin: 0 }}>
            <span className="card-title">{group.group}</span>
          </div>
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '220px' }}>Parameter</th>
                  <th style={{ width: '200px' }}>Configured Value</th>
                  <th>Functional Description</th>
                </tr>
              </thead>
              <tbody>
                {group.items.map(item => (
                  <tr key={item.key}>
                    <td>
                      <code className="mono" style={{ fontSize: '12px', color: '#ffffff', fontWeight: 600 }}>
                        {item.key}
                      </code>
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                        {item.value}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {item.desc}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {/* Service Endpoints */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">🌐 Platform Service Nodes</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          {[
            { name: 'FastAPI REST API', url: 'http://localhost:8000', desc: 'Core backend service' },
            { name: 'Swagger Documentation', url: 'http://localhost:8000/docs', desc: 'Interactive API explorer' },
            { name: 'Health Endpoint', url: 'http://localhost:8000/health', desc: 'System liveness probe' },
            { name: 'WebSocket Occupancy', url: 'ws://localhost:8000/api/v1/live/ws/occupancy', desc: 'Public telemetry socket' },
          ].map(ep => (
            <a
              key={ep.name}
              href={ep.url.startsWith('ws') ? undefined : ep.url}
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'block',
                background: 'var(--bg-surface)',
                padding: '16px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                transition: 'var(--transition)',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
                {ep.name}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                {ep.desc}
              </div>
              <div className="mono" style={{ fontSize: '11px', color: 'var(--text-dim)', wordBreak: 'break-all' }}>
                {ep.url}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
