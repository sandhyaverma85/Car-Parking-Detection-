import { useEffect, useState } from 'react';
import { getAnalytics, getOccupancyAnalytics } from '../api';
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend, CategoryScale, LinearScale,
  PointElement, LineElement, BarElement, Title, Filler
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Filler);

// Monochrome palette for high-contrast charts
const MONO_SHADES = ['#ffffff', '#e4e4e7', '#a1a1aa', '#71717a', '#52525b'];

const VIOLATION_LABELS: Record<string, string> = {
  NO_PARKING: 'No Parking',
  FIRE_HYDRANT_BLOCKED: 'Fire Hydrant',
  EMERGENCY_ACCESS_BLOCKED: 'Emergency Access',
  BUS_STOP_VIOLATION: 'Bus Stop',
  RESTRICTED_CURB_VIOLATION: 'Restricted Curb',
};

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#a1a1aa',
        font: { family: 'Plus Jakarta Sans', size: 11 },
        boxWidth: 12,
      },
    },
    tooltip: {
      backgroundColor: '#18181b',
      titleColor: '#ffffff',
      bodyColor: '#e4e4e7',
      borderColor: '#27272a',
      borderWidth: 1,
    },
  },
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [occupancy, setOccupancy] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      getAnalytics().catch(() => ({ data: null })),
      getOccupancyAnalytics().catch(() => ({ data: [] })),
    ]).then(([a, o]) => {
      setAnalytics(a.data);
      setOccupancy(o.data ?? []);
    }).catch(e => setError(e.response?.data?.detail || 'Failed to load analytics'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" style={{ marginTop: '60px' }} />;
  if (error) return <div className="card" style={{ color: '#fca5a5' }}>{error}</div>;

  const violationTypes = analytics?.violations_by_type ?? [];
  const doughnutData = {
    labels: violationTypes.map((v: any) => VIOLATION_LABELS[v.violation_type] ?? v.violation_type),
    datasets: [{
      data: violationTypes.map((v: any) => v.count),
      backgroundColor: violationTypes.map((_: any, idx: number) => MONO_SHADES[idx % MONO_SHADES.length]),
      borderColor: '#121216',
      borderWidth: 2,
    }],
  };

  const occupancyBarData = {
    labels: occupancy.map((o: any) => o.zone_name),
    datasets: [
      {
        label: 'Average Occupancy %',
        data: occupancy.map((o: any) => o.average_occupancy_pct),
        backgroundColor: '#ffffff',
        borderColor: '#ffffff',
        borderWidth: 0,
        borderRadius: 4,
      },
      {
        label: 'Peak Occupancy %',
        data: occupancy.map((o: any) => o.peak_occupancy_pct),
        backgroundColor: 'rgba(255, 255, 255, 0.25)',
        borderColor: 'rgba(255, 255, 255, 0.5)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const barOpts = {
    ...CHART_OPTS,
    scales: {
      x: {
        ticks: { color: '#71717a', font: { family: 'Plus Jakarta Sans', size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        ticks: { color: '#71717a', font: { family: 'Plus Jakarta Sans', size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
        max: 100,
      },
    },
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.025em' }}>
          MallPark AI · Analytics & Telemetry Reports
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          1,480 Total Bays · 84% Occupancy · Sector D & Zone B Peak Utilization Trends
        </p>
      </div>

      {/* KPI Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Violations Today</span>
            <span className="stat-icon">⚠</span>
          </div>
          <div className="stat-value">{analytics?.total_violations_today ?? 0}</div>
          <div className="stat-sub">Recorded since 00:00 UTC</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Violations This Week</span>
            <span className="stat-icon">📅</span>
          </div>
          <div className="stat-value">{analytics?.total_violations_week ?? 0}</div>
          <div className="stat-sub">Last 7 days total</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Monitored Zones</span>
            <span className="stat-icon">🏙️</span>
          </div>
          <div className="stat-value">{occupancy.length || 1}</div>
          <div className="stat-sub">Active curb sectors</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Violation Types</span>
            <span className="stat-icon">▤</span>
          </div>
          <div className="stat-value">{violationTypes.length}</div>
          <div className="stat-sub">Categorized offences</div>
        </div>
      </div>

      {/* Two Column Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        {/* Doughnut Chart */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <span className="card-title">🚨 Violations by Classification</span>
          </div>
          {violationTypes.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-icon">✓</div>
              <p>No violation data recorded</p>
            </div>
          ) : (
            <div style={{ height: '240px', position: 'relative' }}>
              <Doughnut data={doughnutData} options={CHART_OPTS} />
            </div>
          )}
        </div>

        {/* Breakdown Table */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <span className="card-title">📋 Category Breakdown</span>
          </div>
          {violationTypes.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-icon">✓</div>
              <p>No events recorded</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Offence Type</th>
                    <th>Count</th>
                    <th>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {violationTypes.map((v: any, idx: number) => (
                    <tr key={v.violation_type}>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>
                        {VIOLATION_LABELS[v.violation_type] ?? v.violation_type}
                      </td>
                      <td className="mono">{v.count}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ flex: 1, background: 'var(--bg-elevated)', borderRadius: '4px', height: '6px' }}>
                            <div
                              style={{
                                width: `${v.percentage}%`,
                                background: MONO_SHADES[idx % MONO_SHADES.length],
                                height: '6px',
                                borderRadius: '4px',
                              }}
                            />
                          </div>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', minWidth: '32px' }}>
                            {v.percentage}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Zone Occupancy Bar Chart */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">🅿 Average vs Peak Zone Occupancy</span>
        </div>
        {occupancy.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px 20px' }}>
            <div className="empty-icon">📊</div>
            <p>No occupancy statistics recorded yet</p>
          </div>
        ) : (
          <div style={{ height: '280px' }}>
            <Bar data={occupancyBarData} options={barOpts as any} />
          </div>
        )}
      </div>
    </div>
  );
}
