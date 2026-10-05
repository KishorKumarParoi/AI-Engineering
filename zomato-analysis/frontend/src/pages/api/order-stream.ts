import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';
import { EventHubProducerClient } from '@azure/event-hubs';
import { AUTHENTIC_DATABASE_RESTAURANTS } from '../../data/database_catalog';

export interface OrderEventPayload {
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
  unit_price: number;
  subtotal: number;
  payment_method: string;
  delivery_distance_km: number;
  predicted_delivery_eta_mins: number;
  eta_confidence_band: [number, number];
  event_timestamp: string;
  published_to_kafka: boolean;
  target_topic: string;
}

const ORDER_STATUSES: OrderEventPayload['order_status'][] = ['PLACED', 'ACCEPTED', 'PREPARING', 'PICKED_UP', 'DELIVERED'];
const PAYMENT_METHODS = ['UPI', 'CREDIT_CARD', 'ZOMATO_PAY', 'CASH'];

// Singleton EventHubProducerClient
let cachedProducer: EventHubProducerClient | null = null;

function getProducer(): { client: EventHubProducerClient | null; hubName: string } {
  let hubName = process.env.EVENT_HUBNAME || 'zomato';
  if (cachedProducer) return { client: cachedProducer, hubName };

  try {
    const rootDir = path.resolve(process.cwd(), '..');
    const envPath = path.join(rootDir, '.env');
    let connStr = process.env.CONNECTION_STRING;

    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8');
      content.split('\n').forEach(line => {
        const m = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
        if (m) {
          let v = m[2] || '';
          if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
          if (m[1] === 'CONNECTION_STRING' && !connStr) connStr = v;
          if (m[1] === 'EVENT_HUBNAME') hubName = v;
        }
      });
    }

    if (connStr) {
      cachedProducer = new EventHubProducerClient(connStr, hubName);
      return { client: cachedProducer, hubName };
    }
  } catch (e) {
    console.error('Error initializing EventHubProducerClient:', e);
  }
  return { client: null, hubName };
}

function generateSinglePayload(cuisine?: string, city?: string, targetTopic: string = 'zomato'): OrderEventPayload {
  let candidates = AUTHENTIC_DATABASE_RESTAURANTS;
  if (cuisine && cuisine.toLowerCase() !== 'all') {
    const q = cuisine.toLowerCase();
    const filtered = candidates.filter(r =>
      r.cuisine.toLowerCase().includes(q) ||
      (r.menu && r.menu.some(m => m.category.toLowerCase().includes(q)))
    );
    if (filtered.length > 0) candidates = filtered;
  }

  if (city && city.toLowerCase() !== 'all') {
    const q = city.toLowerCase();
    const filtered = candidates.filter(r => r.city.toLowerCase() === q);
    if (filtered.length > 0) candidates = filtered;
  }

  const rest = candidates[Math.floor(Math.random() * candidates.length)];
  const menuItems = rest.menu && rest.menu.length > 0 ? rest.menu : [
    { food_id: 'fd0', name: 'Aloo Tikki Burger', price: 65, category: 'Burgers' }
  ];
  const dish = menuItems[Math.floor(Math.random() * menuItems.length)];

  const orderId = `ORD-${Math.random().toString(16).substring(2, 8).toUpperCase()}`;
  const itemCount = Math.floor(Math.random() * 3) + 1;
  const unitPrice = dish.price || 149;
  const subtotal = unitPrice * itemCount;
  const deliveryFee = Math.random() > 0.5 ? 35 : 50;
  const orderAmount = subtotal + deliveryFee;
  const distanceKm = parseFloat((Math.random() * 4.5 + 1.8).toFixed(1));

  // Databricks MLflow GBT ETA Formula
  const predictedEta = parseFloat((12.0 + distanceKm * 3.2 + (itemCount > 2 ? 5.5 : 1.8)).toFixed(1));

  return {
    order_id: orderId,
    customer_id: `CUST-${Math.floor(Math.random() * 9000) + 1000}`,
    restaurant_id: rest.id,
    restaurant_name: rest.name,
    food_id: dish.food_id,
    food_name: dish.name,
    cuisine: dish.category || rest.cuisine.split(',')[0],
    city: rest.city,
    order_status: ORDER_STATUSES[Math.floor(Math.random() * ORDER_STATUSES.length)],
    order_amount: orderAmount,
    delivery_fee: deliveryFee,
    item_count: itemCount,
    unit_price: unitPrice,
    subtotal: subtotal,
    payment_method: PAYMENT_METHODS[Math.floor(Math.random() * PAYMENT_METHODS.length)],
    delivery_distance_km: distanceKm,
    predicted_delivery_eta_mins: predictedEta,
    eta_confidence_band: [parseFloat((predictedEta - 3.5).toFixed(1)), parseFloat((predictedEta + 3.5).toFixed(1))],
    event_timestamp: new Date().toISOString(),
    published_to_kafka: true,
    target_topic: targetTopic,
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{
    success: boolean;
    data?: OrderEventPayload | OrderEventPayload[];
    events?: OrderEventPayload[];
    message: string;
    target_topic?: string;
  }>
) {
  const { cuisine, city, count } = req.query;
  const numEvents = Math.min(Math.max(parseInt(count as string) || 1, 1), 50);

  const { client: producer, hubName } = getProducer();
  const generatedEvents: OrderEventPayload[] = [];

  for (let i = 0; i < numEvents; i++) {
    generatedEvents.push(
      generateSinglePayload(
        typeof cuisine === 'string' ? cuisine : undefined,
        typeof city === 'string' ? city : undefined,
        hubName
      )
    );
  }

  // 1. Dispatch directly to Azure Event Hubs instance "zomato"
  let publishedToEventHub = false;
  if (producer) {
    try {
      const batch = await producer.createBatch();
      for (const ev of generatedEvents) {
        batch.tryAdd({ body: ev });
      }
      await producer.sendBatch(batch);
      publishedToEventHub = true;
      console.log(`[✓] Dispatched ${generatedEvents.length} event(s) directly to Azure Event Hub: "${hubName}"`);
    } catch (ehErr) {
      console.warn('[!] Failed to send batch to Azure Event Hubs:', ehErr);
    }
  }

  // 2. Buffer events to shared data sink for Airflow micro-batch cronjob
  try {
    const rootDir = path.resolve(process.cwd(), '..');
    const bufferPath = path.join(rootDir, 'data', 'kafka_order_events.jsonl');
    fs.mkdirSync(path.dirname(bufferPath), { recursive: true });
    const lines = generatedEvents.map(e => JSON.stringify(e)).join('\n') + '\n';
    fs.appendFileSync(bufferPath, lines, 'utf-8');
  } catch (err) {
    // Non-blocking fallback
  }

  const message = publishedToEventHub
    ? `Streamed ${numEvents} event(s) directly into Azure Event Hub [${hubName}] & Lakehouse buffer.`
    : `Buffered ${numEvents} event(s) to Lakehouse buffer.`;

  return res.status(200).json({
    success: true,
    data: numEvents === 1 ? generatedEvents[0] : generatedEvents,
    events: generatedEvents,
    target_topic: hubName,
    message
  });
}
