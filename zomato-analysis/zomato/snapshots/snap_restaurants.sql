{% snapshot snap_restaurants %}

{{
    config(
        target_schema='SNAPSHOTS',
        unique_key='restaurant_id',
        strategy='check',
        check_cols=['restaurant_name', 'city', 'rating', 'rating_count', 'cost_for_two', 'cuisine', 'license_number'],
    )
}}

select * from {{ ref('stg_restaurants') }}

{% endsnapshot %}
