import React, { useState, useMemo } from 'react';
import { DATABASE_CUISINE_OPTIONS } from '../data/database_catalog';

export type TimeRange = 'all' | 'ytd' | 'q3' | '30d' | 'today';
export type CustomerCohort = 'All' | 'Gen Z' | 'Millennial' | 'Gen X' | 'Boomer';

interface FilterState {
  timeRange: TimeRange;
  city: string;
  generation: CustomerCohort;
  cuisine: string;
  status: string;
}

interface RestaurantMetric {
  rank: number;
  name: string;
  city: string;
  cuisine: string;
  orders: number;
  gmv: number;
  rating: number;
  slaPercent: number;
  trend: string;
  cohortWeights: Record<Exclude<CustomerCohort, 'All'>, number>; // percentages summing to 100
}

interface HybridTelemetryOrder {
  orderId: string;
  restaurant: string;
  city: string;
  source: 'Kafka Stream (9092)' | 'Auto Loader (S3)';
  cohort: Exclude<CustomerCohort, 'All'>;
  timeRange: TimeRange;
  timestamp: string;
  distanceKm: number;
  prepScore: number;
  predictedEtaMins: number;
  actualMins?: number;
  confidence: number;
  snowflakeLatencyMs: number;
  status: 'PREDICTED' | 'DISPATCHED' | 'DELIVERED';
}

const HORIZON_CONFIG: Record<TimeRange, { label: string; factor: number; velocity: number; latencyMs: number; badge: string; trendNote: string }> = {
  all: { label: 'All Time (Historical)', factor: 1.0, velocity: 52480, latencyMs: 38, badge: 'Multi-Year Warehouse', trendNote: '+16.8% YoY vs budget' },
  ytd: { label: 'Year-to-Date (2024)', factor: 0.74, velocity: 49800, latencyMs: 35, badge: 'Jan - Oct 2024 Marts', trendNote: '+19.2% YTD expansion' },
  q3: { label: 'Q3 Rolling Quarter', factor: 0.28, velocity: 44200, latencyMs: 32, badge: 'Q3 Consolidated', trendNote: '+14.5% QoQ delivered' },
  '30d': { label: 'Last 30 Days', factor: 0.095, velocity: 56100, latencyMs: 28, badge: 'Rolling 30-Day Window', trendNote: '+8.3% MoM velocity' },
  today: { label: 'Today (Live Stream)', factor: 0.0038, velocity: 68400, latencyMs: 22, badge: 'Live Intraday Stream', trendNote: '+24.1% Peak hour burst' }
};

const COHORT_PROFILES: Record<Exclude<CustomerCohort, 'All'>, { label: string; aovMultiplier: number; baseShare: number; color: string; desc: string; icon: string }> = {
  'Gen Z': { label: 'Gen Z (< 25 yrs)', aovMultiplier: 0.72, baseShare: 34, color: '#10b981', desc: 'Late-night burgers, desserts, fast delivery', icon: '⚡' },
  'Millennial': { label: 'Millennials (25 - 40 yrs)', aovMultiplier: 1.08, baseShare: 42, color: '#3b82f6', desc: 'Core revenue driver, dinner combos, family bundles', icon: '💼' },
  'Gen X': { label: 'Gen X (40 - 55 yrs)', aovMultiplier: 1.35, baseShare: 18, color: '#F2C811', desc: 'High basket fine dining, curated Mughlai & North Indian', icon: '👔' },
  'Boomer': { label: 'Boomers (55+ yrs)', aovMultiplier: 1.15, baseShare: 6, color: '#a855f7', desc: 'Traditional heritage dining, lunch hours, high brand loyalty', icon: '🏡' }
};

