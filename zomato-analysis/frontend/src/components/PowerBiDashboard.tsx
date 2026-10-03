import React, { useState, useMemo } from 'react';

interface FilterState {
  timeRange: 'all' | 'ytd' | 'q3' | '30d' | 'today';
  city: string;
  generation: string;
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
}

interface HybridTelemetryOrder {
  orderId: string;
  restaurant: string;
  city: string;
  source: 'Kafka Stream (9092)' | 'Auto Loader (S3)';
  distanceKm: number;
  prepScore: number;
  predictedEtaMins: number;
  actualMins?: number;
  confidence: number;
  snowflakeLatencyMs: number;
  status: 'PREDICTED' | 'DISPATCHED' | 'DELIVERED';
}

const RAW_DATA: RestaurantMetric[] = [
  { rank: 1, name: "Truffles Central", city: "Bangalore", cuisine: "Burgers, Continental", orders: 142800, gmv: 42840000, rating: 4.6, slaPercent: 96.2, trend: "+12.4%" },
  { rank: 2, name: "Empire Restaurant", city: "Bangalore", cuisine: "North Indian, Biryani", orders: 210500, gmv: 61045000, rating: 4.3, slaPercent: 93.8, trend: "+8.7%" },
  { rank: 3, name: "Bastian Bandra", city: "Mumbai", cuisine: "Seafood, Asian", orders: 84200, gmv: 67360000, rating: 4.7, slaPercent: 95.1, trend: "+21.5%" },
  { rank: 4, name: "Karim's Historic", city: "Delhi", cuisine: "Mughlai, Kebabs", orders: 198000, gmv: 59400000, rating: 4.5, slaPercent: 91.4, trend: "+6.2%" },
  { rank: 5, name: "Meghana Foods", city: "Bangalore", cuisine: "Biryani, Andhra", orders: 245000, gmv: 73500000, rating: 4.8, slaPercent: 97.4, trend: "+18.9%" },
  { rank: 6, name: "Bademiya Colaba", city: "Mumbai", cuisine: "Mughlai, Kebabs", orders: 112000, gmv: 39200000, rating: 4.4, slaPercent: 92.0, trend: "+4.3%" },
  { rank: 7, name: "Gulati Pandara Road", city: "Delhi", cuisine: "North Indian, Butter Chicken", orders: 138000, gmv: 55200000, rating: 4.7, slaPercent: 94.6, trend: "+15.1%" },
  { rank: 8, name: "Corner House Ice Cream", city: "Bangalore", cuisine: "Desserts", orders: 165000, gmv: 29700000, rating: 4.9, slaPercent: 98.6, trend: "+9.8%" },
];

