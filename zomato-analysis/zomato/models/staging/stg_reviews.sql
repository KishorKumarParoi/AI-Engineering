with source as (
    select * from {{ source('raw', 'reviews') }}
),

restaurants as (
    select restaurant_id, city from {{ ref('stg_restaurants') }}
),

renamed as (
    select
        r.review_id,
        r.order_id,
        r.user_id::number as customer_id,
        r.restaurant_id::number as restaurant_id,
        r.rating::number as rating,
        trim(r.comment) as comment,
        trim(r.comment) as review_text,
        r.review_date::date as review_date,
        res.city as city
    from source r
    left join restaurants res
        on r.restaurant_id = res.restaurant_id
    where r.review_id is not null
      and r.comment is not null
)

select * from renamed
