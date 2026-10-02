with orders as (
    select * from {{ ref('fct_orders') }}
)

select
    order_date,
    city,
    count(*) as total_orders,
    count_if(is_delivered) as delivered_orders,
    count_if(order_status = 'Cancelled') as cancelled_orders,
    round(div0(count_if(order_status = 'Cancelled'), count(*)), 4) as cancel_rate,
    sum(iff(is_delivered, sales_amount, 0)) as gmv,
    round(div0(sum(iff(is_delivered, sales_amount, 0)), count_if(is_delivered)), 2) as aov,
    sum(discount) as total_discounts_given,
    sum(delivery_fee) as total_delivery_fees,
    round(avg(iff(is_delivered, delivery_time_min, null)), 1) as avg_delivery_time_mins
from orders
group by 1, 2
