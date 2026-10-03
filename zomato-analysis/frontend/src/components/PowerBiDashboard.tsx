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

export default function PowerBiDashboard() {
  const [filters, setFilters] = useState<FilterState>({
    timeRange: 'all',
    city: 'All',
    generation: 'All',
    cuisine: 'All',
    status: 'All'
  });

  const [activeTab, setActiveTab] = useState<'overview' | 'sla' | 'scd2' | 'data'>('overview');
  const [searchQuery, setSearchQuery] = useState('');

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
          {/* PowerBI Official Yellow/Gold Bar Icon */}
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
                ● Snowflake DirectQuery Live
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#8b949e', margin: '4px 0 0' }}>
              Directly querying Snowflake Gold Marts (<code>fct_orders</code>, <code>dim_restaurants</code>, <code>obt_orders</code>) • 35,240,000 Total Lakehouse Records
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
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)'
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
            <option value="All">All Demographics</option>
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

      {/* PowerBI Top Executive KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
        gap: '16px',
        margin: '24px 0'
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
          <span style={{ fontSize: '12px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>SLA Delivery Compliance</span>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
            {avgSLA}%
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px', color: '#10b981', fontWeight: 600 }}>
            <span>Target &lt; 30 mins</span>
            <span style={{ color: '#8b949e' }}>(Avg 27.4m)</span>
          </div>
        </div>

        {/* Card 4: Customer Satisfaction CSAT */}
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

      {/* PowerBI Visualization Matrix (2 Columns) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Visual 1: City Market Share & SLA Breakdown */}
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

        {/* Visual 2: Customer Demographic Cohort Spend */}
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

      {/* Visual 3: Top Restaurant Leaderboard Data Grid */}
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

        {/* Data Grid Table */}
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
    </div>
  );
}
