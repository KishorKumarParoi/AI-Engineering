with source as (
    select * from {{ source('raw', 'users') }}
),

renamed as (
    select
        user_id::number as customer_id,
        trim(name) as customer_name,
        lower(trim(email)) as email,
        try_to_number(age) as age,
        trim(gender) as gender,
        trim(marital_status) as marital_status,
        trim(occupation) as occupation,
        trim(monthly_income) as income_band,
        trim(education) as education,
        try_to_number(family_size) as family_size
    from source
    where try_to_number(user_id) is not null
)

select * from renamed
