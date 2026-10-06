"""
Zomato Enterprise Lakehouse: Metadata-Driven Pipeline Orchestrator
Reads YAML metadata, performs data quality validation, and applies SCD 1/2 transformations into Delta Lake.
"""

import time
from typing import Dict, Any, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from .spark_session import get_spark_session
from .metadata_parser import MetadataRegistry, EntityConfig
from .data_quality import DataQualityEngine
from .scd_processor import SCDProcessor

class MetadataPipelineRunner:
    def __init__(self, metadata_path: Optional[str] = None, spark: Optional[SparkSession] = None):
        self.registry = MetadataRegistry(metadata_path)
        self.spark = spark or get_spark_session()

    def load_source_dataframe(self, entity_cfg: EntityConfig, custom_path: Optional[str] = None) -> DataFrame:
        src = entity_cfg.source
        path = custom_path or src.default_path

        fmt = src.format.lower()
        print(f"[*] Reading source entity '{entity_cfg.entity_id}' [{fmt}] from: {path}")

        if fmt == "parquet":
            return self.spark.read.parquet(path)
        elif fmt == "jsonl" or fmt == "json":
            return self.spark.read.json(path)
        elif fmt == "csv":
            return self.spark.read.option("header", "true").option("inferSchema", "true").csv(path)
        elif fmt == "delta":
            return self.spark.read.format("delta").load(path)
        else:
            raise ValueError(f"Unsupported source format '{fmt}' for entity {entity_cfg.entity_id}")

    def run_entity(self, entity_id: str, custom_source_df: Optional[DataFrame] = None) -> Dict[str, Any]:
        """
        Executes end-to-end metadata-driven pipeline for a single entity:
        1. Source Read
        2. Data Quality Validation (Clean vs Quarantine)
        3. SCD Type 1 or SCD Type 2 Delta Lake Merge
        """
        start_time = time.time()
        entity_cfg = self.registry.get_entity(entity_id)
        print(f"\n======================================================================")
        print(f"🚀 PIPELINE EXECUTION: {entity_id.upper()} ({entity_cfg.scd_config.scd_type})")
        print(f"======================================================================")

        # 1. Load source
        if custom_source_df is not None:
            raw_df = custom_source_df
        else:
            raw_df = self.load_source_dataframe(entity_cfg)

        raw_count = raw_df.count()
        print(f"[+] Loaded {raw_count} raw records from source.")

        # 2. Data Quality check
        clean_df, quarantined_df = DataQualityEngine.evaluate(raw_df, entity_cfg)
        clean_count = clean_df.count()
        quarantine_count = quarantined_df.count()

        print(f"[+] Data Quality check: {clean_count} records passed, {quarantine_count} records quarantined.")

        # Save quarantined records if any exist
        if quarantine_count > 0:
            quarantine_path = f"data/lakehouse/quarantine/{entity_id}"
            print(f"[!] Routing {quarantine_count} failing records to quarantine sink: {quarantine_path}")
            quarantined_df.write.format("delta").mode("append").save(quarantine_path)

        if clean_count == 0:
            print("[Warning] No valid records remaining after Data Quality check.")
            return {
                "entity_id": entity_id,
                "status": "EMPTY_CLEAN_DATASET",
                "raw_count": raw_count,
                "clean_count": 0,
                "quarantine_count": quarantine_count,
                "elapsed_seconds": round(time.time() - start_time, 2)
            }

        # 3. Apply SCD processing
        scd_type = entity_cfg.scd_config.scd_type
        if scd_type == "SCD_TYPE_1":
            result = SCDProcessor.apply_scd_type_1(self.spark, clean_df, entity_cfg)
        elif scd_type == "SCD_TYPE_2":
            result = SCDProcessor.apply_scd_type_2(self.spark, clean_df, entity_cfg)
        else:
            raise ValueError(f"Unknown SCD Type: {scd_type}")

        elapsed = round(time.time() - start_time, 2)
        result.update({
            "entity_id": entity_id,
            "raw_count": raw_count,
            "clean_count": clean_count,
            "quarantine_count": quarantine_count,
            "elapsed_seconds": elapsed,
            "target_path": entity_cfg.target.path
        })

        print(f"[✓] Entity {entity_id} processed in {elapsed}s: {result}")
        return result

    def run_all(self) -> Dict[str, Any]:
        """Runs the pipeline for all entities configured in metadata."""
        results = {}
        for eid in self.registry.entities.keys():
            results[eid] = self.run_entity(eid)
        return results