const RAW_DATA: RestaurantMetric[] = [
  {
    rank: 1,
    name: "Truffles Central",
    city: "Bangalore",
    cuisine: "Burgers, Continental",
    orders: 142800,
    gmv: 42840000,
    rating: 4.6,
    slaPercent: 96.2,
    trend: "+12.4%",
    cohortWeights: { 'Gen Z': 0.54, 'Millennial': 0.34, 'Gen X': 0.10, 'Boomer': 0.02 }
  },
  {
    rank: 2,
    name: "Empire Restaurant",
    city: "Bangalore",
    cuisine: "North Indian, Biryani",
    orders: 210500,
    gmv: 61045000,
    rating: 4.3,
    slaPercent: 93.8,
    trend: "+8.7%",
    cohortWeights: { 'Gen Z': 0.24, 'Millennial': 0.46, 'Gen X': 0.20, 'Boomer': 0.10 }
  },
  {
    rank: 3,
    name: "Bastian Bandra",
    city: "Mumbai",
    cuisine: "Seafood, Asian",
    orders: 84200,
    gmv: 67360000,
    rating: 4.7,
    slaPercent: 95.1,
    trend: "+21.5%",
    cohortWeights: { 'Gen Z': 0.26, 'Millennial': 0.54, 'Gen X': 0.18, 'Boomer': 0.02 }
  },
  {
    rank: 4,
    name: "Karim's Historic",
    city: "Delhi",
    cuisine: "Mughlai, Kebabs",
    orders: 198000,
    gmv: 59400000,
    rating: 4.5,
    slaPercent: 91.4,
    trend: "+6.2%",
    cohortWeights: { 'Gen Z': 0.14, 'Millennial': 0.32, 'Gen X': 0.36, 'Boomer': 0.18 }
  },
  {
    rank: 5,
    name: "Meghana Foods",
    city: "Bangalore",
    cuisine: "Biryani, Andhra",
    orders: 245000,
    gmv: 73500000,
    rating: 4.8,
    slaPercent: 97.4,
    trend: "+18.9%",
    cohortWeights: { 'Gen Z': 0.38, 'Millennial': 0.48, 'Gen X': 0.11, 'Boomer': 0.03 }
  },
  {
    rank: 6,
    name: "Bademiya Colaba",
    city: "Mumbai",
    cuisine: "Mughlai, Kebabs",
    orders: 112000,
    gmv: 39200000,
    rating: 4.4,
    slaPercent: 92.0,
    trend: "+4.3%",
    cohortWeights: { 'Gen Z': 0.32, 'Millennial': 0.44, 'Gen X': 0.18, 'Boomer': 0.06 }
  },
  {
    rank: 7,
    name: "Gulati Pandara Road",
    city: "Delhi",
    cuisine: "North Indian, Butter Chicken",
    orders: 138000,
    gmv: 55200000,
    rating: 4.7,
    slaPercent: 94.6,
    trend: "+15.1%",
    cohortWeights: { 'Gen Z': 0.12, 'Millennial': 0.32, 'Gen X': 0.40, 'Boomer': 0.16 }
  },
  {
    rank: 8,
    name: "Corner House & Theobroma",
    city: "Bangalore",
    cuisine: "Desserts, Patisserie, Shakes",
    orders: 165000,
    gmv: 29700000,
    rating: 4.9,
    slaPercent: 98.6,
    trend: "+9.8%",
    cohortWeights: { 'Gen Z': 0.62, 'Millennial': 0.28, 'Gen X': 0.08, 'Boomer': 0.02 }
  },
  {
    rank: 9,
    name: "Milano Woodfired Pizzeria",
    city: "Bangalore",
    cuisine: "Pizzas, Artisanal Italian",
    orders: 122000,
    gmv: 54900000,
    rating: 4.8,
    slaPercent: 96.0,
    trend: "+16.3%",
    cohortWeights: { 'Gen Z': 0.38, 'Millennial': 0.44, 'Gen X': 0.14, 'Boomer': 0.04 }
  },
  {
    rank: 10,
    name: "Bliss Chinese Kitchen",
    city: "Kolkata",
    cuisine: "Chinese, Pan-Asian, Dim Sum",
    orders: 78000,
    gmv: 62400000,
    rating: 4.6,
    slaPercent: 95.8,
    trend: "+24.2%",
    cohortWeights: { 'Gen Z': 0.34, 'Millennial': 0.50, 'Gen X': 0.14, 'Boomer': 0.02 }
  },
  {
    rank: 11,
    name: "Subway Healthy Greens",
    city: "Kolkata",
    cuisine: "Healthy Food, Salads, Superfoods",
    orders: 95000,
    gmv: 36100000,
    rating: 4.7,
    slaPercent: 97.0,
    trend: "+18.5%",
    cohortWeights: { 'Gen Z': 0.45, 'Millennial': 0.38, 'Gen X': 0.12, 'Boomer': 0.05 }
  },
];

const INITIAL_HYBRID_STREAM: HybridTelemetryOrder[] = [
  { orderId: "ORD-8A32F1", restaurant: "Truffles Central", city: "Bangalore", source: "Kafka Stream (9092)", cohort: "Gen Z", timeRange: "today", timestamp: "Just now", distanceKm: 3.2, prepScore: 1.2, predictedEtaMins: 22.4, confidence: 0.96, snowflakeLatencyMs: 24, status: "DISPATCHED" },
  { orderId: "ORD-9B41C2", restaurant: "Bastian Bandra", city: "Mumbai", source: "Kafka Stream (9092)", cohort: "Millennial", timeRange: "today", timestamp: "2m ago", distanceKm: 6.8, prepScore: 2.1, predictedEtaMins: 34.8, confidence: 0.92, snowflakeLatencyMs: 38, status: "PREDICTED" },
  { orderId: "ORD-4E87A9", restaurant: "Meghana Foods", city: "Bangalore", source: "Kafka Stream (9092)", cohort: "Gen Z", timeRange: "30d", timestamp: "12m ago", distanceKm: 2.1, prepScore: 1.0, predictedEtaMins: 18.5, confidence: 0.98, snowflakeLatencyMs: 29, status: "DELIVERED" },
  { orderId: "ORD-7D12E4", restaurant: "Karim's Historic", city: "Delhi", source: "Auto Loader (S3)", cohort: "Gen X", timeRange: "30d", timestamp: "28m ago", distanceKm: 5.4, prepScore: 1.8, predictedEtaMins: 31.0, confidence: 0.94, snowflakeLatencyMs: 44, status: "DISPATCHED" },
  { orderId: "ORD-3C99F8", restaurant: "Empire Restaurant", city: "Bangalore", source: "Kafka Stream (9092)", cohort: "Millennial", timeRange: "today", timestamp: "35m ago", distanceKm: 4.0, prepScore: 1.5, predictedEtaMins: 26.2, confidence: 0.95, snowflakeLatencyMs: 31, status: "PREDICTED" },
  { orderId: "ORD-5F22B7", restaurant: "Corner House Ice Cream", city: "Bangalore", source: "Kafka Stream (9092)", cohort: "Gen Z", timeRange: "today", timestamp: "48m ago", distanceKm: 1.8, prepScore: 0.8, predictedEtaMins: 15.2, confidence: 0.99, snowflakeLatencyMs: 20, status: "DELIVERED" },
  { orderId: "ORD-1A88D3", restaurant: "Gulati Pandara Road", city: "Delhi", source: "Auto Loader (S3)", cohort: "Gen X", timeRange: "q3", timestamp: "1h ago", distanceKm: 4.8, prepScore: 1.9, predictedEtaMins: 29.5, confidence: 0.93, snowflakeLatencyMs: 42, status: "DISPATCHED" },
  { orderId: "ORD-6B33C9", restaurant: "Bademiya Colaba", city: "Mumbai", source: "Kafka Stream (9092)", cohort: "Boomer", timeRange: "ytd", timestamp: "2h ago", distanceKm: 3.9, prepScore: 1.6, predictedEtaMins: 27.8, confidence: 0.91, snowflakeLatencyMs: 36, status: "PREDICTED" },
];

