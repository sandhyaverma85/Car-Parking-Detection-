import { useEffect, useState } from 'react';
import { getParkingZones, WS_BASE } from '../api';

interface ParkingSlotData {
  id: string;
  slotNumber: number;
  mallName: string;
  floorNo: string;
  floorLabel: string;
  pillarNo: string;
  zoneCode: string;
  status: 'EMPTY' | 'OCCUPIED';
  vehicleType?: string;
  proximity: string;
  cameraId: string;
}

// Multi-Level Mall & Commercial Building Parking Registry
const MALL_PARKING_REGISTRY: ParkingSlotData[] = [
  // ── Nexus Grand Mall (Floor B1 - Basement 1) ──────────────────────────
  {
    id: 'NX-B1-01',
    slotNumber: 1,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Hypermarket & Food Court)',
    pillarNo: 'Pillar A-01',
    zoneCode: 'ZONE A',
    status: 'EMPTY',
    vehicleType: 'EV Charging / Compact',
    proximity: '8m to North Lift Lobby A',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B1-02',
    slotNumber: 2,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Hypermarket & Food Court)',
    pillarNo: 'Pillar A-04',
    zoneCode: 'ZONE A',
    status: 'OCCUPIED',
    vehicleType: 'Sedan (KA-01-MJ-4412)',
    proximity: '12m to North Escalator 1',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B1-03',
    slotNumber: 3,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Hypermarket & Food Court)',
    pillarNo: 'Pillar B-08',
    zoneCode: 'ZONE B',
    status: 'EMPTY',
    vehicleType: 'Standard SUV / Sedan',
    proximity: '15m to Central Atrium Lift',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B1-04',
    slotNumber: 4,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Hypermarket & Food Court)',
    pillarNo: 'Pillar C-12',
    zoneCode: 'ZONE C',
    status: 'OCCUPIED',
    vehicleType: 'SUV (KA-05-NB-9810)',
    proximity: '18m to Food Court Entrance',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B1-05',
    slotNumber: 5,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Hypermarket & Food Court)',
    pillarNo: 'Pillar C-15',
    zoneCode: 'ZONE C',
    status: 'EMPTY',
    vehicleType: 'Handicapped Accessible / Van',
    proximity: '5m to Disabled Ramp & Lift B',
    cameraId: 'CAM-001',
  },

  // ── Nexus Grand Mall (Floor B2 - Basement 2) ──────────────────────────
  {
    id: 'NX-B2-06',
    slotNumber: 6,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B2',
    floorLabel: 'Basement 2 (Multiplex & Retail Arcade)',
    pillarNo: 'Pillar D-03',
    zoneCode: 'ZONE D',
    status: 'EMPTY',
    vehicleType: 'Standard Sedan',
    proximity: '10m to PVR IMAX Cinema Lift',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B2-07',
    slotNumber: 7,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B2',
    floorLabel: 'Basement 2 (Multiplex & Retail Arcade)',
    pillarNo: 'Pillar D-09',
    zoneCode: 'ZONE D',
    status: 'OCCUPIED',
    vehicleType: 'Sedan (KA-03-EX-1102)',
    proximity: '14m to West Stairwell 2',
    cameraId: 'CAM-001',
  },
  {
    id: 'NX-B2-08',
    slotNumber: 8,
    mallName: 'Nexus Grand Mall',
    floorNo: 'Floor B2',
    floorLabel: 'Basement 2 (Multiplex & Retail Arcade)',
    pillarNo: 'Pillar E-05',
    zoneCode: 'ZONE E',
    status: 'EMPTY',
    vehicleType: 'Electric Vehicle Fast Bay',
    proximity: '6m to EV Charging Station 4',
    cameraId: 'CAM-001',
  },

  // ── Phoenix Marketcity Mall (Floor B1 & Floor L2) ────────────────────
  {
    id: 'PH-B1-01',
    slotNumber: 9,
    mallName: 'Phoenix Marketcity Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Premium Galleria Deck)',
    pillarNo: 'Pillar P-02',
    zoneCode: 'ZONE P',
    status: 'EMPTY',
    vehicleType: 'Large SUV / Pickup',
    proximity: '12m to Central Galleria Entry',
    cameraId: 'CAM-001',
  },
  {
    id: 'PH-B1-02',
    slotNumber: 10,
    mallName: 'Phoenix Marketcity Mall',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Premium Galleria Deck)',
    pillarNo: 'Pillar P-07',
    zoneCode: 'ZONE P',
    status: 'OCCUPIED',
    vehicleType: 'Coupe (KA-04-AB-3390)',
    proximity: '16m to Zara / H&M Mall Lobby',
    cameraId: 'CAM-001',
  },
  {
    id: 'PH-L2-03',
    slotNumber: 11,
    mallName: 'Phoenix Marketcity Mall',
    floorNo: 'Floor L2',
    floorLabel: 'Level 2 (Executive Covered Deck)',
    pillarNo: 'Pillar R-14',
    zoneCode: 'ZONE R',
    status: 'EMPTY',
    vehicleType: 'Executive Valet / Sedan',
    proximity: '4m to VIP Valet Drop-off',
    cameraId: 'CAM-001',
  },

  // ── Orion Commercial Complex (Floor B1 & B2) ────────────────────────
  {
    id: 'OR-B1-01',
    slotNumber: 12,
    mallName: 'Orion Commercial Complex',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Corporate Tech Wing)',
    pillarNo: 'Pillar W-04',
    zoneCode: 'ZONE W',
    status: 'OCCUPIED',
    vehicleType: 'Fleet Van (KA-51-TR-8821)',
    proximity: '9m to Tower A Security Gate',
    cameraId: 'CAM-001',
  },
  {
    id: 'OR-B1-02',
    slotNumber: 13,
    mallName: 'Orion Commercial Complex',
    floorNo: 'Floor B1',
    floorLabel: 'Basement 1 (Corporate Tech Wing)',
    pillarNo: 'Pillar W-11',
    zoneCode: 'ZONE W',
    status: 'EMPTY',
    vehicleType: 'Standard Sedan',
    proximity: '14m to Brigade Tech Entrance',
    cameraId: 'CAM-001',
  },
  {
    id: 'OR-B2-03',
    slotNumber: 14,
    mallName: 'Orion Commercial Complex',
    floorNo: 'Floor B2',
    floorLabel: 'Basement 2 (Logistics & Commercial Dock)',
    pillarNo: 'Pillar X-08',
    zoneCode: 'ZONE X',
    status: 'EMPTY',
    vehicleType: 'Commercial Loading / Delivery',
    proximity: '5m to Freight Elevator 3',
    cameraId: 'CAM-001',
  },
];

