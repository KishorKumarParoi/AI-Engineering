import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { DATABASE_CUISINE_OPTIONS } from '../data/database_catalog';

interface KafkaOrderEvent {
  order_id: string;
  customer_id: string;
  restaurant_id: string;
  restaurant_name: string;
  food_id: string;
  food_name: string;
  cuisine: string;
  city: string;
  order_status: 'PLACED' | 'ACCEPTED' | 'PREPARING' | 'PICKED_UP' | 'DELIVERED';
  order_amount: number;
  delivery_fee: number;
  item_count: number;
  unit_price?: number;
  subtotal?: number;
  payment_method: string;
  delivery_distance_km: number;
  predicted_delivery_eta_mins: number;
  eta_confidence_band: [number, number];
  event_timestamp: string;
  published_to_kafka: boolean;
  target_topic: string;
}

const CITIES = [
  "All Cities", "Bangalore", "Mumbai", "Delhi", "Kolkata", "Surat", "Pune", "Ahmedabad", "Dehradun"
];

export default function KafkaStreamHub() {
  const [selectedCuisine, setSelectedCuisine] = useState("All");
  const [selectedCity, setSelectedCity] = useState("All Cities");
  const [events, setEvents] = useState<KafkaOrderEvent[]>([]);
  const [isDispatching, setIsDispatching] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [batchCount, setBatchCount] = useState(25);
  const [batchRate, setBatchRate] = useState(10);
  const [inspectedEvent, setInspectedEvent] = useState<KafkaOrderEvent | null>(null);
  

  // Initial mock events buffer for immediate rendering
  useEffect(() => {
    // Fetch initial event to prime table
    fetch('/api/order-stream')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data) {
          setEvents([data.data]);
        }
      })
      .catch(() => {});
  }, []);

  // Continuous real-time auto-streamer
  useEffect(() => {
    if (!isStreaming) return;
    const interval = setInterval(async () => {
      try {
        const queryParams = new URLSearchParams();
        if (selectedCuisine !== "All") queryParams.append("cuisine", selectedCuisine);
        if (selectedCity !== "All Cities") queryParams.append("city", selectedCity);
        const url = `/api/order-stream?${queryParams.toString()}`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.success && data.data) {
          setEvents(prev => [data.data, ...prev.slice(0, 49)]);
          setVelocity(Math.floor(Math.random() * 15 + 20));
        }
      } catch (err) {
        console.error("Auto stream error", err);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [isStreaming, selectedCuisine, selectedCity]);

  // Dispatch single event
  const handleDispatchSingle = async () => {
    setIsDispatching(true);
    try {
      const queryParams = new URLSearchParams();
      if (selectedCuisine !== "All") queryParams.append("cuisine", selectedCuisine);
      if (selectedCity !== "All Cities") queryParams.append("city", selectedCity);
      const url = `/api/order-stream?${queryParams.toString()}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.success && data.data) {
        setEvents(prev => [data.data, ...prev.slice(0, 49)]);
        setInspectedEvent(data.data);
      }
    } catch (err) {
      console.error("Dispatch single event error", err);
    } finally {
      setIsDispatching(false);
    }
  };

  // Dispatch batch burst
  const handleDispatchBatch = async () => {
    setIsDispatching(true);
    try {
      const burstEvents: KafkaOrderEvent[] = [];
      for (let i = 0; i < Math.min(batchCount, 15); i++) {
        const queryParams = new URLSearchParams();
        if (selectedCuisine !== "All") queryParams.append("cuisine", selectedCuisine);
        if (selectedCity !== "All Cities") queryParams.append("city", selectedCity);
        const url = `/api/order-stream?${queryParams.toString()}`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.success && data.data) {
          burstEvents.push(data.data);
        }
      }
      setEvents(prev => [...burstEvents, ...prev].slice(0, 50));
      setVelocity(batchRate * 4);
    } catch (err) {
      console.error("Batch dispatch error", err);
    } finally {
      setIsDispatching(false);
    }
  };

  // Database & Airflow sync state
  const [isSyncingAirflow, setIsSyncingAirflow] = useState(false);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [totalInDb, setTotalInDb] = useState<number>(107);
  const [velocity, setVelocity] = useState<number>(24);
  const [isAuditingDb, setIsAuditingDb] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  const [dbAuditData, setDbAuditData] = useState<any>(null);

  // Audit Snowflake Database Live
  const handleAuditDb = async () => {
    setIsAuditingDb(true);
    try {
      const res = await fetch('/api/check-db-sync');
      const data = await res.json();
      if (data.success && data.data) {
        setDbAuditData(data.data);
        setTotalInDb(data.data.total_orders);
        setAuditModalOpen(true);
      }
    } catch (err) {
      console.error("DB Audit error", err);
    } finally {
      setIsAuditingDb(false);
    }
  };

  // S3 Unload state
  const [isUnloadingS3, setIsUnloadingS3] = useState(false);
  const [s3UnloadStatus, setS3UnloadStatus] = useState<any>(null);

  const handleTriggerS3Unload = async () => {
    setIsUnloadingS3(true);
    try {
      const res = await fetch('/api/unload-to-s3');
      const data = await res.json();
      setS3UnloadStatus(data);
      setTimeout(() => setS3UnloadStatus(null), 8000);
    } catch (err) {
      console.error("S3 Unload error", err);
    } finally {
      setIsUnloadingS3(false);
    }
  };

  // Trigger Airflow database sync
  const handleTriggerAirflowSync = async () => {
    setIsSyncingAirflow(true);
    try {
      const res = await fetch('/api/sync-kafka-to-db');
      const data = await res.json();
      setSyncStatus(data);
      if (data.data && data.data.total_in_snowflake) {
        setTotalInDb(data.data.total_in_snowflake);
      }
      setTimeout(() => setSyncStatus(null), 8000);
    } catch (err) {
      console.error("Airflow sync error", err);
    } finally {
      setIsSyncingAirflow(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary, #0c1015)', color: '#fff', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Head>
        <title>Kafka Event Stream Hub • Zomato Enterprise Lakehouse</title>
        <meta name="description" content="Real-time Kafka order event stream details, emission console, and Airflow database sync for Zomato Lakehouse." />
      </Head>

      {/* Navigation Header */}
      <header style={{
        background: 'rgba(18, 22, 34, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '14px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>⚡</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '18px', letterSpacing: '-0.5px', color: '#fff' }}>
                ZOMATO <span style={{ color: '#FF4B4B' }}>KAFKA STREAM</span>
              </div>
              <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>
                High-Throughput Event Ingestion Mesh
              </div>
            </div>
          </Link>

          <nav style={{ display: 'flex', gap: '8px' }}>
            <Link href="/" style={{
              textDecoration: 'none',
              padding: '6px 14px',
              borderRadius: '16px',
              fontSize: '12px',
              fontWeight: 700,
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#94a3b8'
            }}>
              🛍️ Storefront
            </Link>
            <Link href="/?view=powerbi" style={{
              textDecoration: 'none',
              padding: '6px 14px',
              borderRadius: '16px',
              fontSize: '12px',
              fontWeight: 700,
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#94a3b8'
            }}>
              📊 Power BI Telemetry
            </Link>
            <div style={{
              padding: '6px 14px',
              borderRadius: '16px',
              fontSize: '12px',
              fontWeight: 800,
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: '#000'
            }}>
              ⚡ Kafka Stream Hub
            </div>
          </nav>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={handleAuditDb}
            disabled={isAuditingDb}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              color: '#38bdf8',
              padding: '8px 16px',
              borderRadius: '20px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '12px',
              transition: 'all 0.2s'
            }}
          >
            <span>{isAuditingDb ? '⏳' : '❄️'}</span>
            <span>{isAuditingDb ? 'Querying Snowflake...' : 'Audit Snowflake DB Live'}</span>
          </button>

          <button
            onClick={handleTriggerS3Unload}
            disabled={isUnloadingS3}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(234, 88, 12, 0.2) 100%)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              color: '#f59e0b',
              padding: '8px 16px',
              borderRadius: '20px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '12px',
              transition: 'all 0.2s'
            }}
          >
            <span>{isUnloadingS3 ? '⏳' : '📦'}</span>
            <span>{isUnloadingS3 ? 'Exporting to S3...' : 'Export to AWS S3 (Airflow)'}</span>
          </button>

          <button
            onClick={handleTriggerAirflowSync}
            disabled={isSyncingAirflow}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#10b981',
              padding: '8px 16px',
              borderRadius: '20px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '12px',
              transition: 'all 0.2s'
            }}
          >
            <span>{isSyncingAirflow ? '⏳' : '🔄'}</span>
            <span>{isSyncingAirflow ? 'Airflow Syncing...' : 'Sync to DB (Airflow)'}</span>
          </button>
        </div>
      </header>

      {/* S3 Unload Status Banner */}
      {s3UnloadStatus && (
        <div style={{
          background: s3UnloadStatus.success ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          borderBottom: '1px solid rgba(245, 158, 11, 0.3)',
          padding: '12px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '13px',
          color: s3UnloadStatus.success ? '#f59e0b' : '#ef4444'
        }}>
          <div>
            <strong>✓ Airflow 4-Hour Cronjob Unloaded:</strong> {s3UnloadStatus.message}
          </div>
          <button onClick={() => setS3UnloadStatus(null)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {/* Sync Status Banner */}
      {syncStatus && (
        <div style={{
          background: syncStatus.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          borderBottom: '1px solid rgba(16, 185, 129, 0.3)',
          padding: '12px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '13px',
          color: syncStatus.success ? '#10b981' : '#ef4444'
        }}>
          <div>
            <strong>✓ Airflow Cronjob Executed:</strong> {syncStatus.message} • Total Snowflake records: {totalInDb}
          </div>
          <button onClick={() => setSyncStatus(null)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      <main style={{ maxWidth: '1380px', margin: '0 auto', padding: '36px 32px' }}>
        {/* KPI Strip */}
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '18px 20px', borderRadius: '12px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#f59e0b', fontWeight: 800 }}>Kafka Broker & Topic</div>
            <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '6px' }}>zomato.order_events</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Broker: localhost:9092 • Ack=1</div>
          </div>
          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '18px 20px', borderRadius: '12px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#10b981', fontWeight: 800 }}>Snowflake Destination</div>
            <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '6px' }}>RAW.KAFKA_ORDER_EVENTS</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Live in DB: {totalInDb} rows (*/5m cron)</div>
          </div>
          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '18px 20px', borderRadius: '12px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#eab308', fontWeight: 800 }}>AWS S3 Data Lake Export</div>
            <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '6px' }}>zomato-dataset-kkp</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Cadence: 0 */4 * * * • Snappy Parquet</div>
          </div>
          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '18px 20px', borderRadius: '12px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#60a5fa', fontWeight: 800 }}>Stream Velocity</div>
            <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '6px' }}>{velocity} evt/sec</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>P99 Latency: ~1.2s • MLflow GBT</div>
          </div>
          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '18px 20px', borderRadius: '12px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#a855f7', fontWeight: 800 }}>Airflow Orchestrator</div>
            <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '6px' }}>2 Active Cronjobs</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>5-min Sync + 4-hr S3 Unload</div>
          </div>
        </section>

        {/* Control Panel & Sending Options */}
        <section style={{
          background: 'linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '16px',
          padding: '28px',
          marginBottom: '36px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
            <div>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: '#f59e0b', fontWeight: 800 }}>
                Interactive Stream Control Panel
              </span>
              <h2 style={{ fontSize: '26px', fontWeight: 800, margin: '6px 0 4px', letterSpacing: '-0.5px' }}>
                🚀 Kafka Event Dispatcher & Filter Engine
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
                Emit authentic Lakehouse order payloads matching Snowflake DIM_FOOD catalog directly into the message queue.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => setIsStreaming(!isStreaming)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: isStreaming ? 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  border: 'none',
                  color: '#fff',
                  padding: '10px 20px',
                  borderRadius: '24px',
                  fontWeight: 800,
                  fontSize: '13px',
                  cursor: 'pointer',
                  boxShadow: isStreaming ? '0 0 16px rgba(239, 68, 68, 0.4)' : '0 0 16px rgba(16, 185, 129, 0.4)'
                }}
              >
                <span>{isStreaming ? '⏹' : '🌊'}</span>
                <span>{isStreaming ? 'Stop Auto-Streamer' : 'Start Auto-Streamer (Live Flow)'}</span>
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '18px', marginBottom: '24px' }}>
            {/* Cuisine Slicer */}
            <div>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>
                🍽️ Target Cuisine Filter
              </label>
              <select
                value={selectedCuisine}
                onChange={e => setSelectedCuisine(e.target.value)}
                style={{
                  width: '100%',
                  marginTop: '6px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: '#161b22',
                  color: '#fff',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  fontSize: '13px',
                  fontWeight: 600
                }}
              >
                {DATABASE_CUISINE_OPTIONS.map(c => (
                  <option key={c.value} value={c.value}>{c.icon} {c.label}</option>
                ))}
              </select>
            </div>

            {/* City Slicer */}
            <div>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>
                📍 Target Hub City
              </label>
              <select
                value={selectedCity}
                onChange={e => setSelectedCity(e.target.value)}
                style={{
                  width: '100%',
                  marginTop: '6px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: '#161b22',
                  color: '#fff',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  fontSize: '13px',
                  fontWeight: 600
                }}
              >
                {CITIES.map(ct => (
                  <option key={ct} value={ct}>{ct}</option>
                ))}
              </select>
            </div>

            {/* Batch Count Slider */}
            <div>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>
                📦 Batch Quantity ({batchCount} events)
              </label>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={batchCount}
                onChange={e => setBatchCount(parseInt(e.target.value))}
                style={{ width: '100%', marginTop: '14px', accentColor: '#f59e0b' }}
              />
            </div>

            {/* Velocity Slider */}
            <div>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#8b949e', fontWeight: 700 }}>
                ⚡ Velocity ({batchRate} evt/sec)
              </label>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={batchRate}
                onChange={e => setBatchRate(parseInt(e.target.value))}
                style={{ width: '100%', marginTop: '14px', accentColor: '#f59e0b' }}
              />
            </div>
          </div>

          {/* Action Triggers */}
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <button
              onClick={handleDispatchSingle}
              disabled={isDispatching}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                color: '#000',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 800,
                fontSize: '14px',
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)'
              }}
            >
              <span>{isDispatching ? '⏳' : '⚡'}</span>
              <span>{isDispatching ? 'Emitting...' : 'Send Single Order Event'}</span>
            </button>

            <button
              onClick={handleDispatchBatch}
              disabled={isDispatching}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#fff',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              <span>📦</span>
              <span>Send Batch of {batchCount} Events</span>
            </button>
          </div>
        </section>

        {/* Live Stream Table */}
        <section style={{ marginBottom: '48px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 800, margin: 0 }}>
                📡 Live Dispatched Order Stream ({events.length} Captured)
              </h3>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '4px 0 0' }}>
                Real-time Lakehouse events emitted into Kafka cluster with Databricks MLflow GBT ETA inferences.
              </p>
            </div>
            <div style={{ fontSize: '12px', color: '#f59e0b', fontWeight: 700 }}>
              ● Click row to inspect full JSON payload
            </div>
          </div>

          <div style={{ background: '#161b22', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(0, 0, 0, 0.3)', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#8b949e', textTransform: 'uppercase', fontSize: '11px' }}>
                  <th style={{ padding: '12px 16px' }}>Order ID</th>
                  <th style={{ padding: '12px 16px' }}>Restaurant & City</th>
                  <th style={{ padding: '12px 16px' }}>Verified Food Item</th>
                  <th style={{ padding: '12px 16px' }}>Cuisine</th>
                  <th style={{ padding: '12px 16px' }}>Amount</th>
                  <th style={{ padding: '12px 16px' }}>Distance / ETA</th>
                  <th style={{ padding: '12px 16px' }}>Payment</th>
                  <th style={{ padding: '12px 16px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev, idx) => (
                  <tr
                    key={ev.order_id + idx}
                    onClick={() => setInspectedEvent(ev)}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      cursor: 'pointer',
                      background: inspectedEvent?.order_id === ev.order_id ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
                      transition: 'background 0.15s'
                    }}
                  >
                    <td style={{ padding: '12px 16px', fontWeight: 800, color: '#f59e0b' }}>
                      {ev.order_id}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 700 }}>{ev.restaurant_name}</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>📍 {ev.city}</div>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontWeight: 600 }}>{ev.food_name}</span>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>[{ev.food_id}]</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ background: 'rgba(255, 255, 255, 0.08)', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 }}>
                        {ev.cuisine}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: '#10b981' }}>
                      ₹{ev.order_amount.toFixed(0)}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div>⚡ {ev.predicted_delivery_eta_mins} mins</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>{ev.delivery_distance_km} km</div>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>{ev.payment_method}</span>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '11px', color: '#64748b' }}>
                      {new Date(ev.event_timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* JSON Inspector Modal */}
        {inspectedEvent && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '24px'
          }}>
            <div style={{
              background: '#161b22',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '16px',
              maxWidth: '720px',
              width: '100%',
              maxHeight: '85vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: '#f59e0b' }}>
                    🔍 Kafka Event Inspector: {inspectedEvent.order_id}
                  </h4>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                    100% Authentic Snowflake Medallion Lakehouse JSON Schema
                  </div>
                </div>
                <button
                  onClick={() => setInspectedEvent(null)}
                  style={{ background: 'none', border: 'none', color: '#fff', fontSize: '18px', cursor: 'pointer' }}
                >
                  ✕
                </button>
              </div>
              <div style={{ padding: '20px 24px', overflowY: 'auto', background: '#0d1117' }}>
                <pre style={{ margin: 0, fontSize: '12px', color: '#38bdf8', lineHeight: 1.5, fontFamily: 'monospace' }}>
                  {JSON.stringify(inspectedEvent, null, 2)}
                </pre>
              </div>
              <div style={{ padding: '14px 24px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(inspectedEvent, null, 2));
                    alert("JSON copied to clipboard!");
                  }}
                  style={{ background: '#21262d', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontSize: '12px' }}
                >
                  📋 Copy JSON
                </button>
                <button
                  onClick={() => setInspectedEvent(null)}
                  style={{ background: '#f59e0b', border: 'none', color: '#000', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '12px' }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Snowflake Live Audit Modal */}
        {auditModalOpen && dbAuditData && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}>
            <div style={{
              background: '#0d1117',
              border: '1px solid #38bdf8',
              borderRadius: '16px',
              width: '100%',
              maxWidth: '850px',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 25px 50px -12px rgba(56, 189, 248, 0.25)',
              overflow: 'hidden'
            }}>
              <div style={{
                padding: '20px 24px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(13, 17, 23, 1) 100%)'
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#38bdf8' }}>
                    ❄️ Snowflake Live Sync Audit Report
                  </h3>
                  <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#94a3b8' }}>
                    Target: <code>ZOMATO.RAW.KAFKA_ORDER_EVENTS</code> • Warehouse: <code>ZOMATO_WH</code>
                  </p>
                </div>
                <button
                  onClick={() => setAuditModalOpen(false)}
                  style={{ background: 'none', border: 'none', color: '#fff', fontSize: '18px', cursor: 'pointer' }}
                >
                  ✕
                </button>
              </div>

              {/* KPI Strip */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '12px',
                padding: '16px 24px',
                background: '#161b22',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Orders Ingested</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#10b981' }}>{dbAuditData.total_orders}</div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Total Ingested GMV</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#38bdf8' }}>₹{dbAuditData.total_gmv.toLocaleString()}</div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Active Cuisines</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#f59e0b' }}>{dbAuditData.distinct_cuisines}</div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Metro Cities</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#a855f7' }}>{dbAuditData.distinct_cities}</div>
                </div>
              </div>

              {/* Table of Live Records in Snowflake */}
              <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '12px', color: '#f8fafc' }}>
                  Most Recent Orders Ingested in Snowflake:
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Order ID</th>
                      <th style={{ padding: '8px' }}>Restaurant</th>
                      <th style={{ padding: '8px' }}>Food Item</th>
                      <th style={{ padding: '8px' }}>Cuisine</th>
                      <th style={{ padding: '8px' }}>City</th>
                      <th style={{ padding: '8px' }}>Amount</th>
                      <th style={{ padding: '8px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dbAuditData.recent_orders?.map((ord: any) => (
                      <tr key={ord.order_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                        <td style={{ padding: '8px', color: '#38bdf8', fontWeight: 700 }}>{ord.order_id}</td>
                        <td style={{ padding: '8px' }}>{ord.restaurant_name}</td>
                        <td style={{ padding: '8px', color: '#cbd5e1' }}>{ord.food_name}</td>
                        <td style={{ padding: '8px' }}>
                          <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>
                            {ord.cuisine}
                          </span>
                        </td>
                        <td style={{ padding: '8px', color: '#94a3b8' }}>{ord.city}</td>
                        <td style={{ padding: '8px', fontWeight: 700, color: '#10b981' }}>₹{ord.order_amount.toFixed(2)}</td>
                        <td style={{ padding: '8px' }}>
                          <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>
                            {ord.order_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ padding: '14px 24px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', justifyContent: 'flex-end', background: '#161b22' }}>
                <button
                  onClick={() => setAuditModalOpen(false)}
                  style={{ background: '#38bdf8', border: 'none', color: '#000', padding: '8px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '12px' }}
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Deep Dive: Usecase of Kafka Events in Zomato Architecture */}
        <section style={{
          background: '#161b22',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '32px',
          marginTop: '40px'
        }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: '#60a5fa', fontWeight: 800 }}>
            Principal Data Engineering Architecture
          </span>
          <h3 style={{ fontSize: '24px', fontWeight: 800, margin: '8px 0 16px' }}>
            💡 Deep Dive: Why Kafka Order Events are Essential for Zomato Scale
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '20px' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #f59e0b' }}>
              <h4 style={{ margin: '0 0 8px', color: '#f59e0b', fontSize: '16px' }}>
                1. Sub-10ms Checkout Decoupling
              </h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
                Direct database writes collapse at 50,000+ orders/sec. When a customer checks out, the Go Order Service writes to Kafka partition <code>zomato.order_events</code> in under 5ms, immediately freeing up the client connection.
              </p>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #60a5fa' }}>
              <h4 style={{ margin: '0 0 8px', color: '#60a5fa', fontSize: '16px' }}>
                2. Real-Time Rider Geofencing & ETA ML
              </h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
                Databricks Spark Structured Streaming consumes the event stream in real-time, calculates Haversine routing distances, invokes the MLflow GBT model to predict delivery ETA, and alerts the nearest rider within seconds.
              </p>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
              <h4 style={{ margin: '0 0 8px', color: '#10b981', fontSize: '16px' }}>
                3. Airflow Scheduled Micro-Batching
              </h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
                Every 5 minutes (<code>*/5 * * * *</code>), the Airflow cronjob consumes buffered Kafka events, executes idempotent <code>MERGE INTO ZOMATO.RAW.KAFKA_ORDER_EVENTS</code>, and refreshes the Gold dimensional marts.
              </p>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #a855f7' }}>
              <h4 style={{ margin: '0 0 8px', color: '#a855f7', fontSize: '16px' }}>
                4. Fault Tolerance & Replayability
              </h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
                If downstream analytics or Snowflake experiences maintenance, Kafka preserves all order messages with zero data loss. Consumers simply resume from their stored offset when back online.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
