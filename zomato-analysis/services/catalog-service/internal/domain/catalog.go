package domain

type MenuItem struct {
	ID          string  `json:"id"`
	FoodID      string  `json:"food_id"`
	Name        string  `json:"name"`
	Category    string  `json:"category"`
	Price       float64 `json:"price"`
	IsVeg       bool    `json:"is_veg"`
	Description string  `json:"description"`
}

type Restaurant struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	City        string     `json:"city"`
	Cuisine     string     `json:"cuisine"`
	Rating      float64    `json:"rating"`
	RatingCount int        `json:"rating_count"`
	CostForTwo  float64    `json:"cost_for_two"`
	Address     string     `json:"address"`
	ImageURL    string     `json:"image_url"`
	Menu        []MenuItem `json:"menu,omitempty"`
}

type RestaurantFilter struct {
	City      string
	Cuisine   string
	MinRating float64
	Limit     int
}
