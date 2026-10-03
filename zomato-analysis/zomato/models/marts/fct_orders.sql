{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
      -- 3-day lookback buffer catches offline/delayed syncs while unique_key='order_id' prevents duplicate rows
      where order_timestamp > (select coalesce(dateadd('day', -3, max(order_timestamp)), '1900-01-01'::timestamp) from {{ this }})
    {% endif %}
)

select
    order_id,
    order_timestamp,
    order_date,
    customer_id,
    restaurant_id,
    city,
    cuisine,
    items_count,
    sales_qty,
    subtotal,
    discount,
    delivery_fee,
    gst,
    sales_amount,
    currency,
    payment_method,
    order_status,
    is_delivered,
    customer_rating,
    delivery_time_min
from orders
