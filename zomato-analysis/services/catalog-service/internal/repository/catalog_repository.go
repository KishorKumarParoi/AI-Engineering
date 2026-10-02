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
			ID:          "rest_bangalore_01",
			Name:        "Truffles",
			City:        "Bangalore",
			Cuisine:     "American, Burgers, Continental",
			Rating:      4.6,
			RatingCount: 14200,
			CostForTwo:  600,
			Address:     "St. Marks Road, Central Bangalore",
			ImageURL:    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_1", FoodID: "f_101", Name: "All American Cheese Burger", Category: "Burgers", Price: 260, IsVeg: false, Description: "Juicy beef/chicken patty loaded with melted English cheddar"},
				{ID: "m_2", FoodID: "f_102", Name: "Peri Peri Chicken Steak", Category: "Mains", Price: 340, IsVeg: false, Description: "Grilled breast served with herb butter rice and grilled veggies"},
				{ID: "m_3", FoodID: "f_103", Name: "Crispy Paneer Burger", Category: "Burgers", Price: 220, IsVeg: true, Description: "Crunchy crumb-coated paneer steak with spicy chipotle mayo"},
				{ID: "m_4", FoodID: "f_104", Name: "Dutch Truffle Cake Slice", Category: "Desserts", Price: 160, IsVeg: true, Description: "Dense Belgian dark chocolate layer cake"},
			},
		},
		{
			ID:          "rest_bangalore_02",
			Name:        "Empire Restaurant",
			City:        "Bangalore",
			Cuisine:     "North Indian, Biryani, Mughlai",
			Rating:      4.3,
			RatingCount: 22000,
			CostForTwo:  550,
			Address:     "Indiranagar 100ft Road",
			ImageURL:    "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_5", FoodID: "f_201", Name: "Empire Special Chicken Biryani", Category: "Biryani", Price: 290, IsVeg: false, Description: "Fragrant basmati rice layered with spiced marinated chicken"},
				{ID: "m_6", FoodID: "f_202", Name: "Butter Garlic Naan", Category: "Breads", Price: 65, IsVeg: true, Description: "Clay oven baked flatbread brushed with garlic butter"},
				{ID: "m_7", FoodID: "f_203", Name: "Paneer Butter Masala", Category: "Curries", Price: 240, IsVeg: true, Description: "Fresh cottage cheese cubes in rich tomato cashew gravy"},
				{ID: "m_8", FoodID: "f_204", Name: "Chicken Ghee Roast", Category: "Starters", Price: 310, IsVeg: false, Description: "Traditional Mangalorean fiery red spiced chicken in pure ghee"},
			},
		},
		{
			ID:          "rest_mumbai_01",
			Name:        "Bastian Mumbai",
			City:        "Mumbai",
			Cuisine:     "Seafood, Asian, Desserts",
			Rating:      4.7,
			RatingCount: 9800,
			CostForTwo:  2200,
			Address:     "Bandra West, Mumbai",
			ImageURL:    "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_9", FoodID: "f_301", Name: "Butter Garlic Crab Meat", Category: "Seafood", Price: 850, IsVeg: false, Description: "Fresh mud crab tossed in clarified butter, roasted garlic, and scallions"},
				{ID: "m_10", FoodID: "f_302", Name: "Salmon Tartare Bowl", Category: "Raw Bar", Price: 720, IsVeg: false, Description: "Norwegian salmon, avocado relish, sesame ponzu dressing"},
				{ID: "m_11", FoodID: "f_303", Name: "Truffle Edamame Dim Sum", Category: "Appetizers", Price: 490, IsVeg: true, Description: "Steamed crystal dumplings with edamame puree and white truffle oil"},
			},
		},
		{
			ID:          "rest_delhi_01",
			Name:        "Karim's Historic Mughlai",
			City:        "Delhi",
			Cuisine:     "Mughlai, Kebabs, Rolls",
			Rating:      4.5,
			RatingCount: 31000,
			CostForTwo:  800,
			Address:     "Gali Kababian, Jama Masjid, Old Delhi",
			ImageURL:    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop",
			Menu: []domain.MenuItem{
				{ID: "m_12", FoodID: "f_401", Name: "Mutton Seekh Kebab", Category: "Kebabs", Price: 320, IsVeg: false, Description: "Skewered minced spiced mutton char-grilled over hot coals"},
				{ID: "m_13", FoodID: "f_402", Name: "Karim's Nihari Gosht", Category: "Curries", Price: 410, IsVeg: false, Description: "Slow-cooked shank stew with aromatic bone marrow gravy"},
				{ID: "m_14", FoodID: "f_403", Name: "Shahi Khameeri Roti", Category: "Breads", Price: 45, IsVeg: true, Description: "Traditional fluffy leavened bread"},
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