const INITIAL_HYBRID_STREAM: HybridTelemetryOrder[] = [
  { orderId: "ORD-8A32F1", restaurant: "Truffles Central", city: "Bangalore", source: "Kafka Stream (9092)", distanceKm: 3.2, prepScore: 1.2, predictedEtaMins: 22.4, confidence: 0.96, snowflakeLatencyMs: 38, status: "DISPATCHED" },
  { orderId: "ORD-9B41C2", restaurant: "Bastian Bandra", city: "Mumbai", source: "Kafka Stream (9092)", distanceKm: 6.8, prepScore: 2.1, predictedEtaMins: 34.8, confidence: 0.92, snowflakeLatencyMs: 42, status: "PREDICTED" },
  { orderId: "ORD-4E87A9", restaurant: "Meghana Foods", city: "Bangalore", source: "Kafka Stream (9092)", distanceKm: 2.1, prepScore: 1.0, predictedEtaMins: 18.5, confidence: 0.98, snowflakeLatencyMs: 29, status: "DELIVERED" },
  { orderId: "ORD-7D12E4", restaurant: "Karim's Historic", city: "Delhi", source: "Auto Loader (S3)", distanceKm: 5.4, prepScore: 1.8, predictedEtaMins: 31.0, confidence: 0.94, snowflakeLatencyMs: 44, status: "DISPATCHED" },
  { orderId: "ORD-3C99F8", restaurant: "Empire Restaurant", city: "Bangalore", source: "Kafka Stream (9092)", distanceKm: 4.0, prepScore: 1.5, predictedEtaMins: 26.2, confidence: 0.95, snowflakeLatencyMs: 35, status: "PREDICTED" },
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
  const [kafkaEventsTotal, setKafkaEventsTotal] = useState(52480);
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
        // Prepend new simulated incoming live order
        const newOrder: HybridTelemetryOrder = {
          orderId: `ORD-${Math.random().toString(16).substring(2, 8).toUpperCase()}`,
          restaurant: "Truffles Central",
          city: "Bangalore",
          source: "Kafka Stream (9092)",
          distanceKm: parseFloat((Math.random() * 6 + 1.5).toFixed(1)),
          prepScore: 1.4,
          predictedEtaMins: parseFloat((Math.random() * 15 + 18).toFixed(1)),
          confidence: 0.95,
          snowflakeLatencyMs: Math.floor(Math.random() * 20 + 28),
          status: "PREDICTED"
        };
        setHybridOrders(prev => [newOrder, ...prev.slice(0, 7)]);
      }
    }, 150);
  };

  // Filtered dataset based on PowerBI Slicers
  const filteredData = useMemo(() => {
    return RAW_DATA.filter(item => {
      if (filters.city !== 'All' && item.city !== filters.city) return false;
      if (filters.cuisine !== 'All' && !item.cuisine.toLowerCase().includes(filters.cuisine.toLowerCase())) return false;
      if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [filters, searchQuery]);

  // Aggregate Calculations
  const totalGMV = useMemo(() => filteredData.reduce((acc, curr) => acc + curr.gmv, 0), [filteredData]);
  const totalOrders = useMemo(() => filteredData.reduce((acc, curr) => acc + curr.orders, 0), [filteredData]);
  const avgAOV = totalOrders > 0 ? (totalGMV / totalOrders).toFixed(0) : '0';
  const avgSLA = filteredData.length > 0 ? (filteredData.reduce((acc, curr) => acc + curr.slaPercent, 0) / filteredData.length).toFixed(1) : '94.5';
  const avgRating = filteredData.length > 0 ? (filteredData.reduce((acc, curr) => acc + curr.rating, 0) / filteredData.length).toFixed(2) : '4.50';

  const formatCurrency = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString()}`;
  };

  const handleExportCSV = () => {
    const headers = "Rank,Restaurant,City,Cuisine,Orders,GMV,Rating,SLA_Percent,Trend\n";
    const rows = filteredData.map(d => `${d.rank},"${d.name}","${d.city}","${d.cuisine}",${d.orders},${d.gmv},${d.rating},${d.slaPercent},"${d.trend}"`).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `zomato_powerbi_telemetry_${Date.now()}.csv`);
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
            <option value="All">All Cuisines</option>
            <option value="Biryani">Biryani & Andhra</option>
            <option value="Burgers">Burgers & Continental</option>
            <option value="Seafood">Seafood & Coastal</option>
            <option value="Mughlai">Mughlai & Kebabs</option>
            <option value="Desserts">Desserts & Shakes</option>
          </select>
        </div>

        {/* Generation Cohort Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            👥 Customer Cohort
          </label>
          <select
            value={filters.generation}
            onChange={e => setFilters({ ...filters, generation: e.target.value })}
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
            <option value="All">All Generations</option>
            <option value="Gen Z">Gen Z (&lt; 25 yrs)</option>
            <option value="Millennial">Millennials (25 - 40 yrs)</option>
            <option value="Gen X">Gen X (40 - 55 yrs)</option>
            <option value="Boomer">Boomers (55+ yrs)</option>
          </select>
        </div>

        {/* Time Horizon Slicer */}
        <div>
          <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700, letterSpacing: '0.5px' }}>
            📅 Temporal Horizon
          </label>
          <select
            value={filters.timeRange}
            onChange={e => setFilters({ ...filters, timeRange: e.target.value as any })}
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
            <option value="all">All Time (Historical)</option>
            <option value="ytd">Year-to-Date (2024)</option>
            <option value="q3">Q3 Rolling Quarter</option>
            <option value="30d">Last 30 Days</option>
            <option value="today">Today (Live Stream)</option>
          </select>
        </div>
      </div>

      {/* Main Mode / Tab Switcher */}
      <div style={{
        display: 'flex',
        gap: '8px',
        margin: '20px 0 10px',
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
                <span>▲ +16.8% YoY</span>
                <span style={{ color: '#8b949e' }}>vs budget benchmark</span>
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
                <span>🎯 28.4 mins avg</span>
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
                <span>320K+ Reviews</span>
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
                  📊 City Market Contribution & SLA Speed
                </h4>
                <span style={{ fontSize: '11px', color: '#8b949e' }}>Snowflake fct_orders</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  { city: "Bangalore", gmvPercent: 44, amount: "₹207.2 Cr", avgTime: "26.2 mins", sla: "95.4%" },
                  { city: "Mumbai", gmvPercent: 32, amount: "₹150.7 Cr", avgTime: "28.5 mins", sla: "93.8%" },
                  { city: "Delhi", gmvPercent: 24, amount: "₹113.1 Cr", avgTime: "29.8 mins", sla: "92.1%" },
                ].map(item => (
                  <div key={item.city}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, color: '#fff' }}>{item.city}</span>
                      <span style={{ color: '#8b949e' }}>{item.amount} ({item.gmvPercent}%) • SLA {item.sla}</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${item.gmvPercent}%`, height: '100%', background: 'linear-gradient(90deg, #F2C811, #10b981)', borderRadius: '4px' }} />
                    </div>
                  </div>
                ))}
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
                  👥 Generation Cohort Lifetime Spend & AOV
                </h4>
                <span style={{ fontSize: '11px', color: '#8b949e' }}>dim_customers SCD2</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                {[
                  { cohort: "Millennials (25-40)", share: "42%", aov: "₹385", color: "#3b82f6", desc: "Highest family/weekend orders" },
                  { cohort: "Gen Z (< 25)", share: "34%", aov: "₹260", color: "#10b981", desc: "Late-night burgers & fast food" },
                  { cohort: "Gen X (40-55)", share: "18%", aov: "₹460", color: "#F2C811", desc: "High-value fine dining" },
                  { cohort: "Boomers (55+)", share: "6%", aov: "₹410", color: "#a855f7", desc: "Traditional cuisines & health" },
                ].map(c => (
                  <div key={c.cohort} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '10px', borderLeft: `3px solid ${c.color}` }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>{c.cohort}</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: c.color, margin: '4px 0' }}>{c.share} Share</div>
                    <div style={{ fontSize: '11px', color: '#8b949e' }}>AOV: {c.aov} • {c.desc}</div>
                  </div>
                ))}
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
                  🏆 Restaurant Performance Leaderboard (Snowflake Marts)
                </h4>
                <p style={{ fontSize: '12px', color: '#8b949e', margin: '2px 0 0' }}>
                  Consolidated from <code>obt_orders</code> and <code>snap_restaurants</code> SCD Type 2
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
                    <th style={{ padding: '10px' }}>Orders</th>
                    <th style={{ padding: '10px' }}>GMV Revenue</th>
                    <th style={{ padding: '10px' }}>Rating</th>
                    <th style={{ padding: '10px' }}>SLA %</th>
                    <th style={{ padding: '10px' }}>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, idx) => (
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
                      <td style={{ padding: '12px 10px', color: '#10b981', fontWeight: 600 }}>
                        {row.trend}
                      </td>
                    </tr>
                  ))}
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
                  ENTERPRISE HYBRID FABRIC
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 800, margin: '8px 0 4px', color: '#fff' }}>
                  Live Hybrid Telemetry: Kafka Event Streaming → Databricks AI → Snowflake Serving
                </h3>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                  High-throughput ingestion &amp; distributed ML in Databricks, zero-copy Iceberg sync to Snowflake for sub-50ms analytics.
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
                <span>{isSimulatingBurst ? '⚡ Injecting Burst...' : '🚀 Simulate 50k Kafka Burst'}</span>
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
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Query Latency: 38ms P95</div>
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
                3.4 <span style={{ fontSize: '14px', color: '#94a3b8' }}>min micro-batch</span>
              </div>
              <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '4px' }}>Trigger.AvailableNow enabled</div>
            </div>

            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>MLflow ETA Model Confidence</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#a855f7', marginTop: '4px' }}>
                95.2% <span style={{ fontSize: '14px', color: '#94a3b8' }}>score</span>
              </div>
              <div style={{ fontSize: '12px', color: '#c084fc', marginTop: '4px' }}>± 3.5 min error band</div>
            </div>

            <div style={{ background: '#161b22', padding: '18px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>Snowflake Query Latency</span>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                38 <span style={{ fontSize: '14px', color: '#94a3b8' }}>ms</span>
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
                  Real-time feature extraction (Haversine distance, prep score) + MLflow ETA inference scored in &lt; 50ms
                </p>
              </div>
              <span style={{ fontSize: '11px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', padding: '4px 8px', borderRadius: '6px', fontWeight: 700 }}>
                Auto-refreshing
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#8b949e', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Order ID</th>
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
                  {hybridOrders.map((ord, idx) => (
                    <tr key={ord.orderId} style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      background: idx === 0 ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                      transition: 'background 0.2s'
                    }}>
                      <td style={{ padding: '12px 10px', fontWeight: 700, color: '#fff' }}>
                        <code>{ord.orderId}</code>
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
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
