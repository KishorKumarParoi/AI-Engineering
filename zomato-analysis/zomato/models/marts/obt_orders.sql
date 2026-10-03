{{ config(
    materialized='table',
    schema='marts',
    tags=['marts', 'obt']
) }}

/*
========================================================================================
   ZOMATO ENTERPRISE ONE BIG TABLE (OBT) - DENORMALIZED ANALYTICAL BASE
   Consolidates fct_orders + dim_restaurants + dim_customers + stg_reviews.
   Ideal for:
     1. Text-to-SQL AI Assistant (Zero-join natural language querying)
     2. High-speed Streamlit / BI dashboard aggregations
     3. Customer cohort and delivery SLA drill-downs
========================================================================================
*/

with orders as (
    select * from {{ ref('fct_orders') }}
),

restaurants as (
    select * from {{ ref('dim_restaurants') }}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

reviews as (
    select 
        order_id,
        rating as review_rating,
        comment as review_comment,
        review_date
    from {{ ref('stg_reviews') }}
)

select
    -- Order Fact Attributes
    o.order_id,
    o.order_timestamp,
    o.order_date,
    o.order_status,
    o.is_delivered,
    o.payment_method,
    o.currency,
    o.delivery_time_min,
    
    -- Financial Metrics
    o.items_count,
    o.sales_qty,
    o.subtotal,
    o.discount,
    o.delivery_fee,
    o.gst,
    o.sales_amount,
    
    -- Restaurant Dimension Attributes
    r.restaurant_id,
    r.restaurant_name,
    r.city as restaurant_city,
    r.cuisine as restaurant_cuisine,
    r.rating as restaurant_avg_rating,
    r.rating_count as restaurant_rating_count,
    r.cost_for_two as restaurant_cost_for_two,
    r.address as restaurant_address,
    
    -- Customer Dimension Attributes
    c.customer_id,
    c.customer_name,
    c.email as customer_email,
    c.age as customer_age,
    c.generation_cohort as customer_generation,
    c.age_segment as customer_age_segment,
    c.gender as customer_gender,
    c.marital_status as customer_marital_status,
    c.occupation as customer_occupation,
    c.income_band as customer_income_band,
    c.education as customer_education,
    c.family_size as customer_family_size,
    
    -- Customer Feedback / Review Attributes
    rev.review_rating,
    rev.review_comment,
    rev.review_date,
    
    -- Ingestion Metadata
    current_timestamp() as dbt_loaded_at

from orders o
left join restaurants r
    on o.restaurant_id = r.restaurant_id
    and r.is_current = true
left join customers c
    on o.customer_id = c.customer_id
    and c.is_current = true
left join reviews rev
    on o.order_id = rev.order_id
