with orders as (
    select * from {{ ref('fct_orders') }}
    where is_delivered = true
      and delivery_time_min is not null
)

select
    city,
    hour(order_timestamp) as order_hour,
    count(*) as total_delivered_orders,
    round(median(delivery_time_min), 1) as p50_delivery_time_mins,
    round(percentile_cont(0.9) within group (order by delivery_time_min), 1) as p90_delivery_time_mins,
    round(avg(delivery_time_min), 1) as avg_delivery_time_mins,
    min(delivery_time_min) as min_delivery_time_mins,
    max(delivery_time_min) as max_delivery_time_mins,
    count_if(delivery_time_min <= 30) as under_30_mins_count,
    count_if(delivery_time_min > 45) as delayed_over_45_mins_count,
    round(count_if(delivery_time_min <= 30) * 100.0 / nullif(count(*), 0), 2) as on_time_sla_percentage
from orders
group by 1, 2
