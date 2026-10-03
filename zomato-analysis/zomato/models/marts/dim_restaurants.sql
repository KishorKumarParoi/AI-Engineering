with snapshot_data as (
    select * from {{ ref('snap_restaurants') }}
)

select
    -- Surrogate Key (unique for each historical version of a restaurant)
    dbt_scd_id as restaurant_sk,
    
    -- Business / Natural Key
    restaurant_id,
    
    -- Restaurant Attributes
    restaurant_name,
    city,
    rating,
    rating_count,
    cost_for_two,
    cuisine,
    license_number,
    address,
    restaurant_url,
    
    -- SCD Type 2 Timeline & Status
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    case 
        when dbt_valid_to is null then true 
        else false 
    end as is_current,
    row_number() over (
        partition by restaurant_id 
        order by dbt_valid_from asc
    ) as row_version,
    dbt_updated_at as snapshot_updated_at

from snapshot_data
