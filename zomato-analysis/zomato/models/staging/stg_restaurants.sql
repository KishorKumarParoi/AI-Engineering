with source as (
    select * from {{ source('raw', 'restaurants') }}
),

renamed as (
    select
        id::number as restaurant_id,
        trim(name) as restaurant_name,
        trim(coalesce(regexp_substr(city, '[^,]+$'), city)) as city,
        try_to_decimal(nullif(trim(rating), '--'), 3, 1) as rating,
        try_to_number(regexp_substr(rating_count, '[0-9]+')) as rating_count,
        try_to_number(regexp_substr(cost, '[0-9]+')) as cost_for_two,
        trim(cuisine) as cuisine,
        trim(lic_no) as license_number,
        trim(address) as address,
        trim(link) as restaurant_url
    from source
    where try_to_number(id) is not null
)

select * from renamed
