with restaurants as (
    select * from {{ ref('stg_restaurants') }}
)

select
    restaurant_id,
    restaurant_name,
    city,
    rating,
    rating_count,
    cost_for_two,
    cuisine,
    license_number,
    address,
    restaurant_url
from restaurants