export default function ParkingPage() {
  const [slots, setSlots] = useState<ParkingSlotData[]>(MALL_PARKING_REGISTRY);
  const [selectedMall, setSelectedMall] = useState<string>('ALL');
  const [selectedFloor, setSelectedFloor] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'EMPTY' | 'OCCUPIED'>('ALL');
  const [search, setSearch] = useState('');
  const [liveOccupancy, setLiveOccupancy] = useState<{ occupied: number; total: number }>({ occupied: 5, total: 14 });
  const [aiTrackingActive, setAiTrackingActive] = useState(true);

  useEffect(() => {
    // Fetch live backend zones as well
    getParkingZones().catch(() => {});

    // Live occupancy socket updates
    const ws = new WebSocket(`${WS_BASE}/api/v1/live/ws/occupancy`);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'occupancy_update') {
          setLiveOccupancy({
            occupied: data.occupied,
            total: Math.max(data.total, 14),
          });
        }
      } catch {}
    };
    return () => ws.close();
  }, []);

  // Filter slots by mall, floor, status, and pillar search
  const filteredSlots = slots.filter(slot => {
    const matchesMall = selectedMall === 'ALL' || slot.mallName === selectedMall;
    const matchesFloor = selectedFloor === 'ALL' || slot.floorNo === selectedFloor;
    const matchesStatus = statusFilter === 'ALL' || slot.status === statusFilter;
    const q = search.toLowerCase();
    const matchesSearch =
      slot.pillarNo.toLowerCase().includes(q) ||
      slot.floorNo.toLowerCase().includes(q) ||
      slot.mallName.toLowerCase().includes(q) ||
      slot.id.toLowerCase().includes(q) ||
      slot.proximity.toLowerCase().includes(q);

    return matchesMall && matchesFloor && matchesStatus && matchesSearch;
  });

  const totalFiltered = filteredSlots.length;
  const vacantFiltered = filteredSlots.filter(s => s.status === 'EMPTY').length;
  const occupiedFiltered = totalFiltered - vacantFiltered;
  const occupancyPct = totalFiltered > 0 ? Math.round((occupiedFiltered / totalFiltered) * 100) : 0;

  // Toggle slot occupancy for officer manual override
  const handleToggleSlot = (id: string) => {
    setSlots(prev => prev.map(s => {
      if (s.id === id) {
        const newStatus = s.status === 'EMPTY' ? 'OCCUPIED' : 'EMPTY';
        return {
          ...s,
          status: newStatus,
          vehicleType: newStatus === 'OCCUPIED' ? 'Vehicle Marked by Officer' : undefined,
        };
      }
      return s;
    }));
  };

  return (
    <div>
      {/* Page Title & AI Surveillance Strip */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span className="badge badge-active badge-ai-shimmer">
              <span className="ai-radar-dot" />
              AI PILLAR & FLOOR SENSING ACTIVE
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-page-muted)', fontWeight: 600 }}>
              Camera CAM-001 Vision Stream · Live Socket Telemetry ({liveOccupancy.occupied} in use / {liveOccupancy.total} capacity)
            </span>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.025em' }}>
            MallPark AI · Level Zones & Sector Grids
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Sector D & Zone B multi-level floor management, pillar localization, and real-time bay telemetry
          </p>
        </div>

        {/* AI Sensing Switch & Quick Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => setAiTrackingActive(!aiTrackingActive)}
            className="btn btn-secondary btn-sm"
            style={{ background: '#09090c', color: '#ffffff', border: '1px solid #27272f' }}
          >
            <span className="ai-radar-dot" style={{ background: aiTrackingActive ? '#22c55e' : '#6b7280' }} />
            {aiTrackingActive ? 'AI Scan: ACTIVE' : 'AI Scan: PAUSED'}
          </button>
        </div>
      </div>

      {/* Overview Stat Cards (Solid Black Floating Boxes) */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Total Monitored Bays</span>
            <span className="stat-icon">🅿</span>
          </div>
          <div className="stat-value">{totalFiltered}</div>
          <div className="stat-sub">Across selected floors & pillars</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Vacant Parking Spots</span>
            <span className="stat-icon" style={{ color: '#4ade80' }}>✓</span>
          </div>
          <div className="stat-value" style={{ color: '#4ade80' }}>{vacantFiltered}</div>
          <div className="stat-sub">Ready for incoming vehicles</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Occupied Spots</span>
            <span className="stat-icon" style={{ color: '#f87171' }}>🚗</span>
          </div>
          <div className="stat-value" style={{ color: '#f87171' }}>{occupiedFiltered}</div>
          <div className="stat-sub">Vehicles parked under pillars</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Floor Utilization</span>
            <span className="stat-icon">%</span>
          </div>
          <div className="stat-value">{occupancyPct}%</div>
          <div className="progress-bar" style={{ marginTop: '10px' }}>
            <div
              className="progress-fill"
              style={{
                width: `${occupancyPct}%`,
                background: occupancyPct > 80 ? 'var(--status-alert)' : occupancyPct > 50 ? 'var(--status-warn)' : '#ffffff',
              }}
            />
          </div>
        </div>
      </div>

      {/* Building & Mall Filter Selector (Solid Black Floating Box) */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            🏢 Select Mall or Commercial Building:
          </div>
          <div style={{ fontSize: '11px', color: '#4ade80' }}>
            ● 4 Facilities Synced with CCTV
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { id: 'ALL', label: 'All Buildings' },
            { id: 'Nexus Grand Mall', label: 'Nexus Grand Mall (MG Road CBD)' },
            { id: 'Phoenix Marketcity Mall', label: 'Phoenix Marketcity & Palladium' },
            { id: 'Orion Commercial Complex', label: 'Orion Commercial Tech Hub' },
          ].map(mall => (
            <button
              key={mall.id}
              onClick={() => setSelectedMall(mall.id)}
              className="btn btn-sm"
              style={{
                background: selectedMall === mall.id ? '#ffffff' : '#141418',
                color: selectedMall === mall.id ? '#000000' : '#ffffff',
                fontWeight: selectedMall === mall.id ? 800 : 500,
                border: '1px solid',
                borderColor: selectedMall === mall.id ? '#ffffff' : '#27272f',
              }}
            >
              {mall.label}
            </button>
          ))}
        </div>
      </div>

      {/* Floor Level Filter + Search Controls (Solid Black Floating Box) */}
      <div className="card" style={{ padding: '18px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
          {/* Floor Level Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Floor Level:
            </span>
            {[
              { id: 'ALL', label: 'All Floors' },
              { id: 'Floor B1', label: 'Floor B1 (Basement 1)' },
              { id: 'Floor B2', label: 'Floor B2 (Basement 2)' },
              { id: 'Floor L2', label: 'Floor L2 (Level 2)' },
            ].map(fl => (
              <button
                key={fl.id}
                onClick={() => setSelectedFloor(fl.id)}
                className="btn btn-sm"
                style={{
                  background: selectedFloor === fl.id ? '#ffffff' : 'transparent',
                  color: selectedFloor === fl.id ? '#000000' : 'var(--text-secondary)',
                  fontWeight: selectedFloor === fl.id ? 800 : 500,
                  border: '1px solid',
                  borderColor: selectedFloor === fl.id ? '#ffffff' : '#27272f',
                }}
              >
                {fl.label}
              </button>
            ))}
          </div>

          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '6px', background: '#000000', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--box-border)' }}>
            {(['ALL', 'EMPTY', 'OCCUPIED'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className="btn btn-sm"
                style={{
                  background: statusFilter === tab ? '#ffffff' : 'transparent',
                  color: statusFilter === tab ? '#000000' : 'var(--text-muted)',
                  fontWeight: statusFilter === tab ? 800 : 500,
                  border: 'none',
                  padding: '6px 12px',
                }}
              >
                {tab === 'ALL' ? 'All Bays' : tab === 'EMPTY' ? 'Vacant Only' : 'Occupied Only'}
              </button>
            ))}
          </div>
        </div>

        {/* Pillar & Spot Search Bar */}
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            placeholder="Search by Pillar No (e.g. Pillar A-01, Pillar C-12), Floor, Mall name or Lift lobby..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              paddingLeft: '42px',
              height: '46px',
              fontSize: '13px',
              borderRadius: 'var(--radius-sm)',
              background: '#000000',
              borderColor: '#27272f',
              color: '#ffffff',
            }}
          />
          <span style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)', fontSize: '16px' }}>
            🔍
          </span>
          {search && (
            <button
              onClick={() => setSearch('')}
              style={{
                position: 'absolute',
                right: '14px',
                top: '12px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              ✕ Clear
            </button>
          )}
        </div>
      </div>

      {/* Parking Slot Cards Grid (High-Contrast Black Boxes on White Page Canvas) */}
      {filteredSlots.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">🏛️</div>
            <p style={{ color: '#ffffff', fontWeight: 600, fontSize: '15px' }}>
              No parking slots found matching your pillar or floor filter
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
              Try searching for a different pillar number like <code style={{ color: '#ffffff' }}>Pillar A-01</code> or reset filters.
            </p>
            <button
              className="btn btn-primary btn-sm"
              style={{ marginTop: '16px' }}
              onClick={() => { setSelectedMall('ALL'); setSelectedFloor('ALL'); setStatusFilter('ALL'); setSearch(''); }}
            >
              Reset All Filters
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '22px' }}>
          {filteredSlots.map(slot => {
            const isVacant = slot.status === 'EMPTY';

            return (
              <div
                key={slot.id}
                className="card"
                style={{
                  marginBottom: 0,
                  border: isVacant ? '1px solid #27272f' : '1px solid rgba(239, 68, 68, 0.45)',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* AI Laser Scanline Overlay on Active Sensing Slots */}
                {aiTrackingActive && (
                  <div className="ai-scan-container" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px' }}>
                    <div className="ai-scan-beam" style={{ height: '2px' }} />
                  </div>
                )}

                {/* Top Header: Mall Name & Live Status Badge */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '2px' }}>
                      {slot.mallName}
                    </div>
                    <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', margin: 0 }}>
                      Bay Code: {slot.id}
                    </h3>
                  </div>

                  <span className={`badge ${isVacant ? 'badge-active' : 'badge-confirmed'}`}>
                    <span className={isVacant ? 'ai-radar-dot' : 'ai-radar-dot-alert'} />
                    {isVacant ? '● VACANT' : '● OCCUPIED'}
                  </span>
                </div>

                {/* PRIMARY HIGHLIGHT: PILLAR NUMBER & FLOOR NUMBER */}
                <div style={{
                  background: 'var(--box-bg-secondary)',
                  border: '1px solid #27272f',
                  borderRadius: 'var(--radius-sm)',
                  padding: '14px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                }}>
                  {/* Pillar Identification */}
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>
                      Pillar Location
                    </div>
                    <div className="pillar-badge">
                      <span>🏛️</span>
                      <span>{slot.pillarNo}</span>
                    </div>
                  </div>

                  {/* Floor Level Identification */}
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>
                      Building Level
                    </div>
                    <div className="floor-badge">
                      <span>🏢</span>
                      <span>{slot.floorNo}</span>
                    </div>
                  </div>
                </div>

                {/* Detailed Floor Context & Walking Distance */}
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <span style={{ color: '#4ade80' }}>📍</span>
                    <span><strong>Area:</strong> {slot.floorLabel}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: '#38bdf8' }}>🚶</span>
                    <span><strong>Proximity:</strong> {slot.proximity}</span>
                  </div>
                </div>

                {/* Vehicle Classification & AI Stream Tag */}
                <div style={{
                  background: 'var(--box-bg-elevated)',
                  border: '1px solid #27272f',
                  borderRadius: 'var(--radius-xs)',
                  padding: '10px 12px',
                  fontSize: '11px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '18px',
                }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Compatible: </span>
                    <span style={{ color: '#ffffff', fontWeight: 600 }}>{slot.vehicleType || 'Any Passenger Vehicle'}</span>
                  </div>
                  <div className="mono" style={{ color: '#a1a1aa' }}>
                    {slot.cameraId}
                  </div>
                </div>

                {/* Card Footer: Real-time Bay Status & Officer Action */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--box-border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: isVacant ? '#4ade80' : '#f87171',
                      boxShadow: isVacant ? '0 0 8px #4ade80' : '0 0 8px #f87171',
                      display: 'inline-block',
                      animation: isVacant ? 'pulse 2s infinite' : 'none',
                    }} />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: isVacant ? '#4ade80' : '#f87171', letterSpacing: '0.04em' }}>
                      {isVacant ? 'BAY AVAILABLE' : 'BAY IN-USE'}
                    </span>
                  </div>

                  <button
                    onClick={() => handleToggleSlot(slot.id)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '11px', padding: '6px 14px' }}
                  >
                    {isVacant ? 'Mark In-Use' : 'Free Up Bay'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
