with orders as (
    select * from {{ ref('fct_orders') }}
),

restaurants as (
    select * from {{ ref('dim_restaurants') }}
),

restaurant_orders as (
    select
        restaurant_id,
        count(*) as total_orders,
        count_if(is_delivered) as delivered_orders,
        sum(iff(is_delivered, sales_amount, 0)) as total_revenue,
        round(avg(iff(is_delivered, delivery_time_min, null)), 1) as avg_delivery_time_mins,
        round(avg(customer_rating), 2) as avg_customer_rating
    from orders
    group by 1
)

select
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    r.cuisine,
    r.rating as catalog_rating,
    r.cost_for_two,
    coalesce(ro.total_orders, 0) as total_orders,
    coalesce(ro.delivered_orders, 0) as delivered_orders,
    coalesce(ro.total_revenue, 0) as total_revenue,
    ro.avg_delivery_time_mins,
    ro.avg_customer_rating
from restaurants r
left join restaurant_orders ro
    on r.restaurant_id = ro.restaurant_id
