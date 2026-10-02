with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        order_item_id,
        order_id,
        r_id as restaurant_id,
        trim(f_id) as f_id,
        trim(f_id) as food_id,
        price::decimal(10, 2) as price,
        quantity::number as quantity,
        line_amount::decimal(10, 2) as line_amount
    from source
    where order_item_id is not null
)

select * from renamed
