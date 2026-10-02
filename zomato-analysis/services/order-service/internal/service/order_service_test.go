package service_test

import (
	"context"
	"testing"

	"github.com/zomato/order-service/internal/domain"
	"github.com/zomato/order-service/internal/events"
	"github.com/zomato/order-service/internal/repository"
	"github.com/zomato/order-service/internal/service"
)

func TestCreateOrder_Success(t *testing.T) {
	repo := repository.NewMemoryOrderRepository()
	producer := events.NewLoggingEventProducer()
	saga := events.NewSagaOrchestrator(producer)
	svc := service.NewOrderService(repo, saga)

	req := service.CreateOrderRequest{
		CustomerID:     "cust_1001",
		RestaurantID:   "rest_501",
		RestaurantName: "Empire Restaurant",
		City:           "Bangalore",
		DeliveryAddr:   "100 Feet Rd, Indiranagar",
		PaymentMethod:  "UPI",
		Items: []domain.OrderItem{
			{FoodID: "f_1", Name: "Chicken Biryani", Quantity: 2, Price: 280.0},
			{FoodID: "f_2", Name: "Garlic Naan", Quantity: 3, Price: 60.0},
		},
		Discount: 50.0,
	}

	order, err := svc.CreateOrder(context.Background(), req)
	if err != nil {
		t.Fatalf("expected nil error, got %v", err)
	}

	if order.ID == "" {
		t.Errorf("expected generated order ID, got empty")
	}

	// Subtotal = 2*280 + 3*60 = 560 + 180 = 740
	// DeliveryFee = 40
	// Tax = 740 * 0.05 = 37
	// Discount = 50
	// Total = 740 + 40 + 37 - 50 = 767.0
	expectedTotal := 767.0
	if order.TotalAmount != expectedTotal {
		t.Errorf("expected total %.2f, got %.2f", expectedTotal, order.TotalAmount)
	}

	if order.Status != domain.StatusPending {
		t.Errorf("expected status %s, got %s", domain.StatusPending, order.Status)
	}
}

func TestCreateOrder_Idempotency(t *testing.T) {
	repo := repository.NewMemoryOrderRepository()
	producer := events.NewLoggingEventProducer()
	saga := events.NewSagaOrchestrator(producer)
	svc := service.NewOrderService(repo, saga)

	idempotencyKey := "idem_key_123456"

	req := service.CreateOrderRequest{
		CustomerID:     "cust_1001",
		RestaurantID:   "rest_501",
		RestaurantName: "Empire Restaurant",
		City:           "Bangalore",
		PaymentMethod:  "UPI",
		IdempotencyKey: idempotencyKey,
		Items: []domain.OrderItem{
			{FoodID: "f_1", Name: "Chicken Biryani", Quantity: 1, Price: 280.0},
		},
	}

	order1, err1 := svc.CreateOrder(context.Background(), req)
	if err1 != nil {
		t.Fatalf("first request failed: %v", err1)
	}

	order2, err2 := svc.CreateOrder(context.Background(), req)
	if err2 != nil {
		t.Fatalf("idempotent second request failed: %v", err2)
	}

	if order1.ID != order2.ID {
		t.Errorf("expected identical order ID for idempotent request: %s != %s", order1.ID, order2.ID)
	}
}
