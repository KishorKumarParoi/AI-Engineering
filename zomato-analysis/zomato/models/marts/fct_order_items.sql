{{ config(
    materialized='incremental',
    unique_key='order_item_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, order_timestamp, order_date, city
    from {{ ref('stg_orders') }}
),

joined as (
    select
        oi.order_item_id,
        oi.order_id,
        oi.restaurant_id,
        oi.f_id,
        oi.food_id,
        o.order_timestamp as order_ts,
        o.order_date,
        o.city,
        oi.price,
        oi.quantity,
        oi.line_amount
    from items oi
    inner join orders o
        on oi.order_id = o.order_id
    {% if is_incremental() %}
      -- 3-day lookback buffer to prevent missing delayed line items
      where o.order_timestamp > (select coalesce(dateadd('day', -3, max(order_ts)), '1900-01-01'::timestamp) from {{ this }})
    {% endif %}
)

select * from joined
