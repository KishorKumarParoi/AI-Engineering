"""
Zomato Enterprise Lakehouse: Slowly Changing Dimension (SCD) Processor
Principal Data Engineer Standard
Implements atomic SCD Type 1 (in-place) and SCD Type 2 (historical versioning) using Delta Lake ACID MERGE.
"""

from typing import Dict, Any, List
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable
from .metadata_parser import EntityConfig, SCDConfig

class SCDProcessor:
    @staticmethod
    def compute_row_hash(df: DataFrame, columns_to_hash: List[str], hash_col_name: str = "row_hash") -> DataFrame:
        """
        Calculates a deterministic SHA-256 hash over specified columns.
        Handles null values consistently to avoid false change detections.
        """
        valid_cols = [c for c in columns_to_hash if c in df.columns]
        if not valid_cols:
            return df.withColumn(hash_col_name, F.sha2(F.lit("EMPTY"), 256))

        hash_exprs = [
            F.coalesce(F.col(c).cast("string"), F.lit("__NULL__"))
            for c in valid_cols
        ]
        concat_expr = F.concat_ws("||", *hash_exprs)
        return df.withColumn(hash_col_name, F.sha2(concat_expr, 256))

    @classmethod
    def apply_scd_type_1(cls, spark: SparkSession, source_df: DataFrame, entity_cfg: EntityConfig) -> Dict[str, Any]:
        """
        SCD Type 1: In-Place Overwrite (Upsert)
        Updates existing matching records and inserts new ones. Does not retain historical versions.
        """
        scd_cfg = entity_cfg.scd_config
        target_path = entity_cfg.target.path
        pks = scd_cfg.primary_keys
        hash_col = scd_cfg.hash_col

        # 1. Compute hash on incoming source
        src_hashed = cls.compute_row_hash(source_df, scd_cfg.tracked_columns, hash_col)
        src_hashed = src_hashed.withColumn(scd_cfg.effective_from_col, F.current_timestamp())

        # 2. Check if target Delta table exists
        if not DeltaTable.isDeltaTable(spark, target_path):
            print(f"[+] [SCD-1] Initializing target Delta table at: {target_path}")
            writer = src_hashed.write.format("delta").mode("overwrite")
            if entity_cfg.target.partition_by:
                writer = writer.partitionBy(*entity_cfg.target.partition_by)
            writer.save(target_path)
            init_count = src_hashed.count()
            return {"status": "INITIALIZED", "inserted": init_count, "updated": 0, "unchanged": 0}

        # 3. Perform Delta Lake MERGE INTO
        target_table = DeltaTable.forPath(spark, target_path)
        join_cond = " AND ".join([f"tgt.{k} = src.{k}" for k in pks])

        update_set = {col: f"src.{col}" for col in src_hashed.columns}
        insert_set = {col: f"src.{col}" for col in src_hashed.columns}

        print(f"[+] [SCD-1] Merging source into target table on ({join_cond})...")
        (
            target_table.alias("tgt")
            .merge(
                source=src_hashed.alias("src"),
                condition=join_cond
            )
            .whenMatchedUpdate(
                condition=f"tgt.{hash_col} != src.{hash_col}",
                set=update_set
            )
            .whenNotMatchedInsert(
                values=insert_set
            )
            .execute()
        )

        final_count = target_table.toDF().count()
        return {"status": "MERGED_SCD1", "total_records": final_count}

    @classmethod
    def apply_scd_type_2(cls, spark: SparkSession, source_df: DataFrame, entity_cfg: EntityConfig) -> Dict[str, Any]:
        """
        SCD Type 2: Historical Change Tracking with Surrogate Keys
        Closes superseded active records (is_current = false, valid_to = current_ts)
        and inserts new versions (is_current = true, valid_from = current_ts, valid_to = 9999-12-31).
        """
        scd_cfg = entity_cfg.scd_config
        target_path = entity_cfg.target.path
        pks = scd_cfg.primary_keys
        tracked_cols = scd_cfg.tracked_columns
        sk_col = scd_cfg.surrogate_key or f"{pks[0]}_sk"
        from_col = scd_cfg.effective_from_col
        to_col = scd_cfg.effective_to_col
        current_col = scd_cfg.is_current_col
        hash_col = scd_cfg.hash_col
        future_date = scd_cfg.future_date_literal

        # 1. Compute hash on incoming source
        src_hashed = cls.compute_row_hash(source_df, tracked_cols, hash_col)

        # 2. If target Delta table does not exist, initialize with version 1
        if not DeltaTable.isDeltaTable(spark, target_path):
            print(f"[+] [SCD-2] Initializing target Delta table at: {target_path}")
            init_df = (
                src_hashed
                .withColumn(
                    sk_col,
                    F.sha2(F.concat_ws("::", *[F.col(k) for k in pks], F.current_timestamp().cast("string")), 256)
                )
                .withColumn(from_col, F.current_timestamp())
                .withColumn(to_col, F.to_timestamp(F.lit(future_date)))
                .withColumn(current_col, F.lit(True))
            )

            writer = init_df.write.format("delta").mode("overwrite")
            if entity_cfg.target.partition_by:
                writer = writer.partitionBy(*entity_cfg.target.partition_by)
            writer.save(target_path)
            init_count = init_df.count()
            return {"status": "INITIALIZED_SCD2", "inserted": init_count, "expired": 0, "active": init_count}

        target_table = DeltaTable.forPath(spark, target_path)
        current_target_df = target_table.toDF().filter(F.col(current_col) == True)

        # 3. Identify record differences between incoming source and current target
        # Join condition on primary keys
        join_cond = [src_hashed[k] == current_target_df[k] for k in pks]

        matched_df = src_hashed.alias("s").join(
            current_target_df.alias("t"),
            on=join_cond,
            how="left"
        ).select(
            *[F.col(f"s.{c}").alias(c) for c in src_hashed.columns],
            F.col(f"t.{hash_col}").alias("target_hash"),
            F.col(f"t.{pks[0]}").alias("target_pk_check")
        )

        # Determine categorization:
        # A) NEW: target_pk_check is null -> insert
        # B) CHANGED: target_pk_check is not null AND target_hash != row_hash -> expire old, insert new
        # C) UNCHANGED: target_hash == row_hash -> do nothing
        changed_or_new = matched_df.filter(
            F.col("target_pk_check").isNull() | (F.col("target_hash") != F.col(hash_col))
        )

        change_count = changed_or_new.count()
        if change_count == 0:
            print("[*] [SCD-2] No changes or new records detected. Target table remains up to date.")
            active_cnt = current_target_df.count()
            return {"status": "NO_CHANGES", "inserted": 0, "expired": 0, "active": active_cnt}

        print(f"[*] [SCD-2] Detected {change_count} changed or new records. Building Delta MERGE stage...")

        now_ts = F.current_timestamp()

        # Step A: Rows to EXPIRE existing active records in target (merge_key = primary_key)
        records_to_expire = (
            changed_or_new
            .filter(F.col("target_pk_check").isNotNull())
            .select(*[F.col(k) for k in pks])
            .withColumn("merge_key", F.col(pks[0]))
            .withColumn("stage_action", F.lit("EXPIRE"))
        )

        # Step B: Rows to INSERT (new version or brand new record, merge_key = NULL)
        records_to_insert = (
            changed_or_new
            .drop("target_hash", "target_pk_check")
            .withColumn("merge_key", F.lit(None).cast("string"))
            .withColumn("stage_action", F.lit("INSERT"))
            .withColumn(
                sk_col,
                F.sha2(F.concat_ws("::", *[F.col(k) for k in pks], now_ts.cast("string")), 256)
            )
            .withColumn(from_col, now_ts)
            .withColumn(to_col, F.to_timestamp(F.lit(future_date)))
            .withColumn(current_col, F.lit(True))
        )

        # Step C: Union into staged dataset for the atomic MERGE
        # Harmonize schemas for union
        dummy_insert_cols = {col: F.lit(None) for col in records_to_insert.columns if col not in records_to_expire.columns}
        staged_expire = records_to_expire
        for c, expr in dummy_insert_cols.items():
            staged_expire = staged_expire.withColumn(c, expr)

        staged_union = records_to_insert.select(*staged_expire.columns).unionByName(staged_expire)

        # Step D: Execute atomic Delta Lake MERGE
        merge_cond = f"tgt.{pks[0]} = stg.merge_key AND tgt.{current_col} = true"
        print(f"[+] [SCD-2] Executing atomic MERGE on target ({merge_cond})...")

        insert_map = {col: f"stg.{col}" for col in records_to_insert.columns if col != "merge_key" and col != "stage_action"}

        (
            target_table.alias("tgt")
            .merge(
                source=staged_union.alias("stg"),
                condition=merge_cond
            )
            .whenMatchedUpdate(
                condition="stg.stage_action = 'EXPIRE'",
                set={
                    current_col: F.lit(False),
                    to_col: now_ts
                }
            )
            .whenNotMatchedInsert(
                values=insert_map
            )
            .execute()
        )

        total_records = target_table.toDF().count()
        active_records = target_table.toDF().filter(F.col(current_col) == True).count()
        historical_records = total_records - active_records

        print(f"[✓] [SCD-2] Merge complete: Total={total_records}, Active={active_records}, Historical Versions={historical_records}")
        return {
            "status": "MERGED_SCD2",
            "total_records": total_records,
            "active_records": active_records,
            "historical_records": historical_records
        }
