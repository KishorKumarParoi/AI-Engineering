with food as (
    select * from {{ ref('stg_food') }}
)

select
    food_id,
    food_name,
    veg_or_non_veg
from food
