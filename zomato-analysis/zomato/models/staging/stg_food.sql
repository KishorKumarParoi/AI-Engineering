with source as (
    select * from {{ source('raw', 'food') }}
),

renamed as (
    select
        trim(f_id) as f_id,
        trim(f_id) as food_id,
        trim(item) as food_name,
        initcap(trim(veg_or_non_veg)) as veg_or_non_veg
    from source
    where f_id is not null and f_id != ''
)

select * from renamed
