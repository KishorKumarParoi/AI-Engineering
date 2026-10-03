{% snapshot snap_users %}

{{
    config(
        target_schema='SNAPSHOTS',
        unique_key='customer_id',
        strategy='check',
        check_cols=[
            'customer_name',
            'email',
            'age',
            'gender',
            'marital_status',
            'occupation',
            'income_band',
            'education',
            'family_size'
        ],
        invalidate_hard_deletes=true
    )
}}

select * from {{ ref('stg_users') }}

{% endsnapshot %}
