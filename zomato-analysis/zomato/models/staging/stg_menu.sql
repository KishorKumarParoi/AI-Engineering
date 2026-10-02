with source as (
    select * from {{ source('raw', 'menu') }}
),

renamed as (
    select
        trim(menu_id) as menu_id,
        try_to_number(r_id) as restaurant_id,
        trim(f_id) as f_id,
        trim(f_id) as food_id,
        trim(cuisine) as cuisine,
        try_to_decimal(price, 10, 2) as price
    from source
    where try_to_number(r_id) is not null
      and try_to_decimal(price, 10, 2) > 0
)

select * from renamed
