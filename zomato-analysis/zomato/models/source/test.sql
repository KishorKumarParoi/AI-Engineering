-- Pass-through of raw user profiles.
-- Explicit column list (no SELECT *): stable contract, and it keeps the
-- raw PASSWORD secret and the internal _IDX index column out of downstream.
select
    user_id,
    name,
    email,
    age,
    gender,
    marital_status,
    occupation,
    monthly_income,
    education,
    family_size
from {{ source('raw', 'users') }}
