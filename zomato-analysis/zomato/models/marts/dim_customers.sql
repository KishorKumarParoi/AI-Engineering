with users as (
    select * from {{ ref('stg_users') }}
)

select
    customer_id,
    customer_name,
    email,
    age,
    case
        when age < 25 then 'Gen Z'
        when age < 40 then 'Millennial'
        when age < 55 then 'Gen X'
        when age is null then 'Unknown'
        else 'Boomer'
    end as generation_cohort,
    case
        when age < 20 then 'Under 20'
        when age between 20 and 29 then '20-29'
        when age between 30 and 39 then '30-39'
        when age between 40 and 49 then '40-49'
        when age >= 50 then '50+'
        else 'Unknown'
    end as age_segment,
    gender,
    marital_status,
    occupation,
    income_band,
    education,
    family_size
from users
