"""
Zomato Enterprise Lakehouse: Data Quality Enforcement Engine
Filters invalid records and routes them to an isolated Delta Lake quarantine sink.
"""

from typing import List, Tuple
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from .metadata_parser import DataQualityRule, EntityConfig

class DataQualityEngine:
    @staticmethod
    def evaluate(df: DataFrame, entity_cfg: EntityConfig) -> Tuple[DataFrame, DataFrame]:
        """
        Evaluates data quality rules on the incoming DataFrame.
        Returns:
            (clean_df, quarantined_df)
        """
        if not entity_cfg.dq_enabled or not entity_cfg.data_quality_rules:
            return df, df.filter(F.lit(False))

        # Build condition expressions
        violation_exprs = []

        for rule in entity_cfg.data_quality_rules:
            col_name = rule.column
            if col_name not in df.columns:
                continue

            col_ref = F.col(col_name)

            if rule.check == "NOT_NULL":
                cond = col_ref.isNull()
                reason = f"{col_name} is null"
            elif rule.check in ("GREATER_THAN", "POSITIVE"):
                val = rule.value if rule.value is not None else 0
                cond = (col_ref <= val) | col_ref.isNull()
                reason = f"{col_name} <= {val}"
            elif rule.check == "BETWEEN":
                cond = (col_ref < rule.min) | (col_ref > rule.max) | col_ref.isNull()
                reason = f"{col_name} not between [{rule.min}, {rule.max}]"
            else:
                continue

            violation_exprs.append(
                F.when(cond, F.lit(reason)).otherwise(None)
            )

        if not violation_exprs:
            return df, df.filter(F.lit(False))

        # Aggregate all violations into an array and filter out nulls
        violations_array = F.array_compact(F.array(*violation_exprs))
        
        assessed_df = df.withColumn("_dq_violations", violations_array) \
                        .withColumn("_dq_is_valid", F.size(F.col("_dq_violations")) == 0) \
                        .withColumn("_dq_evaluated_at", F.current_timestamp())

        clean_df = assessed_df.filter(F.col("_dq_is_valid")) \
                              .drop("_dq_violations", "_dq_is_valid")

        quarantined_df = assessed_df.filter(~F.col("_dq_is_valid")) \
                                    .withColumn("_quarantine_reason", F.concat_ws("; ", F.col("_dq_violations"))) \
                                    .drop("_dq_violations", "_dq_is_valid")

        return clean_df, quarantined_df