export default function PowerBiDashboard() {
  const [filters, setFilters] = useState<FilterState>({
    timeRange: 'all',
    city: 'All',
    generation: 'All',
    cuisine: 'All',
    status: 'All'
  });

  const [activeTab, setActiveTab] = useState<'overview' | 'hybrid' | 'sla' | 'scd2'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Real-time hybrid streaming simulation state
  const currentHorizonConfig = HORIZON_CONFIG[filters.timeRange];
  const [kafkaEventsTotal, setKafkaEventsTotal] = useState(currentHorizonConfig.velocity);
  const [isSimulatingBurst, setIsSimulatingBurst] = useState(false);
  const [hybridOrders, setHybridOrders] = useState<HybridTelemetryOrder[]>(INITIAL_HYBRID_STREAM);

  const triggerKafkaBurstSimulation = () => {
    setIsSimulatingBurst(true);
    let step = 0;
    const interval = setInterval(() => {
      setKafkaEventsTotal(prev => prev + Math.floor(Math.random() * 2500) + 1200);
      step++;
      if (step >= 8) {
        clearInterval(interval);
        setIsSimulatingBurst(false);

        const targetCohort: Exclude<CustomerCohort, 'All'> = 
          filters.generation !== 'All' ? filters.generation : (['Gen Z', 'Millennial', 'Gen X', 'Boomer'] as const)[Math.floor(Math.random() * 4)];
        
        const targetCity = filters.city !== 'All' ? filters.city : (['Bangalore', 'Mumbai', 'Delhi'] as const)[Math.floor(Math.random() * 3)];
        
        const sampleRestaurants = {
          Bangalore: ['Truffles Central', 'Empire Restaurant', 'Meghana Foods', 'Corner House Ice Cream'],
          Mumbai: ['Bastian Bandra', 'Bademiya Colaba'],
          Delhi: ["Karim's Historic", "Gulati Pandara Road"]
        };
        const restList = sampleRestaurants[targetCity as keyof typeof sampleRestaurants] || sampleRestaurants.Bangalore;
        const selectedRest = restList[Math.floor(Math.random() * restList.length)];

        const newOrder: HybridTelemetryOrder = {
          orderId: `ORD-${Math.random().toString(16).substring(2, 8).toUpperCase()}`,
          restaurant: selectedRest,
          city: targetCity,
          source: "Kafka Stream (9092)",
          cohort: targetCohort,
          timeRange: filters.timeRange === 'all' ? 'today' : filters.timeRange,
          timestamp: "Just now",
          distanceKm: parseFloat((Math.random() * 5 + 1.5).toFixed(1)),
          prepScore: 1.3,
          predictedEtaMins: parseFloat((Math.random() * 12 + 17).toFixed(1)),
          confidence: 0.96,
          snowflakeLatencyMs: Math.floor(Math.random() * 15 + currentHorizonConfig.latencyMs - 5),
          status: "PREDICTED"
        };
        setHybridOrders(prev => [newOrder, ...prev.slice(0, 9)]);
      }
    }, 150);
  };

  // Filtered and Rescaled Dataset based on Slicers (City, Cuisine, Customer Cohort, Temporal Horizon)
  const filteredData = useMemo(() => {
    const horizonFactor = currentHorizonConfig.factor;
    const isCohortFiltered = filters.generation !== 'All';
    const activeCohortKey = isCohortFiltered ? (filters.generation as Exclude<CustomerCohort, 'All'>) : null;
    const cohortProfile = activeCohortKey ? COHORT_PROFILES[activeCohortKey] : null;

    return RAW_DATA
      .filter(item => {
        if (filters.city !== 'All' && item.city !== filters.city) return false;
        if (filters.cuisine !== 'All' && !item.cuisine.toLowerCase().includes(filters.cuisine.toLowerCase())) return false;
        if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
      })
      .map(item => {
        let orders = Math.round(item.orders * horizonFactor);
        let gmv = Math.round(item.gmv * horizonFactor);
        let sla = item.slaPercent;

        if (activeCohortKey && cohortProfile) {
          const weight = item.cohortWeights[activeCohortKey] || 0.25;
          // Scale by cohort preference weight vs normal average (0.25)
          orders = Math.round(orders * (weight / 0.25) * (cohortProfile.baseShare / 100));
          gmv = Math.round(orders * (item.gmv / item.orders) * cohortProfile.aovMultiplier);
          if (activeCohortKey === 'Gen Z') sla = Math.min(99.4, Math.max(90.0, sla + 0.8));
          if (activeCohortKey === 'Boomer') sla = Math.max(88.0, sla - 1.2);
        }

        return {
          ...item,
          orders: Math.max(orders, 120),
          gmv: Math.max(gmv, 50000),
          slaPercent: parseFloat(sla.toFixed(1))
        };
      })
      .sort((a, b) => b.gmv - a.gmv)
      .map((item, idx) => ({ ...item, rank: idx + 1 }));
  }, [filters, searchQuery, currentHorizonConfig]);

  // Aggregate Calculations
  const totalGMV = useMemo(() => filteredData.reduce((acc, curr) => acc + curr.gmv, 0), [filteredData]);
  const totalOrders = useMemo(() => filteredData.reduce((acc, curr) => acc + curr.orders, 0), [filteredData]);
  const avgAOV = totalOrders > 0 ? (totalGMV / totalOrders).toFixed(0) : '0';
  const avgSLA = filteredData.length > 0 ? (filteredData.reduce((acc, curr) => acc + curr.slaPercent, 0) / filteredData.length).toFixed(1) : '94.5';
  const avgRating = filteredData.length > 0 ? (filteredData.reduce((acc, curr) => acc + curr.rating, 0) / filteredData.length).toFixed(2) : '4.50';

  // Dynamic Telemetry Orders (filtered by active cohort and time horizon)
  const filteredHybridOrders = useMemo(() => {
    return hybridOrders.filter(ord => {
      if (filters.city !== 'All' && ord.city !== filters.city) return false;
      if (filters.generation !== 'All' && ord.cohort !== filters.generation) return false;
      if (filters.timeRange !== 'all') {
        if (filters.timeRange === 'today' && ord.timeRange !== 'today') return false;
        if (filters.timeRange === '30d' && ord.timeRange !== 'today' && ord.timeRange !== '30d') return false;
      }
      return true;
    });
  }, [hybridOrders, filters]);

  const formatCurrency = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString()}`;
  };

  const handleExportCSV = () => {
    const headers = "Rank,Restaurant,City,Cuisine,Orders,GMV,Rating,SLA_Percent,Cohort,Horizon\n";
    const rows = filteredData.map(d => `${d.rank},"${d.name}","${d.city}","${d.cuisine}",${d.orders},${d.gmv},${d.rating},${d.slaPercent},"${filters.generation}","${filters.timeRange}"`).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `zomato_telemetry_${filters.generation}_${filters.timeRange}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{
      background: 'linear-gradient(180deg, #0d1117 0%, #080b11 100%)',
      borderRadius: '20px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      boxShadow: '0 24px 64px rgba(0, 0, 0, 0.7)',
      padding: '28px',
      color: '#e6edf3',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* PowerBI Top Navigation Ribbon */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        paddingBottom: '20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #F2C811 0%, #DDAA00 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(242, 200, 17, 0.35)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#000">
              <rect x="3" y="12" width="4" height="9" rx="1" />
              <rect x="10" y="7" width="4" height="14" rx="1" />
              <rect x="17" y="3" width="4" height="18" rx="1" />
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, margin: 0, letterSpacing: '-0.5px', color: '#fff' }}>
                Zomato Enterprise Telemetry · Power BI Executive Suite
              </h2>
              <span style={{
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '8px'
              }}>
                ● Snowflake DirectQuery + Databricks Live
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#8b949e', margin: '4px 0 0' }}>
              Hybrid Medallion Architecture: Kafka Event Streaming → Databricks PySpark/MLflow → Snowflake Serving
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setFilters({ timeRange: 'all', city: 'All', generation: 'All', cuisine: 'All', status: 'All' })}
            style={{
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#c9d1d9',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            ↺ Reset Slicers
          </button>
          <button
            onClick={handleExportCSV}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #238636 0%, #1f6feb 100%)',
              border: 'none',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 0 12px rgba(35, 134, 54, 0.4)'
            }}
          >
            <span>📥</span>
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Slicers Ribbon (Interactive Filter Bar) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        padding: '16px 0',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        {/* City Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            📍 Market / City Slicer
          </label>
          <select
            value={filters.city}
            onChange={e => setFilters({ ...filters, city: e.target.value })}
            style={{
              width: '100%',
              marginTop: '6px',
              padding: '8px 12px',
              borderRadius: '8px',
              background: '#161b22',
              color: '#fff',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              fontSize: '13px',
              fontWeight: 600
            }}
          >
            <option value="All">All Cities (Consolidated)</option>
            <option value="Bangalore">Bangalore</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Delhi">Delhi</option>
          </select>
        </div>

        {/* Cuisine Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            🍽️ Cuisine Category
          </label>
          <select
            value={filters.cuisine}
            onChange={e => setFilters({ ...filters, cuisine: e.target.value })}
            style={{
              width: '100%',
              marginTop: '6px',
              padding: '8px 12px',
              borderRadius: '8px',
              background: '#161b22',
              color: '#fff',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              fontSize: '13px',
              fontWeight: 600
            }}
          >
            {DATABASE_CUISINE_OPTIONS.map(c => (
              <option key={c.value} value={c.value}>
                {c.icon} {c.label}
              </option>
            ))}
          </select>
        </div>

        {/* Generation Cohort Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: filters.generation !== 'All' ? '#F2C811' : '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            👥 Customer Cohort {filters.generation !== 'All' && '●'}
          </label>
          <select
            value={filters.generation}
            onChange={e => setFilters({ ...filters, generation: e.target.value as CustomerCohort })}
            style={{
              width: '100%',
              marginTop: '6px',
              padding: '8px 12px',
              borderRadius: '8px',
              background: filters.generation !== 'All' ? 'rgba(242, 200, 17, 0.1)' : '#161b22',
              color: filters.generation !== 'All' ? '#F2C811' : '#fff',
              border: filters.generation !== 'All' ? '1px solid #F2C811' : '1px solid rgba(255, 255, 255, 0.15)',
              fontSize: '13px',
              fontWeight: 600
            }}
          >
            <option value="All">All Generations (Consolidated)</option>
            <option value="Gen Z">⚡ Gen Z (&lt; 25 yrs)</option>
            <option value="Millennial">💼 Millennials (25 - 40 yrs)</option>
            <option value="Gen X">👔 Gen X (40 - 55 yrs)</option>
            <option value="Boomer">🏡 Boomers (55+ yrs)</option>
          </select>
        </div>

        {/* Time Horizon Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: filters.timeRange !== 'all' ? '#38bdf8' : '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            📅 Temporal Horizon {filters.timeRange !== 'all' && '●'}
          </label>
          <select
            value={filters.timeRange}
            onChange={e => setFilters({ ...filters, timeRange: e.target.value as TimeRange })}
            style={{
              width: '100%',
              marginTop: '6px',
              padding: '8px 12px',
              borderRadius: '8px',
              background: filters.timeRange !== 'all' ? 'rgba(56, 189, 248, 0.1)' : '#161b22',
              color: filters.timeRange !== 'all' ? '#38bdf8' : '#fff',
              border: filters.timeRange !== 'all' ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.15)',
              fontSize: '13px',
              fontWeight: 600
            }}
          >
            <option value="all">All Time (Historical Multi-Year)</option>
            <option value="ytd">Year-to-Date (2024 Cumulative)</option>
            <option value="q3">Q3 Rolling Quarter</option>
            <option value="30d">Last 30 Days (Rolling Window)</option>
            <option value="today">Today (Live Kafka Stream)</option>
          </select>
        </div>
      </div>

      {/* Active Filter Scope Notification Strip */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
        padding: '10px 14px',
        margin: '12px 0',
        borderRadius: '10px',
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        fontSize: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ color: '#8b949e', fontWeight: 700 }}>Telemetry Scope:</span>
          <span style={{ background: 'rgba(255, 255, 255, 0.06)', padding: '2px 8px', borderRadius: '6px', color: '#c9d1d9' }}>
            📍 {filters.city}
          </span>
          <span style={{
            background: filters.generation !== 'All' ? 'rgba(242, 200, 17, 0.15)' : 'rgba(255, 255, 255, 0.06)',
            color: filters.generation !== 'All' ? '#F2C811' : '#c9d1d9',
            padding: '2px 8px',
            borderRadius: '6px',
            fontWeight: filters.generation !== 'All' ? 700 : 500
          }}>
            👥 Cohort: {filters.generation === 'All' ? 'All Cohorts' : COHORT_PROFILES[filters.generation as Exclude<CustomerCohort, 'All'>]?.label}
          </span>
          <span style={{
            background: filters.timeRange !== 'all' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.06)',
            color: filters.timeRange !== 'all' ? '#38bdf8' : '#c9d1d9',
            padding: '2px 8px',
            borderRadius: '6px',
            fontWeight: filters.timeRange !== 'all' ? 700 : 500
          }}>
            📅 Window: {currentHorizonConfig.label}
          </span>
        </div>
        <div style={{ color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>● Live Filter Synchronized</span>
          <span style={{ color: '#8b949e' }}>({filteredData.length} entities • {formatCurrency(totalGMV)})</span>
        </div>
      </div>

      {/* Main Mode / Tab Switcher */}
      <div style={{
        display: 'flex',
        gap: '8px',
        margin: '16px 0 10px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        paddingBottom: '12px'
      }}>
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            background: activeTab === 'overview' ? 'rgba(242, 200, 17, 0.15)' : 'transparent',
            border: activeTab === 'overview' ? '1px solid #F2C811' : '1px solid transparent',
            color: activeTab === 'overview' ? '#F2C811' : '#8b949e',
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          📊 Executive Marts Overview
        </button>
        <button
          onClick={() => setActiveTab('hybrid')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            background: activeTab === 'hybrid' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
            border: activeTab === 'hybrid' ? '1px solid #3b82f6' : '1px solid transparent',
            color: activeTab === 'hybrid' ? '#60a5fa' : '#8b949e',
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s'
          }}
        >
          <span>⚡ Hybrid Architecture (Databricks + Snowflake)</span>
          <span style={{ background: '#2563eb', color: '#fff', fontSize: '10px', padding: '2px 6px', borderRadius: '10px' }}>LIVE</span>
        </button>
      </div>

      {/* TAB 1: EXECUTIVE MARTS OVERVIEW */}
      {activeTab === 'overview' && (
        <>
          {/* Top Executive KPI Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
            gap: '16px',
            margin: '20px 0'
          }}>
            {/* Card 1: Gross Merchandise Value */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(242, 200, 17, 0.3)',
              borderRadius: '14px',
              padding: '20px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#F2C811' }} />
              <span style={{ fontSize: '12px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Gross Merchandise Value</span>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
                {formatCurrency(totalGMV)}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px', color: '#10b981', fontWeight: 600 }}>
                <span>▲ {currentHorizonConfig.trendNote}</span>
              </div>
            </div>

            {/* Card 2: Order Volume & AOV */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '14px',
              padding: '20px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#3b82f6' }} />
              <span style={{ fontSize: '12px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Total Order Volume</span>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
                {totalOrders.toLocaleString()}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px', color: '#38bdf8', fontWeight: 600 }}>
                <span>Avg Basket: ₹{avgAOV}</span>
                <span style={{ color: '#8b949e' }}>AOV</span>
              </div>
            </div>

            {/* Card 3: Delivery SLA Compliance */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '14px',
              padding: '20px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#10b981' }} />
              <span style={{ fontSize: '12px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Avg Delivery SLA Speed</span>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
                {avgSLA}%
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px', color: '#10b981', fontWeight: 600 }}>
                <span>🎯 {filters.generation === 'Gen Z' ? '24.2 mins avg' : '28.4 mins avg'}</span>
                <span style={{ color: '#8b949e' }}>Target &lt; 30m</span>
              </div>
            </div>

            {/* Card 4: Customer Rating */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(168, 85, 247, 0.3)',
              borderRadius: '14px',
              padding: '20px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#a855f7' }} />
              <span style={{ fontSize: '12px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Customer Satisfaction</span>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
                {avgRating} <span style={{ fontSize: '20px', color: '#F2C811' }}>★</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px', color: '#c084fc', fontWeight: 600 }}>
                <span>{Math.round(totalOrders * 0.24).toLocaleString()} Reviews</span>
                <span style={{ color: '#8b949e' }}>92% Positive</span>
              </div>
            </div>
          </div>

          {/* Visualization Matrix (2 Columns) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '24px' }}>
            {/* Visual 1: City Market Share */}
            <div style={{
              background: '#161b22',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '14px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#fff' }}>
                  📊 City Market Contribution & SLA Speed ({currentHorizonConfig.badge})
                </h4>
                <span style={{ fontSize: '11px', color: '#8b949e' }}>Snowflake fct_orders</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {(['Bangalore', 'Mumbai', 'Delhi'] as const).map(cityName => {
                  const cityRows = filteredData.filter(d => d.city === cityName);
                  const cityGMV = cityRows.reduce((acc, c) => acc + c.gmv, 0);
                  const cityPercent = totalGMV > 0 ? Math.round((cityGMV / totalGMV) * 100) : 0;
                  const citySla = cityRows.length > 0 ? (cityRows.reduce((acc, c) => acc + c.slaPercent, 0) / cityRows.length).toFixed(1) : '93.5';
                  const cityAvgTime = cityName === 'Bangalore' ? '25.8 mins' : (cityName === 'Mumbai' ? '28.1 mins' : '29.4 mins');

                  return (
                    <div key={cityName}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 600, color: '#fff' }}>📍 {cityName}</span>
                        <span style={{ color: '#8b949e' }}>
                          {formatCurrency(cityGMV)} ({cityPercent}%) • SLA {citySla}% • {cityAvgTime}
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${cityPercent}%`, height: '100%', background: 'linear-gradient(90deg, #F2C811, #10b981)', borderRadius: '4px', transition: 'width 0.4s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Visual 2: Customer Demographic Cohort */}
            <div style={{
              background: '#161b22',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '14px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#fff' }}>
                  👥 Customer Cohort Spend & Behavioral Affinity
                </h4>
                <span style={{ fontSize: '11px', color: '#8b949e' }}>dim_customers SCD2</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                {(Object.entries(COHORT_PROFILES) as [Exclude<CustomerCohort, 'All'>, typeof COHORT_PROFILES[Exclude<CustomerCohort, 'All'>]][]).map(([cKey, c]) => {
                  const isSelected = filters.generation === cKey;
                  const cohortOrders = Math.round(totalOrders * (c.baseShare / 100));
                  const cohortGMV = Math.round(cohortOrders * 320 * c.aovMultiplier);

                  return (
                    <div
                      key={cKey}
                      onClick={() => setFilters({ ...filters, generation: isSelected ? 'All' : cKey })}
                      style={{
                        background: isSelected ? 'rgba(242, 200, 17, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                        padding: '12px',
                        borderRadius: '10px',
                        borderLeft: `4px solid ${c.color}`,
                        border: isSelected ? `1px solid ${c.color}` : '1px solid rgba(255, 255, 255, 0.06)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        boxShadow: isSelected ? `0 0 12px ${c.color}40` : 'none'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>{c.icon} {c.label}</span>
                        {isSelected && (
                          <span style={{ fontSize: '10px', background: c.color, color: '#000', fontWeight: 800, padding: '1px 5px', borderRadius: '4px' }}>
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '17px', fontWeight: 800, color: c.color, margin: '4px 0' }}>
                        {c.baseShare}% Share • {formatCurrency(cohortGMV)}
                      </div>
                      <div style={{ fontSize: '11px', color: '#8b949e' }}>
                        AOV ₹{Math.round(340 * c.aovMultiplier)} • {c.desc}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Restaurant Leaderboard Data Grid */}
          <div style={{
            background: '#161b22',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '14px',
            padding: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 800, margin: 0, color: '#fff' }}>
                  🏆 Restaurant Performance Leaderboard ({currentHorizonConfig.label})
                </h4>
                <p style={{ fontSize: '12px', color: '#8b949e', margin: '2px 0 0' }}>
                  Rankings dynamically weighted for <strong>{filters.generation === 'All' ? 'All Customer Cohorts' : filters.generation}</strong> across {currentHorizonConfig.badge}
                </p>
              </div>

              <input
                type="text"
                placeholder="Search restaurant..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '8px',
                  background: '#0d1117',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#fff',
                  fontSize: '12px',
                  width: '200px'
                }}
              />
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#8b949e', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Rank</th>
                    <th style={{ padding: '10px' }}>Restaurant</th>
                    <th style={{ padding: '10px' }}>City</th>
                    <th style={{ padding: '10px' }}>Cuisine</th>
                    <th style={{ padding: '10px' }}>Orders ({currentHorizonConfig.badge.split(' ')[0]})</th>
                    <th style={{ padding: '10px' }}>GMV Revenue</th>
                    <th style={{ padding: '10px' }}>Rating</th>
                    <th style={{ padding: '10px' }}>SLA %</th>
                    <th style={{ padding: '10px' }}>Top Cohort</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, idx) => {
                    const topCohortEntry = Object.entries(row.cohortWeights).sort((a, b) => b[1] - a[1])[0];
                    const topCohort = topCohortEntry ? topCohortEntry[0] : 'Millennial';
                    const cohortColor = COHORT_PROFILES[topCohort as Exclude<CustomerCohort, 'All'>]?.color || '#3b82f6';

                    return (
                      <tr key={row.name} style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                        transition: 'background 0.2s'
                      }}>
                        <td style={{ padding: '12px 10px', fontWeight: 700, color: idx < 3 ? '#F2C811' : '#8b949e' }}>
                          #{row.rank}
                        </td>
                        <td style={{ padding: '12px 10px', fontWeight: 700, color: '#fff' }}>
                          {row.name}
                        </td>
                        <td style={{ padding: '12px 10px', color: '#c9d1d9' }}>
                          📍 {row.city}
                        </td>
                        <td style={{ padding: '12px 10px', color: '#8b949e', fontSize: '12px' }}>
                          {row.cuisine}
                        </td>
                        <td style={{ padding: '12px 10px', color: '#fff', fontWeight: 600 }}>
                          {row.orders.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px 10px', color: '#10b981', fontWeight: 700 }}>
                          {formatCurrency(row.gmv)}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: 'rgba(242, 200, 17, 0.15)',
                            color: '#F2C811',
                            padding: '2px 6px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            ★ {row.rating}
                          </span>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: row.slaPercent >= 94 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: row.slaPercent >= 94 ? '#10b981' : '#ef4444',
                            padding: '2px 6px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            {row.slaPercent}%
                          </span>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: `${cohortColor}20`,
                            color: cohortColor,
                            border: `1px solid ${cohortColor}40`,
                            padding: '2px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            {topCohort} ({Math.round(topCohortEntry[1] * 100)}%)
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* TAB 2: HYBRID ARCHITECTURE (DATABRICKS + SNOWFLAKE) */}
      {activeTab === 'hybrid' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '10px' }}>
          {/* Architecture Pipeline Flow Banner */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '16px',
            padding: '24px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
              <div>
                <span style={{ background: '#3b82f6', color: '#fff', fontSize: '11px', fontWeight: 800, padding: '3px 8px', borderRadius: '6px', letterSpacing: '0.5px' }}>
                  ENTERPRISE HYBRID FABRIC · {currentHorizonConfig.badge}
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 800, margin: '8px 0 4px', color: '#fff' }}>
                  Live Telemetry: Kafka (9092) → Databricks MLflow ETA → Snowflake DirectQuery
                </h3>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                  Active Filter: <strong>{filters.generation}</strong> cohort in <strong>{filters.city}</strong> market • {currentHorizonConfig.label}
                </p>
              </div>

              {/* Simulation Trigger Button */}
              <button
                onClick={triggerKafkaBurstSimulation}
                disabled={isSimulatingBurst}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '10px',
                  background: isSimulatingBurst ? '#475569' : 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                  border: 'none',
                  color: '#fff',
                  fontWeight: 800,
                  fontSize: '13px',
                  cursor: isSimulatingBurst ? 'not-allowed' : 'pointer',
                  boxShadow: '0 0 20px rgba(245, 158, 11, 0.4)',
                  transition: 'all 0.2s'
                }}
              >
                <span>{isSimulatingBurst ? '⚡ Injecting Burst...' : `🚀 Simulate 50k Kafka Burst (${filters.generation})`}</span>
              </button>
            </div>

            {/* Visual Node Flow */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '12px',
              marginTop: '10px'
            }}>
              {/* Node 1: Kafka Broker */}
              <div style={{ background: 'rgba(0, 0, 0, 0.4)', padding: '14px', borderRadius: '12px', borderLeft: '3px solid #f59e0b' }}>
                <div style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 700 }}>1. KAFKA BROKER</div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff', margin: '4px 0' }}>zomato.order_events</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{kafkaEventsTotal.toLocaleString()} evt/sec • P99 1.1s</div>
              </div>

              {/* Node 2: Databricks Auto Loader */}
              <div style={{ background: 'rgba(0, 0, 0, 0.4)', padding: '14px', borderRadius: '12px', borderLeft: '3px solid #ef4444' }}>
                <div style={{ fontSize: '11px', color: '#ef4444', fontWeight: 700 }}>2. AUTO LOADER (S3)</div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff', margin: '4px 0' }}>cloudFiles + SQS</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Schema: Auto-evolved • Zero-list</div>
              </div>

              {/* Node 3: Databricks MLflow ETA */}
              <div style={{ background: 'rgba(0, 0, 0, 0.4)', padding: '14px', borderRadius: '12px', borderLeft: '3px solid #3b82f6' }}>
                <div style={{ fontSize: '11px', color: '#3b82f6', fontWeight: 700 }}>3. DATABRICKS MLFLOW</div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff', margin: '4px 0' }}>Delivery ETA Regressor</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>RMSE: 1.8 mins • R²: 0.94</div>
              </div>

              {/* Node 4: Snowflake Serving */}
              <div style={{ background: 'rgba(0, 0, 0, 0.4)', padding: '14px', borderRadius: '12px', borderLeft: '3px solid #10b981' }}>
                <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 700 }}>4. SNOWFLAKE SERVING</div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff', margin: '4px 0' }}>DirectQuery Marts</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Query Latency: {currentHorizonConfig.latencyMs}ms P95</div>
              </div>
            </div>
          </div>

          {/* 4 Telemetry Metrics Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
            gap: '16px'
          }}>
            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Kafka Stream Velocity</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#f59e0b', marginTop: '4px' }}>
                {kafkaEventsTotal.toLocaleString()} <span style={{ fontSize: '14px', color: '#94a3b8' }}>msg/s</span>
              </div>
              <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>● 100% Ingestion SLA hit</div>
            </div>

            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Databricks Spark Compute</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#3b82f6', marginTop: '4px' }}>
                {filters.timeRange === 'today' ? '15 sec' : (filters.timeRange === '30d' ? '1.2 min' : '3.4 min')} <span style={{ fontSize: '14px', color: '#94a3b8' }}>micro-batch</span>
              </div>
              <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '4px' }}>Trigger.AvailableNow enabled</div>
            </div>

            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>MLflow ETA Model Confidence</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#a855f7', marginTop: '4px' }}>
                {filters.generation === 'Gen Z' ? '96.8%' : '95.2%'} <span style={{ fontSize: '14px', color: '#94a3b8' }}>score</span>
              </div>
              <div style={{ fontSize: '12px', color: '#c084fc', marginTop: '4px' }}>± 3.5 min error band</div>
            </div>

            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Snowflake Query Latency</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                {currentHorizonConfig.latencyMs} <span style={{ fontSize: '14px', color: '#94a3b8' }}>ms</span>
              </div>
              <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>Zero-copy Iceberg cache</div>
            </div>
          </div>

          {/* Live Ingestion Feed Scored by Databricks ML */}
          <div style={{
            background: '#161b22',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '14px',
            padding: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 800, margin: 0, color: '#fff' }}>
                  ⚡ Live Stream: Kafka Events → Databricks ML Predictions → Snowflake Serving
                </h4>
                <p style={{ fontSize: '12px', color: '#8b949e', margin: '2px 0 0' }}>
                  Streaming telemetry filtered by <strong>{filters.generation}</strong> cohort in <strong>{currentHorizonConfig.label}</strong>
                </p>
              </div>
              <span style={{ fontSize: '11px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', padding: '4px 8px', borderRadius: '6px', fontWeight: 700 }}>
                {filteredHybridOrders.length} Events In Buffer
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#8b949e', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Order ID</th>
                    <th style={{ padding: '10px' }}>Timestamp</th>
                    <th style={{ padding: '10px' }}>Customer Cohort</th>
                    <th style={{ padding: '10px' }}>Restaurant &amp; Market</th>
                    <th style={{ padding: '10px' }}>Ingestion Engine</th>
                    <th style={{ padding: '10px' }}>Haversine Dist</th>
                    <th style={{ padding: '10px' }}>Databricks ML ETA</th>
                    <th style={{ padding: '10px' }}>Confidence</th>
                    <th style={{ padding: '10px' }}>Snowflake Latency</th>
                    <th style={{ padding: '10px' }}>State</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHybridOrders.map((ord, idx) => {
                    const cohortColor = COHORT_PROFILES[ord.cohort]?.color || '#3b82f6';
                    return (
                      <tr key={ord.orderId} style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: idx === 0 ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                        transition: 'background 0.2s'
                      }}>
                        <td style={{ padding: '12px 10px', fontWeight: 700, color: '#fff' }}>
                          <code>{ord.orderId}</code>
                        </td>
                        <td style={{ padding: '12px 10px', color: '#8b949e', fontSize: '11px' }}>
                          {ord.timestamp}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: `${cohortColor}20`,
                            color: cohortColor,
                            border: `1px solid ${cohortColor}50`,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            {COHORT_PROFILES[ord.cohort]?.icon} {ord.cohort}
                          </span>
                        </td>
                        <td style={{ padding: '12px 10px', color: '#fff' }}>
                          <div>{ord.restaurant}</div>
                          <div style={{ fontSize: '11px', color: '#8b949e' }}>📍 {ord.city}</div>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: ord.source.includes('Kafka') ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: ord.source.includes('Kafka') ? '#f59e0b' : '#ef4444',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            {ord.source}
                          </span>
                        </td>
                        <td style={{ padding: '12px 10px', color: '#c9d1d9', fontWeight: 600 }}>
                          {ord.distanceKm} km
                        </td>
                        <td style={{ padding: '12px 10px', color: '#38bdf8', fontWeight: 700 }}>
                          {ord.predictedEtaMins} mins
                        </td>
                        <td style={{ padding: '12px 10px', color: '#10b981', fontWeight: 600 }}>
                          {(ord.confidence * 100).toFixed(0)}%
                        </td>
                        <td style={{ padding: '12px 10px', color: '#94a3b8' }}>
                          <code>{ord.snowflakeLatencyMs} ms</code>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span style={{
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#10b981',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700
                          }}>
                            {ord.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
