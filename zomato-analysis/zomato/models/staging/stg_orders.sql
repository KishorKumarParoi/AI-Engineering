with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        order_id,
        order_timestamp,
        order_date,
        user_id as customer_id,
        r_id as restaurant_id,
        trim(coalesce(regexp_substr(restaurant_city, '[^,]+$'), restaurant_city)) as city,
        trim(cuisine) as cuisine,
        items_count,
        sales_qty,
        subtotal,
        discount,
        delivery_fee,
        gst,
        sales_amount,
        trim(currency) as currency,
        trim(payment_method) as payment_method,
        trim(order_status) as order_status,
        (trim(order_status) = 'Delivered') as is_delivered,
        customer_rating,
        delivery_time_min
    from source
    where order_id is not null
)

select * from renamed
