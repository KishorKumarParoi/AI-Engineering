package repository

import (
	"context"
	"sync"
	"time"

	"github.com/zomato/order-service/internal/domain"
)

type OrderRepository interface {
	CreateOrderWithOutbox(ctx context.Context, order *domain.Order, event *domain.OutboxEvent) error
	GetOrderByID(ctx context.Context, id string) (*domain.Order, error)
	GetOrderByIdempotencyKey(ctx context.Context, key string) (*domain.Order, error)
	UpdateOrderStatus(ctx context.Context, id string, status domain.OrderStatus) error
	ListRecentOrders(ctx context.Context, limit int) ([]domain.Order, error)
	GetPendingOutboxEvents(ctx context.Context, limit int) ([]domain.OutboxEvent, error)
	MarkOutboxProcessed(ctx context.Context, eventID string) error
}

type MemoryOrderRepository struct {
	mu           sync.RWMutex
	orders       map[string]*domain.Order
	idempotency  map[string]string // key -> orderID
	outboxEvents map[string]*domain.OutboxEvent
}

func NewMemoryOrderRepository() *MemoryOrderRepository {
	return &MemoryOrderRepository{
		orders:       make(map[string]*domain.Order),
		idempotency:  make(map[string]string),
		outboxEvents: make(map[string]*domain.OutboxEvent),
	}
}

func (r *MemoryOrderRepository) CreateOrderWithOutbox(ctx context.Context, order *domain.Order, event *domain.OutboxEvent) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if order.IdempotencyKey != "" {
		if existingID, exists := r.idempotency[order.IdempotencyKey]; exists {
			if existingOrder, ok := r.orders[existingID]; ok {
				*order = *existingOrder
				return domain.ErrDuplicateRequest
			}
		}
		r.idempotency[order.IdempotencyKey] = order.ID
	}

	orderCopy := *order
	r.orders[order.ID] = &orderCopy

	if event != nil {
		eventCopy := *event
		r.outboxEvents[event.ID] = &eventCopy
	}

	return nil
}

func (r *MemoryOrderRepository) GetOrderByID(ctx context.Context, id string) (*domain.Order, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	order, exists := r.orders[id]
	if !exists {
		return nil, domain.ErrOrderNotFound
	}
	orderCopy := *order
	return &orderCopy, nil
}

func (r *MemoryOrderRepository) GetOrderByIdempotencyKey(ctx context.Context, key string) (*domain.Order, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	id, exists := r.idempotency[key]
	if !exists {
		return nil, domain.ErrOrderNotFound
	}
	return r.GetOrderByID(ctx, id)
}

func (r *MemoryOrderRepository) UpdateOrderStatus(ctx context.Context, id string, status domain.OrderStatus) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	order, exists := r.orders[id]
	if !exists {
		return domain.ErrOrderNotFound
	}
	order.Status = status
	order.UpdatedAt = time.Now().UTC()
	return nil
}

func (r *MemoryOrderRepository) ListRecentOrders(ctx context.Context, limit int) ([]domain.Order, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]domain.Order, 0, len(r.orders))
	for _, o := range r.orders {
		result = append(result, *o)
		if limit > 0 && len(result) >= limit {
			break
		}
	}
	return result, nil
}

func (r *MemoryOrderRepository) GetPendingOutboxEvents(ctx context.Context, limit int) ([]domain.OutboxEvent, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	events := make([]domain.OutboxEvent, 0)
	for _, e := range r.outboxEvents {
		if e.Status == "PENDING" {
			events = append(events, *e)
			if limit > 0 && len(events) >= limit {
				break
			}
		}
	}
	return events, nil
}

func (r *MemoryOrderRepository) MarkOutboxProcessed(ctx context.Context, eventID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if event, exists := r.outboxEvents[eventID]; exists {
		event.Status = "PROCESSED"
	}
	return nil
}
