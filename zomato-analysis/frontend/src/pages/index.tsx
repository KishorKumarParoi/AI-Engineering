import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import PowerBiDashboard from '../components/PowerBiDashboard';

import { 
  MenuItem, 
  Restaurant, 
  FeaturedDishItem, 
  DATABASE_CUISINE_OPTIONS,
  AUTHENTIC_DATABASE_RESTAURANTS, 
  AUTHENTIC_DATABASE_FEATURED_DISHES 
} from '../data/database_catalog';

interface CartItem extends MenuItem {
  quantity: number;
}

interface Order {
  id: string;
  customer_id: string;
  restaurant_id: string;
  restaurant_name: string;
  city: string;
  items: { name: string; quantity: number; price: number }[];
  subtotal: number;
  delivery_fee: number;
  tax: number;
  discount: number;
  total_amount: number;
  status: string;
  estimated_delivery_mins: number;
  created_at: string;
}

const DEFAULT_RESTAURANTS: Restaurant[] = AUTHENTIC_DATABASE_RESTAURANTS;
const FEATURED_SIGNATURE_DISHES: FeaturedDishItem[] = AUTHENTIC_DATABASE_FEATURED_DISHES;

export default function Home() {
  const [selectedCity, setSelectedCity] = useState("All");
  const [selectedCuisine, setSelectedCuisine] = useState("All");
  const [restaurants, setRestaurants] = useState<Restaurant[]>(DEFAULT_RESTAURANTS);
  const [activeRestaurant, setActiveRestaurant] = useState<Restaurant | null>(null);
  const [cart, setCart] = useState<{ [id: string]: CartItem }>({});
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [aiTab, setAiTab] = useState<'sql' | 'rag'>('sql');
  const [activeOrder, setActiveOrder] = useState<Order | null>(null);
  const [isTrackingOpen, setIsTrackingOpen] = useState(false);
  const [promoCode, setPromoCode] = useState("");
  const [discount, setDiscount] = useState(0);
  const [deliveryAddr, setDeliveryAddr] = useState("Indiranagar 100ft Road, Bangalore");
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [viewMode, setViewMode] = useState<'storefront' | 'powerbi'>('storefront');
  
  // Status check for microservices & Streamlit AI apps
  const [catalogHealthy, setCatalogHealthy] = useState(false);
  const [orderHealthy, setOrderHealthy] = useState(false);
  const [streamlitSqlHealthy, setStreamlitSqlHealthy] = useState(false);
  const [streamlitRagHealthy, setStreamlitRagHealthy] = useState(false);
  const [embeddedApp, setEmbeddedApp] = useState<'none' | 'sql' | 'rag'>('none');
  const [isDispatchingEvent, setIsDispatchingEvent] = useState(false);
  const [lastDispatchedEvent, setLastDispatchedEvent] = useState<any>(null);

  const handleDispatchLiveEvent = async () => {
    setIsDispatchingEvent(true);
    try {
      const url = selectedCuisine !== 'All' 
        ? `/api/order-stream?cuisine=${encodeURIComponent(selectedCuisine)}` 
        : `/api/order-stream`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        setLastDispatchedEvent(data.data);
        setTimeout(() => setLastDispatchedEvent(null), 8000);
      }
    } catch (e) {
      console.error('Failed to dispatch live event', e);
    } finally {
      setIsDispatchingEvent(false);
    }
  };

  // Poll Microservices and Streamlit Apps Health
  useEffect(() => {
    fetch('http://localhost:8082/healthz')
      .then(res => setCatalogHealthy(res.ok))
      .catch(() => setCatalogHealthy(false));

    fetch('http://localhost:8081/healthz')
      .then(res => setOrderHealthy(res.ok))
      .catch(() => setOrderHealthy(false));

    // Streamlit app health checks
    fetch('http://localhost:8501/_stcore/health', { mode: 'no-cors' })
      .then(() => setStreamlitSqlHealthy(true))
      .catch(() => setStreamlitSqlHealthy(false));

    fetch('http://localhost:8502/_stcore/health', { mode: 'no-cors' })
      .then(() => setStreamlitRagHealthy(true))
      .catch(() => setStreamlitRagHealthy(false));
  }, []);

  // Fetch from Catalog Service if available with reliable fallback filtering
  useEffect(() => {
    let url = 'http://localhost:8082/api/v1/restaurants';
    const params = new URLSearchParams();
    if (selectedCity !== 'All') params.append('city', selectedCity);
    if (selectedCuisine !== 'All') params.append('cuisine', selectedCuisine);
    if (params.toString()) url += `?${params.toString()}`;

    const applyFilters = (list: Restaurant[]) => {
      let filtered = list;
      if (selectedCity !== 'All') {
        filtered = filtered.filter(r => r.city === selectedCity);
      }
      if (selectedCuisine !== 'All') {
        const query = selectedCuisine.toLowerCase();
        filtered = filtered.filter(r => 
          r.cuisine.toLowerCase().includes(query) ||
          (r.menu && r.menu.some(m => 
            m.category.toLowerCase().includes(query) ||
            m.name.toLowerCase().includes(query)
          ))
        );
      }
      return filtered;
    };

    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setRestaurants(applyFilters(data));
        } else {
          setRestaurants(applyFilters(DEFAULT_RESTAURANTS));
        }
      })
      .catch(() => setRestaurants(applyFilters(DEFAULT_RESTAURANTS)));
  }, [selectedCity, selectedCuisine]);

  // Cart Calculations
  const cartItems = Object.values(cart);
  const cartSubtotal = cartItems.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  const deliveryFee = cartItems.length > 0 ? 40 : 0;
  const tax = cartSubtotal * 0.05;
  const grandTotal = Math.max(0, (cartSubtotal + deliveryFee + tax) - discount);

  const addToCart = (item: MenuItem, restaurant: Restaurant) => {
    setCart(prev => {
      const existing = prev[item.id];
      const qty = existing ? existing.quantity + 1 : 1;
      return {
        ...prev,
        [item.id]: { ...item, quantity: qty }
      };
    });
  };

  const removeFromCart = (itemId: string) => {
    setCart(prev => {
      const existing = prev[itemId];
      if (!existing) return prev;
      if (existing.quantity <= 1) {
        const copy = { ...prev };
        delete copy[itemId];
        return copy;
      }
      return {
        ...prev,
        [itemId]: { ...existing, quantity: existing.quantity - 1 }
      };
    });
  };

  const applyPromo = () => {
    if (promoCode.trim().toUpperCase() === "ZOMATO50") {
      setDiscount(50);
    } else {
      alert("Invalid promo code. Try 'ZOMATO50'");
    }
  };

  // Place Order through Go Microservice with Idempotency Key
  const placeOrder = async () => {
    if (cartItems.length === 0) return;
    setIsPlacingOrder(true);

    const idempotencyKey = `idemp_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const payload = {
      customer_id: "cust_kkp_007",
      restaurant_id: activeRestaurant ? activeRestaurant.id : "rest_bangalore_01",
      restaurant_name: activeRestaurant ? activeRestaurant.name : "Zomato Partner",
      city: selectedCity === "All" ? "Bangalore" : selectedCity,
      delivery_address: deliveryAddr,
      items: cartItems.map(item => ({
        food_id: item.food_id,
        name: item.name,
        quantity: item.quantity,
        price: item.price
      })),
      discount: discount,
      payment_method: "UPI"
    };

    try {
      const res = await fetch('http://localhost:8081/api/v1/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Order creation failed');
      const orderData: Order = await res.json();
      setActiveOrder(orderData);
      setIsCheckoutOpen(false);
      setCart({});
      setIsTrackingOpen(true);
    } catch {
      // Offline fallback mock order
      const mockOrder: Order = {
        id: `ord_${Date.now().toString(36)}`,
        customer_id: "cust_kkp_007",
        restaurant_id: activeRestaurant?.id || "rest_01",
        restaurant_name: activeRestaurant?.name || "Empire Restaurant",
        city: selectedCity === "All" ? "Bangalore" : selectedCity,
        items: cartItems.map(i => ({ name: i.name, quantity: i.quantity, price: i.price })),
        subtotal: cartSubtotal,
        delivery_fee: deliveryFee,
        tax: tax,
        discount: discount,
        total_amount: grandTotal,
        status: "PENDING",
        estimated_delivery_mins: 32,
        created_at: new Date().toISOString()
      };
      setActiveOrder(mockOrder);
      setIsCheckoutOpen(false);
      setCart({});
      setIsTrackingOpen(true);
    } finally {
      setIsPlacingOrder(false);
    }
  };

  // Poll Order Status for Live Tracking Timeline
  useEffect(() => {
    if (!activeOrder || !isTrackingOpen) return;

    const interval = setInterval(() => {
      fetch(`http://localhost:8081/api/v1/orders/${activeOrder.id}`)
        .then(res => res.json())
        .then((updated: Order) => {
          if (updated && updated.status) {
            setActiveOrder(updated);
          }
        })
        .catch(() => {
          // Progress status locally for testing demonstration if order service is stopped
          const orderStates = ["PENDING", "PAYMENT_AUTHORIZED", "CONFIRMED", "KITCHEN_ACCEPTED", "RIDER_ASSIGNED", "OUT_FOR_DELIVERY", "DELIVERED"];
          const currIdx = orderStates.indexOf(activeOrder.status);
          if (currIdx < orderStates.length - 1) {
            setActiveOrder(prev => prev ? { ...prev, status: orderStates[currIdx + 1] } : null);
          }
        });
    }, 2500);

    return () => clearInterval(interval);
  }, [activeOrder, isTrackingOpen]);

  const ORDER_STEPS = [
    { key: "PENDING", label: "Order Placed", desc: "Sent to Saga Orchestrator" },
    { key: "PAYMENT_AUTHORIZED", label: "Payment Authorized", desc: "Escrow verified" },
    { key: "CONFIRMED", label: "Order Confirmed", desc: "Inventory locked" },
    { key: "KITCHEN_ACCEPTED", label: "Kitchen Preparing", desc: "Chef preparing your meal" },
    { key: "RIDER_ASSIGNED", label: "Rider Assigned", desc: "Courier en route to restaurant" },
    { key: "OUT_FOR_DELIVERY", label: "Out for Delivery", desc: "Rider arriving shortly" },
    { key: "DELIVERED", label: "Delivered", desc: "Enjoy your food!" }
  ];

  const currentStepIndex = activeOrder ? ORDER_STEPS.findIndex(s => s.key === activeOrder.status) : 0;

  return (
    <>
      <Head>
        <title>Zomato AI - Enterprise Food Delivery & Intelligent Lakehouse</title>
        <meta name="description" content="Hyper-scale food delivery platform powered by Go microservices, Kafka event streaming, Snowflake medallion lakehouse, and agentic AI." />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Navigation Bar */}
        <header style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          background: 'rgba(10, 13, 20, 0.85)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '16px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }} onClick={() => setActiveRestaurant(null)}>
              <span style={{ fontSize: '26px' }}>⚡</span>
              <span style={{ fontSize: '24px', fontWeight: 800, background: 'var(--primary-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                zomato<span style={{ color: 'var(--accent-gold)' }}>.ai</span>
              </span>
            </div>

            {/* City Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '24px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '14px' }}>📍</span>
              <select 
                value={selectedCity} 
                onChange={e => setSelectedCity(e.target.value)}
                style={{ background: 'transparent', color: '#fff', border: 'none', outline: 'none', cursor: 'pointer', fontWeight: 600 }}
              >
                <option value="All" style={{ background: '#101522' }}>All Cities</option>
                <option value="Bangalore" style={{ background: '#101522' }}>Bangalore</option>
                <option value="Mumbai" style={{ background: '#101522' }}>Mumbai</option>
                <option value="Delhi" style={{ background: '#101522' }}>Delhi</option>
              </select>
            </div>

            {/* Architecture Health Indicators */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', background: 'rgba(255,255,255,0.04)', padding: '4px 10px', borderRadius: '12px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: catalogHealthy ? 'var(--accent-emerald)' : '#e23744' }}></span>
                <span>Catalog Svc :8082</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', background: 'rgba(255,255,255,0.04)', padding: '4px 10px', borderRadius: '12px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: orderHealthy ? 'var(--accent-emerald)' : '#e23744' }}></span>
                <span>Order Svc :8081</span>
              </div>
            </div>

            {/* Streamlit AI Applications Quick Launch */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '12px' }}>
              <a 
                href="http://localhost:8501" 
                target="_blank" 
                rel="noopener noreferrer"
                title="Launch Streamlit Text-to-SQL Analytics Assistant on port 8501"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  color: '#10b981',
                  padding: '5px 12px',
                  borderRadius: '16px',
                  textDecoration: 'none',
                  fontWeight: 700,
                  transition: 'all 0.2s ease'
                }}
              >
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: streamlitSqlHealthy ? '#10b981' : '#f59e0b', boxShadow: streamlitSqlHealthy ? '0 0 8px #10b981' : 'none' }}></span>
                <span>📊 Streamlit SQL (:8501) ↗</span>
              </a>

              <a 
                href="http://localhost:8502" 
                target="_blank" 
                rel="noopener noreferrer"
                title="Launch Streamlit Customer Reviews RAG Chat on port 8502"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.35)',
                  color: '#60a5fa',
                  padding: '5px 12px',
                  borderRadius: '16px',
                  textDecoration: 'none',
                  fontWeight: 700,
                  transition: 'all 0.2s ease'
                }}
              >
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: streamlitRagHealthy ? '#3b82f6' : '#f59e0b', boxShadow: streamlitRagHealthy ? '0 0 8px #3b82f6' : 'none' }}></span>
                <span>💬 Streamlit RAG (:8502) ↗</span>
              </a>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* View Mode Switcher: Storefront vs Power BI Telemetry */}
            <div style={{
              display: 'flex',
              background: 'rgba(255, 255, 255, 0.06)',
              padding: '3px',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.12)'
            }}>
              <button
                onClick={() => setViewMode('storefront')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: 'none',
                  background: viewMode === 'storefront' ? 'var(--primary-gradient)' : 'transparent',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <span>🛍️</span>
                <span>Storefront</span>
              </button>

              <button
                onClick={() => setViewMode('powerbi')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: 'none',
                  background: viewMode === 'powerbi' ? 'linear-gradient(135deg, #F2C811 0%, #DDAA00 100%)' : 'transparent',
                  color: viewMode === 'powerbi' ? '#000' : '#fff',
                  fontSize: '12px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: viewMode === 'powerbi' ? '0 0 12px rgba(242, 200, 17, 0.4)' : 'none'
                }}
              >
                <span>📊</span>
                <span>Power BI Telemetry</span>
              </button>

              <Link
                href="/kafka-stream"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: 'none',
                  background: 'transparent',
                  color: '#f59e0b',
                  fontSize: '12px',
                  fontWeight: 800,
                  textDecoration: 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <span>⚡</span>
                <span>Kafka Stream Hub ↗</span>
              </Link>
            </div>

            {/* Dispatch Event Option */}
            <button 
              id="dispatch-event-btn"
              onClick={handleDispatchLiveEvent}
              disabled={isDispatchingEvent}
              title="Stream a live order event into Kafka topic [zomato.order_events]"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(239, 68, 68, 0.2) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                color: '#f59e0b',
                padding: '8px 18px',
                borderRadius: '24px',
                cursor: 'pointer',
                fontWeight: 700,
                fontSize: '13px',
                transition: 'all 0.2s ease',
                boxShadow: isDispatchingEvent ? '0 0 16px rgba(245, 158, 11, 0.5)' : 'none'
              }}
            >
              <span>{isDispatchingEvent ? '⏳' : '⚡'}</span>
              <span>{isDispatchingEvent ? 'Dispatching...' : 'Dispatch Event (Kafka)'}</span>
            </button>

            {/* AI Assistant Button */}
            <button 
              id="ai-assistant-btn"
              onClick={() => setIsAIOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                color: '#fff',
                padding: '8px 18px',
                borderRadius: '24px',
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 0.2s ease'
              }}
            >
              <span>✨</span>
              <span>Ask AI Assistant</span>
            </button>

            {/* Cart Button */}
            <button 
              id="cart-btn"
              onClick={() => setIsCheckoutOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                background: cartItems.length > 0 ? 'var(--primary-gradient)' : 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                color: '#fff',
                padding: '8px 20px',
                borderRadius: '24px',
                cursor: 'pointer',
                fontWeight: 700,
                boxShadow: cartItems.length > 0 ? '0 0 20px var(--primary-glow)' : 'none'
              }}
            >
              <span>🛒</span>
              <span>Cart ({cartItems.reduce((a, b) => a + b.quantity, 0)})</span>
              {cartItems.length > 0 && <span>₹{grandTotal.toFixed(0)}</span>}
            </button>
          </div>
        </header>

        {/* Live Dispatched Event Banner */}
        {lastDispatchedEvent && (
          <div style={{
            background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%)',
            borderBottom: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '10px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: '#10b981',
            fontWeight: 600
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '16px' }}>⚡</span>
              <span>
                <strong>Kafka Order Event Published:</strong> <code>{lastDispatchedEvent.order_id}</code> • {lastDispatchedEvent.food_name} at {lastDispatchedEvent.restaurant_name} ({lastDispatchedEvent.city}) → <code>[zomato.order_events]</code>
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span style={{ color: 'var(--accent-gold)' }}>₹{lastDispatchedEvent.order_amount}</span>
              <span style={{ color: '#94a3b8' }}>ETA: {lastDispatchedEvent.predicted_delivery_eta_mins} mins</span>
              <button onClick={() => setLastDispatchedEvent(null)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '14px' }}>✕</button>
            </div>
          </div>
        )}

        {viewMode === 'storefront' ? (
          /* Hero Section & Storefront */
          <section style={{ padding: '48px 32px 24px', maxWidth: '1280px', margin: '0 auto', width: '100%' }}>
          <div style={{ textAlign: 'center', marginBottom: '36px' }}>
            <span style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--accent-gold)', fontWeight: 700 }}>
              Enterprise Microservices Mesh & Snowflake Lakehouse
            </span>
            <h1 style={{ fontSize: '44px', fontWeight: 800, marginTop: '8px', letterSpacing: '-1px' }}>
              Hyper-Scale Food Delivery & Intelligent Logistics
            </h1>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '640px', margin: '12px auto 0', fontSize: '16px' }}>
              Sub-10ms transactional checkout powered by Go, Kafka event sourcing, and autonomous LangGraph self-critique agents.
            </p>
          </div>

          {/* Cuisine Filter Pills */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '32px' }}>
            {DATABASE_CUISINE_OPTIONS.map(cat => (
              <button
                key={cat.value}
                onClick={() => setSelectedCuisine(cat.value)}
                style={{
                  background: selectedCuisine === cat.value ? 'var(--primary-gradient)' : 'var(--bg-secondary)',
                  border: selectedCuisine === cat.value ? '1px solid #FF4B4B' : '1px solid var(--border-subtle)',
                  color: '#fff',
                  padding: '8px 18px',
                  borderRadius: '20px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: selectedCuisine === cat.value ? '0 0 16px rgba(255, 75, 75, 0.35)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
              </button>
            ))}
          </div>

          {/* Streamlit AI & Analytics Suite Hub */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(20, 24, 38, 0.9) 0%, rgba(13, 17, 28, 0.95) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            padding: '24px 28px',
            marginBottom: '36px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(255, 43, 43, 0.15)', border: '1px solid rgba(255, 43, 43, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="#FF4B4B">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#fff', margin: 0 }}>
                    Streamlit AI & Analytics Suite
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
                    Interactive Snowflake Gold Marts exploration & Semantic Review RAG assistants
                  </p>
                </div>
              </div>

              {embeddedApp !== 'none' && (
                <button
                  onClick={() => setEmbeddedApp('none')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  ✕ Close Embedded View
                </button>
              )}
            </div>

            {/* App Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              {/* App 1: Text-to-SQL */}
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '14px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>📊</span>
                    <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#fff' }}>Warehouse Text-to-SQL</h4>
                  </div>
                  <span style={{
                    fontSize: '11px',
                    padding: '3px 8px',
                    borderRadius: '10px',
                    background: streamlitSqlHealthy ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: streamlitSqlHealthy ? '#10b981' : '#f59e0b',
                    fontWeight: 700
                  }}>
                    {streamlitSqlHealthy ? '● Port :8501 Live' : '○ Standby (:8501)'}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                  Query 35M+ rows of Snowflake Gold Marts (<code>fct_orders</code>, <code>dim_restaurants</code>, SLA metrics) using natural language with AST guardrails.
                </p>
                <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', paddingTop: '8px' }}>
                  <a
                    href="http://localhost:8501"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      flex: 1,
                      textAlign: 'center',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: '#10b981',
                      fontSize: '12px',
                      fontWeight: 700,
                      textDecoration: 'none'
                    }}
                  >
                    Open in Tab ↗
                  </a>
                  <button
                    onClick={() => setEmbeddedApp(embeddedApp === 'sql' ? 'none' : 'sql')}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: embeddedApp === 'sql' ? 'var(--primary-gradient)' : 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    {embeddedApp === 'sql' ? 'Hide Frame ▲' : 'Embed Here ▼'}
                  </button>
                </div>
              </div>

              {/* App 2: RAG Chat */}
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '14px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>🍔</span>
                    <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#fff' }}>Customer Feedback RAG</h4>
                  </div>
                  <span style={{
                    fontSize: '11px',
                    padding: '3px 8px',
                    borderRadius: '10px',
                    background: streamlitRagHealthy ? 'rgba(59, 130, 246, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: streamlitRagHealthy ? '#60a5fa' : '#f59e0b',
                    fontWeight: 700
                  }}>
                    {streamlitRagHealthy ? '● Port :8502 Live' : '○ Standby (:8502)'}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                  Semantic vector search across 300,000 customer reviews powered by <code>text-embedding-3-small</code> and LangGraph cyclic reasoning loops.
                </p>
                <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', paddingTop: '8px' }}>
                  <a
                    href="http://localhost:8502"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      flex: 1,
                      textAlign: 'center',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      color: '#60a5fa',
                      fontSize: '12px',
                      fontWeight: 700,
                      textDecoration: 'none'
                    }}
                  >
                    Open in Tab ↗
                  </a>
                  <button
                    onClick={() => setEmbeddedApp(embeddedApp === 'rag' ? 'none' : 'rag')}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: embeddedApp === 'rag' ? 'var(--primary-gradient)' : 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    {embeddedApp === 'rag' ? 'Hide Frame ▲' : 'Embed Here ▼'}
                  </button>
                </div>
              </div>
            </div>

            {/* Embedded Iframe Container */}
            {embeddedApp !== 'none' && (
              <div style={{ marginTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-emerald)' }}></span>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>
                      {embeddedApp === 'sql' ? 'Live Streamlit Text-to-SQL (http://localhost:8501)' : 'Live Streamlit Reviews RAG (http://localhost:8502)'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <a
                      href={embeddedApp === 'sql' ? 'http://localhost:8501' : 'http://localhost:8502'}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: '12px', color: 'var(--accent-gold)', textDecoration: 'none', fontWeight: 600 }}
                    >
                      Open Full Screen ↗
                    </a>
                  </div>
                </div>
                <iframe
                  src={embeddedApp === 'sql' ? 'http://localhost:8501' : 'http://localhost:8502'}
                  style={{
                    width: '100%',
                    height: '620px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    background: '#0e1117'
                  }}
                  title="Streamlit Interactive Application"
                />
              </div>
            )}
          </div>

          {/* Featured Signature Dishes Showcase */}
          {(() => {
            const visibleDishes = FEATURED_SIGNATURE_DISHES.filter(d => {
              if (selectedCity !== "All" && d.city !== selectedCity) return false;
              if (selectedCuisine !== "All" && !d.category.toLowerCase().includes(selectedCuisine.toLowerCase())) return false;
              return true;
            });

            if (visibleDishes.length === 0) return null;

            return (
              <div style={{ marginBottom: '42px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '11px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '3px 8px', borderRadius: '6px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        ❄️ Snowflake Lakehouse Catalog (DIM_FOOD)
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>● 371,561 Authentic Enlisted Items</span>
                    </div>
                    <h3 style={{ fontSize: '24px', fontWeight: 800, color: '#fff', margin: '8px 0 4px' }}>
                      🔥 Verified Bestsellers: Burgers, Biryani, Seafood & Mughlai
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                      Enlisted catalog dishes directly verified against Zomato Snowflake Data Lakehouse in {selectedCity === 'All' ? 'India' : selectedCity}
                    </p>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--accent-gold)', fontWeight: 600 }}>
                    Showing {visibleDishes.length} verified items
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                  {visibleDishes.map(dishItem => {
                    const cartItem = cart[dishItem.id];
                    const dummyRest: Restaurant = {
                      id: dishItem.restaurant_id,
                      name: dishItem.restaurant_name,
                      city: dishItem.city,
                      cuisine: dishItem.category,
                      rating: 4.8,
                      rating_count: 5000,
                      cost_for_two: 800,
                      address: `${dishItem.city} Prime Kitchen`,
                      image_url: dishItem.image_url
                    };
                    const menuItem: MenuItem = {
                      id: dishItem.id,
                      food_id: dishItem.food_id,
                      name: dishItem.name,
                      category: dishItem.category,
                      price: dishItem.price,
                      is_veg: dishItem.is_veg,
                      description: dishItem.description
                    };

                    return (
                      <div
                        key={dishItem.id}
                        className="glass-panel"
                        style={{
                          overflow: 'hidden',
                          display: 'flex',
                          flexDirection: 'column',
                          borderRadius: '16px',
                          border: '1px solid rgba(255, 255, 255, 0.08)',
                          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.03) 0%, rgba(13, 17, 28, 0.95) 100%)',
                          transition: 'transform 0.2s, box-shadow 0.2s'
                        }}
                      >
                        <div style={{ position: 'relative', height: '160px', width: '100%', overflow: 'hidden' }}>
                          <img
                            src={dishItem.image_url}
                            alt={dishItem.name}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          />
                          <div style={{ position: 'absolute', top: '10px', left: '10px', background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)', padding: '3px 8px', borderRadius: '8px', fontSize: '11px', fontWeight: 700, color: '#fff' }}>
                            {dishItem.category_icon} {dishItem.category}
                          </div>
                          <div style={{ position: 'absolute', top: '10px', right: '10px', background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)', padding: '3px 8px', borderRadius: '8px', fontSize: '11px', fontWeight: 800, color: '#fff', boxShadow: '0 0 10px rgba(245, 158, 11, 0.4)' }}>
                            {dishItem.badge}
                          </div>
                        </div>

                        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', flex: 1, gap: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '10px', border: `1px solid ${dishItem.is_veg ? 'var(--accent-emerald)' : '#e23744'}`, padding: '1px 5px', borderRadius: '4px', color: dishItem.is_veg ? 'var(--accent-emerald)' : '#e23744', fontWeight: 700 }}>
                              {dishItem.is_veg ? '● VEG' : '▲ NON-VEG'}
                            </span>
                            <span style={{ fontSize: '10px', fontFamily: 'monospace', color: '#93c5fd', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                              {dishItem.food_id}
                            </span>
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>📍 {dishItem.restaurant_name}</span>
                          </div>

                          <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', margin: 0, lineHeight: 1.3 }}>
                            {dishItem.name}
                          </h4>

                          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, flex: 1, lineHeight: 1.4 }}>
                            {dishItem.description}
                          </p>

                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                            <span style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-gold)' }}>
                              ₹{dishItem.price}
                            </span>

                            {cartItem ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--primary-gradient)', padding: '5px 12px', borderRadius: '20px' }}>
                                <button onClick={() => removeFromCart(menuItem.id)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 800, fontSize: '14px' }}>-</button>
                                <span style={{ fontWeight: 700, fontSize: '13px' }}>{cartItem.quantity}</span>
                                <button onClick={() => addToCart(menuItem, dummyRest)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 800, fontSize: '14px' }}>+</button>
                              </div>
                            ) : (
                              <button
                                onClick={() => addToCart(menuItem, dummyRest)}
                                style={{
                                  background: 'linear-gradient(135deg, #e23744 0%, #b31d28 100%)',
                                  border: 'none',
                                  color: '#fff',
                                  padding: '6px 16px',
                                  borderRadius: '20px',
                                  cursor: 'pointer',
                                  fontWeight: 700,
                                  fontSize: '12px',
                                  boxShadow: '0 0 10px rgba(226, 55, 68, 0.35)',
                                  transition: 'all 0.2s'
                                }}
                              >
                                + ADD
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* Curated Restaurant Partners Section */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <h3 style={{ fontSize: '22px', fontWeight: 800, color: '#fff', margin: 0 }}>
                🏆 Curated Restaurant Kitchens ({restaurants.length} Partners)
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
                Select a kitchen to explore its full live menu and chef selections
              </p>
            </div>
            <span style={{ fontSize: '12px', color: 'var(--accent-emerald)', fontWeight: 600 }}>
              ● 100% Hygiene Verified
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: '24px' }}>
            {restaurants.map(rst => (
              <div 
                key={rst.id}
                className="glass-panel"
                onClick={() => setActiveRestaurant(rst)}
                style={{ cursor: 'pointer', overflow: 'hidden' }}
              >
                <div style={{ position: 'relative', height: '170px', width: '100%', overflow: 'hidden' }}>
                  <img 
                    src={rst.image_url} 
                    alt={rst.name} 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  />
                  <div style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', padding: '4px 10px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: 700 }}>
                    <span style={{ color: 'var(--accent-gold)' }}>★</span>
                    <span>{rst.rating}</span>
                  </div>
                  <div style={{ position: 'absolute', bottom: '12px', left: '12px', background: 'rgba(16, 185, 129, 0.9)', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
                    ⚡ 30-35 mins
                  </div>
                </div>

                <div style={{ padding: '18px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>{rst.name}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '10px' }}>{rst.cuisine}</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>📍 {rst.city}</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>₹{rst.cost_for_two} for two</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
        ) : (
          /* Power BI Executive Telemetry Suite */
          <main style={{ padding: '36px 32px', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
            <PowerBiDashboard />
          </main>
        )}

        {/* Restaurant Menu Modal */}
        {activeRestaurant && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
            <div className="glass-panel" style={{ width: '100%', maxWidth: '780px', maxHeight: '90vh', overflowY: 'auto', padding: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '26px', fontWeight: 800 }}>{activeRestaurant.name}</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>{activeRestaurant.cuisine} • {activeRestaurant.address}</p>
                </div>
                <button 
                  onClick={() => setActiveRestaurant(null)}
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer', fontSize: '16px' }}
                >
                  ✕
                </button>
              </div>

              <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-gold)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Recommended Dishes
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {(activeRestaurant.menu || []).map(item => {
                  const inCart = cart[item.id];
                  return (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '12px', border: `1px solid ${item.is_veg ? 'var(--accent-emerald)' : '#e23744'}`, padding: '2px 4px', borderRadius: '4px', color: item.is_veg ? 'var(--accent-emerald)' : '#e23744' }}>
                            {item.is_veg ? '● VEG' : '▲ NON-VEG'}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: '16px' }}>{item.name}</span>
                        </div>
                        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '6px' }}>{item.description}</p>
                        <span style={{ display: 'inline-block', marginTop: '6px', fontWeight: 700, fontSize: '15px', color: 'var(--accent-gold)' }}>₹{item.price}</span>
                      </div>

                      <div>
                        {inCart ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--primary-gradient)', padding: '6px 14px', borderRadius: '20px' }}>
                            <button onClick={() => removeFromCart(item.id)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 800 }}>-</button>
                            <span style={{ fontWeight: 700 }}>{inCart.quantity}</span>
                            <button onClick={() => addToCart(item, activeRestaurant)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 800 }}>+</button>
                          </div>
                        ) : (
                          <button
                            onClick={() => addToCart(item, activeRestaurant)}
                            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '8px 18px', borderRadius: '20px', cursor: 'pointer', fontWeight: 600 }}
                          >
                            + ADD
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Checkout Drawer */}
        {isCheckoutOpen && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)', display: 'flex', justifyContent: 'flex-end' }}>
            <div className="slide-drawer" style={{ width: '100%', maxWidth: '440px', background: 'var(--bg-secondary)', height: '100%', padding: '32px 24px', display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 800 }}>Order Checkout</h3>
                <button onClick={() => setIsCheckoutOpen(false)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '18px' }}>✕</button>
              </div>

              {cartItems.length === 0 ? (
                <div style={{ textAlign: 'center', margin: 'auto 0', color: 'var(--text-muted)' }}>
                  <span style={{ fontSize: '48px' }}>🛒</span>
                  <p style={{ marginTop: '12px', fontWeight: 600 }}>Your cart is empty</p>
                </div>
              ) : (
                <>
                  <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {cartItems.map(item => (
                      <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                        <div>
                          <p style={{ fontWeight: 600, fontSize: '14px' }}>{item.name}</p>
                          <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>₹{item.price} × {item.quantity}</span>
                        </div>
                        <span style={{ fontWeight: 700 }}>₹{item.price * item.quantity}</span>
                      </div>
                    ))}

                    <div style={{ marginTop: '16px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>DELIVERY ADDRESS</label>
                      <input 
                        type="text" 
                        value={deliveryAddr} 
                        onChange={e => setDeliveryAddr(e.target.value)}
                        style={{ width: '100%', marginTop: '6px', padding: '10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                      />
                    </div>

                    <div style={{ marginTop: '12px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>PROMO CODE</label>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                        <input 
                          type="text" 
                          placeholder="e.g. ZOMATO50"
                          value={promoCode} 
                          onChange={e => setPromoCode(e.target.value)}
                          style={{ flex: 1, padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                        />
                        <button onClick={applyPromo} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>Apply</button>
                      </div>
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', marginTop: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <span>Subtotal</span>
                      <span>₹{cartSubtotal}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <span>Delivery Fee</span>
                      <span>₹{deliveryFee}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <span>GST & Restaurant Charges (5%)</span>
                      <span>₹{tax.toFixed(1)}</span>
                    </div>
                    {discount > 0 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--accent-emerald)', marginBottom: '6px' }}>
                        <span>Promo Discount</span>
                        <span>-₹{discount}</span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: 800, marginTop: '12px', marginBottom: '20px' }}>
                      <span>To Pay</span>
                      <span>₹{grandTotal.toFixed(0)}</span>
                    </div>

                    <button
                      id="place-order-btn"
                      onClick={placeOrder}
                      disabled={isPlacingOrder}
                      style={{
                        width: '100%',
                        background: 'var(--primary-gradient)',
                        border: 'none',
                        color: '#fff',
                        padding: '14px',
                        borderRadius: '12px',
                        fontSize: '16px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        boxShadow: '0 0 25px var(--primary-glow)'
                      }}
                    >
                      {isPlacingOrder ? "Coordinating Saga..." : "Place Order (Saga Orchestration)"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Live Order Tracking Modal */}
        {isTrackingOpen && activeOrder && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 70, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(12px)', display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
            <div className="glass-panel" style={{ width: '100%', maxWidth: '640px', padding: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1.5px', color: 'var(--accent-emerald)', fontWeight: 700 }}>LIVE SAGA ORDER TRACKING</span>
                  <h3 style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px' }}>Order #{activeOrder.id}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{activeOrder.restaurant_name} • Total: ₹{activeOrder.total_amount}</p>
                </div>
                <button onClick={() => setIsTrackingOpen(false)} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
              </div>

              {/* Progress Timeline */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', margin: '24px 0' }}>
                {ORDER_STEPS.map((step, idx) => {
                  const isDone = idx <= currentStepIndex;
                  const isCurrent = idx === currentStepIndex;

                  return (
                    <div key={step.key} style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <div style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          background: isDone ? (isCurrent ? 'var(--accent-gold)' : 'var(--accent-emerald)') : 'rgba(255,255,255,0.1)',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '12px',
                          fontWeight: 700,
                          boxShadow: isCurrent ? '0 0 15px var(--accent-gold)' : 'none'
                        }}>
                          {isDone ? (isCurrent ? '●' : '✓') : idx + 1}
                        </div>
                        {idx < ORDER_STEPS.length - 1 && (
                          <div style={{ width: '2px', height: '32px', background: isDone && idx < currentStepIndex ? 'var(--accent-emerald)' : 'rgba(255,255,255,0.1)' }}></div>
                        )}
                      </div>

                      <div>
                        <p style={{ fontWeight: 700, fontSize: '15px', color: isDone ? '#fff' : 'var(--text-muted)' }}>{step.label}</p>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ textAlign: 'center', marginTop: '24px' }}>
                <button 
                  onClick={() => setIsTrackingOpen(false)}
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '10px 24px', borderRadius: '20px', cursor: 'pointer', fontWeight: 600 }}
                >
                  Close Tracking Window
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Embedded AI Assistant Drawer */}
        {isAIOpen && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 65, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)', display: 'flex', justifyContent: 'flex-end' }}>
            <div className="slide-drawer" style={{ width: '100%', maxWidth: '540px', background: 'var(--bg-secondary)', height: '100%', padding: '32px 24px', display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>✨</span>
                  <h3 style={{ fontSize: '20px', fontWeight: 800 }}>Zomato AI Copilot</h3>
                </div>
                <button onClick={() => setIsAIOpen(false)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '18px' }}>✕</button>
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <button 
                  onClick={() => setAiTab('sql')}
                  style={{ flex: 1, padding: '10px', borderRadius: '10px', border: '1px solid var(--border-subtle)', background: aiTab === 'sql' ? 'var(--primary-gradient)' : 'rgba(255,255,255,0.04)', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
                >
                  📊 Warehouse Analytics (SQL)
                </button>
                <button 
                  onClick={() => setAiTab('rag')}
                  style={{ flex: 1, padding: '10px', borderRadius: '10px', border: '1px solid var(--border-subtle)', background: aiTab === 'rag' ? 'var(--primary-gradient)' : 'rgba(255,255,255,0.04)', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
                >
                  🍔 Customer Feedback (RAG)
                </button>
              </div>

              {aiTab === 'sql' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                    Ask business analytics questions directly against Snowflake Gold Marts:
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {[
                      "Top 10 cities by GMV in 2024",
                      "Which cuisine generates the most orders?",
                      "Average delivery SLA by city, worst first"
                    ].map(q => (
                      <div key={q} style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', border: '1px solid var(--border-subtle)' }}>
                        👉 {q}
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: 'auto', padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-emerald)', borderRadius: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <p style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-emerald)', margin: 0 }}>⚡ LIVE STREAMLIT TEXT-TO-SQL APP</p>
                      <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 700 }}>:8501</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#fff', marginTop: '6px', marginBottom: '12px' }}>
                      Query Snowflake Gold Marts directly with natural language and SQL AST guardrails.
                    </p>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <a
                        href="http://localhost:8501"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          flex: 1,
                          textAlign: 'center',
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'var(--accent-emerald)',
                          color: '#fff',
                          fontSize: '12px',
                          fontWeight: 700,
                          textDecoration: 'none'
                        }}
                      >
                        Open Streamlit App ↗
                      </a>
                      <button
                        onClick={() => {
                          setEmbeddedApp('sql');
                          setIsAIOpen(false);
                          window.scrollTo({ top: 380, behavior: 'smooth' });
                        }}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'rgba(255, 255, 255, 0.1)',
                          border: '1px solid var(--border-subtle)',
                          color: '#fff',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer'
                        }}
                      >
                        Embed on Page ⬇
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                    Semantic vector search across 300,000 customer reviews with text-embedding-3-small:
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {[
                      "What are common complaints about cold food delivery in Bangalore?",
                      "Which restaurants have the highest ratings for Biryani?",
                      "Feedback trends regarding delivery riders"
                    ].map(q => (
                      <div key={q} style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', border: '1px solid var(--border-subtle)' }}>
                        💬 {q}
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: 'auto', padding: '16px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid var(--accent-blue)', borderRadius: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <p style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-blue)', margin: 0 }}>⚡ LIVE REVIEWS RAG CHAT APP</p>
                      <span style={{ fontSize: '11px', color: '#60a5fa', fontWeight: 700 }}>:8502</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#fff', marginTop: '6px', marginBottom: '12px' }}>
                      Search 300K customer reviews with LangGraph self-critique cycles and grounded citations.
                    </p>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <a
                        href="http://localhost:8502"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          flex: 1,
                          textAlign: 'center',
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'var(--accent-blue)',
                          color: '#fff',
                          fontSize: '12px',
                          fontWeight: 700,
                          textDecoration: 'none'
                        }}
                      >
                        Open Streamlit App ↗
                      </a>
                      <button
                        onClick={() => {
                          setEmbeddedApp('rag');
                          setIsAIOpen(false);
                          window.scrollTo({ top: 380, behavior: 'smooth' });
                        }}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'rgba(255, 255, 255, 0.1)',
                          border: '1px solid var(--border-subtle)',
                          color: '#fff',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer'
                        }}
                      >
                        Embed on Page ⬇
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer style={{ marginTop: 'auto', borderTop: '1px solid var(--border-subtle)', padding: '24px 32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
          Zomato AI Enterprise Platform • Staff / Principal Engineer Architecture • Snowflake Medallion Lakehouse • Go Microservices • Kafka Event Sourcing
        </footer>
      </div>
    </>
  );
}
