package repository

import (
	"context"
	"strings"
	"sync"

	"github.com/zomato/catalog-service/internal/domain"
)

type CatalogRepository interface {
	ListRestaurants(ctx context.Context, filter domain.RestaurantFilter) ([]domain.Restaurant, error)
	GetRestaurantByID(ctx context.Context, id string) (*domain.Restaurant, error)
	GetMenuByRestaurantID(ctx context.Context, restaurantID string) ([]domain.MenuItem, error)
}

type MemoryCatalogRepository struct {
	mu          sync.RWMutex
	restaurants map[string]*domain.Restaurant
}

func NewMemoryCatalogRepository() *MemoryCatalogRepository {
	repo := &MemoryCatalogRepository{
		restaurants: make(map[string]*domain.Restaurant),
	}
	repo.seedInitialData()
	return repo
}

func (r *MemoryCatalogRepository) seedInitialData() {
	sampleRestaurants := []*domain.Restaurant{
		{
			ID:          "170435",
			Name:        "Good Flippin' Burgers",
			City:        "Mumbai",
			Cuisine:     "Burgers, Fast Food",
			Rating:      4.6,
			RatingCount: 14200,
			CostForTwo:  500,
			Address:     "Bandra West, Mumbai",
			ImageURL:    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd745691", FoodID: "fd745691", Name: "Aloo Tikki Cheese Crunch Burger", Category: "Burgers", Price: 137, IsVeg: true, Description: "Crispy spiced aloo tikki patty topped with melted cheese, secret burger relish and fresh greens"},
				{ID: "m_fd5", FoodID: "fd5", Name: "Bbq Chicken Burger", Category: "Burgers", Price: 180, IsVeg: false, Description: "Smoky barbecue charred chicken patty glazed in hickory sauce on toasted sesame brioche"},
				{ID: "m_fd2", FoodID: "fd2", Name: "Cheese Burst Burger", Category: "Burgers", Price: 150, IsVeg: true, Description: "Molten cheddar cheese burst core enveloped in a golden herb crust with garlic aioli"},
				{ID: "m_fd6", FoodID: "fd6", Name: "Peri Peri Chicken Burger", Category: "Burgers", Price: 190, IsVeg: false, Description: "Fiery African bird's eye chili spiced chicken fillet with crunchy slaw and spicy mayo"},
			},
		},
		{
			ID:          "537139",
			Name:        "NARMADA Chain of Restaurants",
			City:        "Bangalore",
			Cuisine:     "Biryani, Andhra",
			Rating:      4.5,
			RatingCount: 28500,
			CostForTwo:  500,
			Address:     "Koramangala 5th Block, Bangalore",
			ImageURL:    "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd3970", FoodID: "fd3970", Name: "Dsp Chicken Dum Biryani", Category: "Biryani", Price: 280, IsVeg: false, Description: "Authentic slow-cooked spicy chicken dum biryani infused with Andhra herbs, saffron & ghee"},
				{ID: "m_fd2624", FoodID: "fd2624", Name: "Mutton Biryani", Category: "Biryani", Price: 340, IsVeg: false, Description: "Tender goat meat slow-braised in clay handi with aged basmati, fried onions and fresh mint"},
				{ID: "m_fd921119", FoodID: "fd921119", Name: "Dum Paneer Biryani One Kg- Jain", Category: "Biryani", Price: 316, IsVeg: true, Description: "Fresh cottage cheese cubes slow dum-cooked in fragrant basmati with royal whole spices"},
				{ID: "m_fd817", FoodID: "fd817", Name: "Veg Biryani", Category: "Biryani", Price: 220, IsVeg: true, Description: "Assorted garden fresh vegetables steamed on dum with fragrant basmati and kewra"},
			},
		},
		{
			ID:          "56590",
			Name:        "Mangalore Pearl",
			City:        "Bangalore",
			Cuisine:     "Coastal, Seafood",
			Rating:      4.5,
			RatingCount: 11200,
			CostForTwo:  550,
			Address:     "Frazer Town, Central Bangalore",
			ImageURL:    "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd38410", FoodID: "fd38410", Name: "Fish Curry (4 Pcs)", Category: "Seafood", Price: 130, IsVeg: false, Description: "Traditional coastal curry with fresh sea fish simmered in tangy kokum, coconut and Byadgi chili gravy"},
				{ID: "m_fd4467", FoodID: "fd4467", Name: "Butter Garlic Prawns", Category: "Seafood", Price: 320, IsVeg: false, Description: "Fresh wild tiger prawns seared in clarified golden desi butter, roasted garlic slivers and parsley"},
				{ID: "m_fd41301", FoodID: "fd41301", Name: "Fish 65 Dry", Category: "Seafood", Price: 84, IsVeg: false, Description: "Crisp golden fried fish fillets tossed with curry leaves, ginger-garlic paste and crushed peppers"},
			},
		},
		{
			ID:          "407261",
			Name:        "Shiraz Golden Restaurant",
			City:        "Kolkata",
			Cuisine:     "Biryani, Mughlai",
			Rating:      4.2,
			RatingCount: 31000,
			CostForTwo:  600,
			Address:     "Park Street, Central Kolkata",
			ImageURL:    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd46293", FoodID: "fd46293", Name: "Mutton Tikka", Category: "Mughlai", Price: 233, IsVeg: false, Description: "Authentic Lakehouse item [fd46293] with 180 verified orders in Kolkata."},
				{ID: "m_fd4224", FoodID: "fd4224", Name: "Chicken Mughlai", Category: "Mughlai", Price: 320, IsVeg: false, Description: "Authentic Lakehouse item [fd4224] with verified orders in Kolkata."},
				{ID: "m_fd4403", FoodID: "fd4403", Name: "Mughlai Paneer", Category: "Mughlai", Price: 240, IsVeg: true, Description: "Authentic Lakehouse item [fd4403] with verified orders in Kolkata."},
			},
		},
		{
			ID:          "525247",
			Name:        "Olio - The Wood Fired Pizzeria",
			City:        "Bangalore",
			Cuisine:     "Pizzas",
			Rating:      4.0,
			RatingCount: 16800,
			CostForTwo:  400,
			Address:     "Indiranagar 100ft Road, Bangalore",
			ImageURL:    "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd50845", FoodID: "fd50845", Name: "Queen Margherita Pizza", Category: "Pizzas", Price: 219, IsVeg: true, Description: "Authentic Lakehouse item [fd50845] with 40 verified orders in Bangalore."},
				{ID: "m_fd80786", FoodID: "fd80786", Name: "Peri Peri Chicken Pizza", Category: "Pizzas", Price: 299, IsVeg: false, Description: "Authentic Lakehouse item [fd80786] with 39 verified orders in Bangalore."},
				{ID: "m_fd109", FoodID: "fd109", Name: "Peri Peri Paneer Pizza", Category: "Pizzas", Price: 319, IsVeg: true, Description: "Authentic Lakehouse item [fd109] with 34 verified orders in Bangalore."},
			},
		},
		{
			ID:          "68144",
			Name:        "WarmOven Cakes & Desserts",
			City:        "Bangalore",
			Cuisine:     "Desserts, Bakery",
			Rating:      4.2,
			RatingCount: 24000,
			CostForTwo:  300,
			Address:     "Koramangala 4th Block, Bangalore",
			ImageURL:    "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_fd347086", FoodID: "fd347086", Name: "Classic Black Forest Pastry", Category: "Desserts", Price: 69, IsVeg: true, Description: "Authentic Lakehouse item [fd347086] with 21 verified orders in Bangalore."},
				{ID: "m_fd803484", FoodID: "fd803484", Name: "Black Forest Bento Cake", Category: "Desserts", Price: 299, IsVeg: true, Description: "Authentic Lakehouse item [fd803484] with 20 verified orders in Bangalore."},
				{ID: "m_fd800682", FoodID: "fd800682", Name: "Dark Chocolate Pinata Heart Cake", Category: "Desserts", Price: 999, IsVeg: true, Description: "Authentic Lakehouse item [fd800682] with 20 verified orders in Bangalore."},
			},
		},
	}

	for _, rst := range sampleRestaurants {
		r.restaurants[rst.ID] = rst
	}
}

