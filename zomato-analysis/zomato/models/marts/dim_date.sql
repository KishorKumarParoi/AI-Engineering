with spine as (
    select dateadd(day, seq4(), '2024-01-01'::date) as date_day
    from table(generator(rowcount => 1200))
)

select
    date_day,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    monthname(date_day) as month_name,
    extract(day from date_day) as day_of_month,
    dayname(date_day) as day_name,
    case when dayofweekiso(date_day) in (6, 7) then true else false end as is_weekend
from spine
where date_day <= '2026-12-31'
order by date_day
