package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/zomato/order-service/internal/domain"
	"github.com/zomato/order-service/internal/service"
)

type OrderHandler struct {
	svc *service.OrderService
}

func NewOrderHandler(svc *service.OrderService) *OrderHandler {
	return &OrderHandler{svc: svc}
}

func (h *OrderHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/healthz", h.Healthz)
	mux.HandleFunc("/api/v1/orders", h.HandleOrders)
	mux.HandleFunc("/api/v1/orders/", h.HandleOrderByID)
}

func (h *OrderHandler) Healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"service":   "order-service",
		"timestamp": time.Now().UTC(),
	})
}

func (h *OrderHandler) HandleOrders(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	switch r.Method {
	case http.MethodPost:
		var req service.CreateOrderRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "invalid JSON: %s"}`, err.Error()), http.StatusBadRequest)
			return
		}

		idempotencyKey := r.Header.Get("Idempotency-Key")
		if idempotencyKey != "" {
			req.IdempotencyKey = idempotencyKey
		}

		order, err := h.svc.CreateOrder(r.Context(), req)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "%s"}`, err.Error()), http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(order)

	case http.MethodGet:
		orders, err := h.svc.ListRecentOrders(r.Context(), 50)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "%s"}`, err.Error()), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(orders)

	default:
		http.Error(w, `{"error": "method not allowed"}`, http.StatusMethodNotAllowed)
	}
}

func (h *OrderHandler) HandleOrderByID(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	path := strings.TrimPrefix(r.URL.Path, "/api/v1/orders/")
	parts := strings.Split(path, "/")
	orderID := parts[0]

	if orderID == "" {
		http.Error(w, `{"error": "order ID is required"}`, http.StatusBadRequest)
		return
	}

	// Check if SSE tracking stream is requested: /api/v1/orders/{id}/stream
	if len(parts) > 1 && parts[1] == "stream" {
		h.streamOrderStatus(w, r, orderID)
		return
	}

	order, err := h.svc.GetOrder(r.Context(), orderID)
	if err != nil {
		if err == domain.ErrOrderNotFound {
			http.Error(w, `{"error": "order not found"}`, http.StatusNotFound)
		} else {
			http.Error(w, fmt.Sprintf(`{"error": "%s"}`, err.Error()), http.StatusInternalServerError)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(order)
}

func (h *OrderHandler) streamOrderStatus(w http.ResponseWriter, r *http.Request, orderID string) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	var lastStatus domain.OrderStatus

	for {
		select {
		case <-r.Context().Done():
			return
		case <-ticker.C:
			order, err := h.svc.GetOrder(r.Context(), orderID)
			if err != nil {
				return
			}

			if order.Status != lastStatus {
				lastStatus = order.Status
				data, _ := json.Marshal(map[string]interface{}{
					"order_id": order.ID,
					"status":   order.Status,
					"time":     time.Now().UTC(),
				})
				_, _ = fmt.Fprintf(w, "data: %s\n\n", data)
				flusher.Flush()
			}

			if order.Status == domain.StatusDelivered || order.Status == domain.StatusCancelled {
				return
			}
		}
	}
}

func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, Idempotency-Key")
}
