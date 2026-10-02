package service

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/zomato/order-service/internal/domain"
	"github.com/zomato/order-service/internal/events"
	"github.com/zomato/order-service/internal/repository"
)

type CreateOrderRequest struct {
	CustomerID     string             `json:"customer_id"`
	RestaurantID   string             `json:"restaurant_id"`
	RestaurantName string             `json:"restaurant_name"`
	City           string             `json:"city"`
	DeliveryAddr   string             `json:"delivery_address"`
	Items          []domain.OrderItem `json:"items"`
	PaymentMethod  string             `json:"payment_method"`
	IdempotencyKey string             `json:"idempotency_key"`
	Discount       float64            `json:"discount"`
}

type OrderService struct {
	repo repository.OrderRepository
	saga *events.SagaOrchestrator
}

func NewOrderService(repo repository.OrderRepository, saga *events.SagaOrchestrator) *OrderService {
	return &OrderService{
		repo: repo,
		saga: saga,
	}
}

func generateID(prefix string) string {
	bytes := make([]byte, 8)
	_, _ = rand.Read(bytes)
	return fmt.Sprintf("%s_%s", prefix, hex.EncodeToString(bytes))
}

func (s *OrderService) CreateOrder(ctx context.Context, req CreateOrderRequest) (*domain.Order, error) {
	if len(req.Items) == 0 {
		return nil, domain.ErrEmptyItems
	}

	// Check Idempotency Key
	if req.IdempotencyKey != "" {
		existing, err := s.repo.GetOrderByIdempotencyKey(ctx, req.IdempotencyKey)
		if err == nil && existing != nil {
			return existing, nil
		}
	}

	now := time.Now().UTC()
	order := &domain.Order{
		ID:             generateID("ord"),
		CustomerID:     req.CustomerID,
		RestaurantID:   req.RestaurantID,
		RestaurantName: req.RestaurantName,
		City:           req.City,
		DeliveryAddr:   req.DeliveryAddr,
		Items:          req.Items,
		Discount:       req.Discount,
		PaymentMethod:  req.PaymentMethod,
		Status:         domain.StatusPending,
		IdempotencyKey: req.IdempotencyKey,
		EstimatedMins:  35, // Dynamic SLA estimate
		CreatedAt:      now,
		UpdatedAt:      now,
	}

	for i := range order.Items {
		if order.Items[i].ID == "" {
			order.Items[i].ID = generateID("item")
		}
	}

	order.CalculateTotals()
	if order.TotalAmount <= 0 {
		return nil, domain.ErrInvalidAmount
	}

	payloadBytes, _ := json.Marshal(order)
	outboxEvent := &domain.OutboxEvent{
		ID:            generateID("evt"),
		AggregateType: "Order",
		AggregateID:   order.ID,
		EventType:     "OrderCreated",
		Payload:       string(payloadBytes),
		Status:        "PENDING",
		CreatedAt:     now,
	}

	if err := s.repo.CreateOrderWithOutbox(ctx, order, outboxEvent); err != nil {
		if err == domain.ErrDuplicateRequest {
			return order, nil
		}
		return nil, err
	}

	// Start asynchronous Saga flow
	s.saga.ExecuteOrderSaga(ctx, order, func(id string, status domain.OrderStatus) {
		_ = s.repo.UpdateOrderStatus(context.Background(), id, status)
	})

	return order, nil
}

func (s *OrderService) GetOrder(ctx context.Context, id string) (*domain.Order, error) {
	return s.repo.GetOrderByID(ctx, id)
}

func (s *OrderService) ListRecentOrders(ctx context.Context, limit int) ([]domain.Order, error) {
	return s.repo.ListRecentOrders(ctx, limit)
}
