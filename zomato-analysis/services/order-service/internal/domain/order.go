package domain

import (
	"errors"
	"time"
)

type OrderStatus string

const (
	StatusPending           OrderStatus = "PENDING"
	StatusPaymentAuthorized OrderStatus = "PAYMENT_AUTHORIZED"
	StatusConfirmed         OrderStatus = "CONFIRMED"
	StatusKitchenAccepted   OrderStatus = "KITCHEN_ACCEPTED"
	StatusRiderAssigned     OrderStatus = "RIDER_ASSIGNED"
	StatusOutForDelivery    OrderStatus = "OUT_FOR_DELIVERY"
	StatusDelivered         OrderStatus = "DELIVERED"
	StatusCancelled         OrderStatus = "CANCELLED"
)

var (
	ErrEmptyItems       = errors.New("order must contain at least one item")
	ErrInvalidAmount    = errors.New("total amount must be greater than zero")
	ErrOrderNotFound    = errors.New("order not found")
	ErrDuplicateRequest = errors.New("duplicate request with idempotency key")
)

type OrderItem struct {
	ID        string  `json:"id"`
	FoodID    string  `json:"food_id"`
	Name      string  `json:"name"`
	Quantity  int     `json:"quantity"`
	Price     float64 `json:"price"`
	LineTotal float64 `json:"line_total"`
}

type Order struct {
	ID             string      `json:"id"`
	CustomerID     string      `json:"customer_id"`
	RestaurantID   string      `json:"restaurant_id"`
	RestaurantName string      `json:"restaurant_name"`
	City           string      `json:"city"`
	DeliveryAddr   string      `json:"delivery_address"`
	Items          []OrderItem `json:"items"`
	Subtotal       float64     `json:"subtotal"`
	Discount       float64     `json:"discount"`
	DeliveryFee    float64     `json:"delivery_fee"`
	Tax            float64     `json:"tax"`
	TotalAmount    float64     `json:"total_amount"`
	PaymentMethod  string      `json:"payment_method"`
	Status         OrderStatus `json:"status"`
	IdempotencyKey string      `json:"idempotency_key"`
	EstimatedMins  int         `json:"estimated_delivery_mins"`
	CreatedAt      time.Time   `json:"created_at"`
	UpdatedAt      time.Time   `json:"updated_at"`
}

func (o *Order) CalculateTotals() {
	var subtotal float64
	for i := range o.Items {
		o.Items[i].LineTotal = float64(o.Items[i].Quantity) * o.Items[i].Price
		subtotal += o.Items[i].LineTotal
	}
	o.Subtotal = subtotal
	if o.DeliveryFee == 0 {
		o.DeliveryFee = 40.0 // Standard default delivery fee
	}
	o.Tax = subtotal * 0.05 // 5% GST
	o.TotalAmount = (subtotal + o.DeliveryFee + o.Tax) - o.Discount
	if o.TotalAmount < 0 {
		o.TotalAmount = 0
	}
}

type OutboxEvent struct {
	ID            string    `json:"id"`
	AggregateType string    `json:"aggregate_type"`
	AggregateID   string    `json:"aggregate_id"`
	EventType     string    `json:"event_type"`
	Payload       string    `json:"payload"`
	Status        string    `json:"status"`
	CreatedAt     time.Time `json:"created_at"`
}