func (r *MemoryCatalogRepository) ListRestaurants(ctx context.Context, filter domain.RestaurantFilter) ([]domain.Restaurant, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]domain.Restaurant, 0)
	for _, rst := range r.restaurants {
		if filter.City != "" && !strings.EqualFold(rst.City, filter.City) {
			continue
		}
		if filter.Cuisine != "" && !strings.Contains(strings.ToLower(rst.Cuisine), strings.ToLower(filter.Cuisine)) {
			continue
		}
		if filter.MinRating > 0 && rst.Rating < filter.MinRating {
			continue
		}
		// Exclude full menu in list view for performance (Principal microservices optimization)
		summary := *rst
		summary.Menu = nil
		result = append(result, summary)

		if filter.Limit > 0 && len(result) >= filter.Limit {
			break
		}
	}
	return result, nil
}

func (r *MemoryCatalogRepository) GetRestaurantByID(ctx context.Context, id string) (*domain.Restaurant, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	rst, exists := r.restaurants[id]
	if !exists {
		return nil, nil
	}
	copy := *rst
	return &copy, nil
}

func (r *MemoryCatalogRepository) GetMenuByRestaurantID(ctx context.Context, restaurantID string) ([]domain.MenuItem, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	rst, exists := r.restaurants[restaurantID]
	if !exists {
		return nil, nil
	}
	items := make([]domain.MenuItem, len(rst.Menu))
	copy(items, rst.Menu)
	return items, nil
}
