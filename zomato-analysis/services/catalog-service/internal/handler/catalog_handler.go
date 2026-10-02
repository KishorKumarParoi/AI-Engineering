package handler

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/zomato/catalog-service/internal/domain"
	"github.com/zomato/catalog-service/internal/repository"
)

type CatalogHandler struct {
	repo repository.CatalogRepository
}

func NewCatalogHandler(repo repository.CatalogRepository) *CatalogHandler {
	return &CatalogHandler{repo: repo}
}

func (h *CatalogHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/healthz", h.Healthz)
	mux.HandleFunc("/api/v1/restaurants", h.HandleRestaurants)
	mux.HandleFunc("/api/v1/restaurants/", h.HandleRestaurantByID)
}

func (h *CatalogHandler) Healthz(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"service":   "catalog-service",
		"timestamp": time.Now().UTC(),
	})
}

func (h *CatalogHandler) HandleRestaurants(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	city := r.URL.Query().Get("city")
	cuisine := r.URL.Query().Get("cuisine")
	minRatingStr := r.URL.Query().Get("min_rating")
	limitStr := r.URL.Query().Get("limit")

	var minRating float64
	if minRatingStr != "" {
		minRating, _ = strconv.ParseFloat(minRatingStr, 64)
	}

	var limit int
	if limitStr != "" {
		limit, _ = strconv.Atoi(limitStr)
	}

	filter := domain.RestaurantFilter{
		City:      city,
		Cuisine:   cuisine,
		MinRating: minRating,
		Limit:     limit,
	}

	restaurants, err := h.repo.ListRestaurants(r.Context(), filter)
	if err != nil {
		http.Error(w, `{"error": "failed to list restaurants"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(restaurants)
}

func (h *CatalogHandler) HandleRestaurantByID(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	path := strings.TrimPrefix(r.URL.Path, "/api/v1/restaurants/")
	parts := strings.Split(path, "/")
	restaurantID := parts[0]

	if restaurantID == "" {
		http.Error(w, `{"error": "restaurant ID required"}`, http.StatusBadRequest)
		return
	}

	// Check if menu requested: /api/v1/restaurants/{id}/menu
	if len(parts) > 1 && parts[1] == "menu" {
		menu, err := h.repo.GetMenuByRestaurantID(r.Context(), restaurantID)
		if err != nil {
			http.Error(w, `{"error": "failed to get menu"}`, http.StatusInternalServerError)
			return
		}
		if menu == nil {
			http.Error(w, `{"error": "restaurant not found"}`, http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(menu)
		return
	}

	restaurant, err := h.repo.GetRestaurantByID(r.Context(), restaurantID)
	if err != nil {
		http.Error(w, `{"error": "failed to fetch restaurant"}`, http.StatusInternalServerError)
		return
	}
	if restaurant == nil {
		http.Error(w, `{"error": "restaurant not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(restaurant)
}

func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}
