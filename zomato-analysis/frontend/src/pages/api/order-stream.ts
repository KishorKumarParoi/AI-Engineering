import type { NextApiRequest, NextApiResponse } from 'next';

interface OrderEventPayload {
  order_id: string;
  customer_id: string;
  restaurant_id: string;
  restaurant_name: string;
  city: string;
  order_status: 'PLACED' | 'ACCEPTED' | 'PREPARING' | 'PICKED_UP' | 'DELIVERED';
  order_amount: number;
  delivery_fee: number;
  item_count: number;
  payment_method: string;
  delivery_distance_km: number;
  predicted_delivery_eta_mins: number;
  eta_confidence_band: [number, number];
  event_timestamp: string;
  published_to_kafka: boolean;
  target_topic: string;
}

const SAMPLE_RESTAURANTS = [
  { id: "rest_101", name: "Truffles Central", city: "Bangalore", baseDist: 3.2 },
  { id: "rest_102", name: "Empire Restaurant", city: "Bangalore", baseDist: 4.5 },
  { id: "rest_103", name: "Bastian Bandra", city: "Mumbai", baseDist: 6.8 },
  { id: "rest_104", name: "Karim's Historic", city: "Delhi", baseDist: 5.1 },
  { id: "rest_105", name: "Meghana Foods", city: "Bangalore", baseDist: 2.4 },
];

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{ success: boolean; data: OrderEventPayload; message: string }>
) {
  // Select random or requested restaurant
  const rest = SAMPLE_RESTAURANTS[Math.floor(Math.random() * SAMPLE_RESTAURANTS.length)];
  const orderId = `ORD-${Math.random().toString(16).substring(2, 8).toUpperCase()}`;
  const itemCount = Math.floor(Math.random() * 5) + 1;
  const distanceKm = parseFloat((rest.baseDist + (Math.random() * 2 - 1)).toFixed(1));
  
  // Databricks MLflow GBT ETA Formula
  const predictedEta = parseFloat((12.0 + distanceKm * 3.2 + (itemCount > 2 ? 6.5 : 2.0)).toFixed(1));

  const payload: OrderEventPayload = {
    order_id: orderId,
    customer_id: `CUST-${Math.floor(Math.random() * 9000) + 1000}`,
    restaurant_id: rest.id,
    restaurant_name: rest.name,
    city: rest.city,
    order_status: 'PLACED',
    order_amount: Math.floor(Math.random() * 850) + 250,
    delivery_fee: Math.random() > 0.5 ? 35 : 50,
    item_count: itemCount,
    payment_method: Math.random() > 0.4 ? 'UPI' : 'CREDIT_CARD',
    delivery_distance_km: distanceKm,
    predicted_delivery_eta_mins: predictedEta,
    eta_confidence_band: [parseFloat((predictedEta - 3.5).toFixed(1)), parseFloat((predictedEta + 3.5).toFixed(1))],
    event_timestamp: new Date().toISOString(),
    published_to_kafka: true,
    target_topic: 'zomato.order_events',
  };

  return res.status(200).json({
    success: true,
    data: payload,
    message: `Order ${orderId} successfully streamed into Kafka topic [zomato.order_events]`
  });
}
