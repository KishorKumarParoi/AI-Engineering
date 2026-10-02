package events

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/zomato/order-service/internal/domain"
)

type EventProducer interface {
	Publish(ctx context.Context, topic string, key string, payload []byte) error
}

type OrderEventPayload struct {
	OrderID        string             `json:"order_id"`
	CustomerID     string             `json:"customer_id"`
	RestaurantID   string             `json:"restaurant_id"`
	City           string             `json:"city"`
	TotalAmount    float64            `json:"total_amount"`
	Status         domain.OrderStatus `json:"status"`
	EstimatedMins  int                `json:"estimated_delivery_mins"`
	Timestamp      time.Time          `json:"timestamp"`
}

type LoggingEventProducer struct {
	mu     sync.Mutex
	events []string
}

func NewLoggingEventProducer() *LoggingEventProducer {
	return &LoggingEventProducer{
		events: make([]string, 0),
	}
}

func (p *LoggingEventProducer) Publish(ctx context.Context, topic string, key string, payload []byte) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	msg := fmt.Sprintf("[%s] Key: %s | Payload: %s", topic, key, string(payload))
	p.events = append(p.events, msg)
	log.Printf("[KAFKA EMULATOR] Published to topic '%s' (key: %s): %s", topic, key, string(payload))
	return nil
}

// SagaOrchestrator manages the distributed order saga asynchronously
type SagaOrchestrator struct {
	producer EventProducer
	statusCh chan domain.OrderStatus
}

func NewSagaOrchestrator(producer EventProducer) *SagaOrchestrator {
	return &SagaOrchestrator{
		producer: producer,
		statusCh: make(chan domain.OrderStatus, 100),
	}
}

// SimulateSagaExecution simulates asynchronous Saga transitions across Payment, Kitchen, Rider, Delivery
func (s *SagaOrchestrator) ExecuteOrderSaga(ctx context.Context, order *domain.Order, onStatusUpdate func(id string, status domain.OrderStatus)) {
	go func() {
		time.Sleep(1500 * time.Millisecond)
		onStatusUpdate(order.ID, domain.StatusPaymentAuthorized)
		s.publishOrderEvent(ctx, "zomato.payment.authorized", order.ID, domain.StatusPaymentAuthorized)

		time.Sleep(1500 * time.Millisecond)
		onStatusUpdate(order.ID, domain.StatusConfirmed)
		s.publishOrderEvent(ctx, "zomato.order.confirmed", order.ID, domain.StatusConfirmed)

		time.Sleep(2000 * time.Millisecond)
		onStatusUpdate(order.ID, domain.StatusKitchenAccepted)
		s.publishOrderEvent(ctx, "zomato.kitchen.accepted", order.ID, domain.StatusKitchenAccepted)

		time.Sleep(2500 * time.Millisecond)
		onStatusUpdate(order.ID, domain.StatusRiderAssigned)
		s.publishOrderEvent(ctx, "zomato.rider.assigned", order.ID, domain.StatusRiderAssigned)

		time.Sleep(3000 * time.Millisecond)
		onStatusUpdate(order.ID, domain.StatusOutForDelivery)
		s.publishOrderEvent(ctx, "zomato.order.out_for_delivery", order.ID, domain.StatusOutForDelivery)
	}()
}

func (s *SagaOrchestrator) publishOrderEvent(ctx context.Context, topic string, orderID string, status domain.OrderStatus) {
	payload, _ := json.Marshal(map[string]interface{}{
		"order_id":  orderID,
		"status":    status,
		"timestamp": time.Now().UTC(),
	})
	_ = s.producer.Publish(ctx, topic, orderID, payload)
}
