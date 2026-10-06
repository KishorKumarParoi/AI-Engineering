"""
Zomato Enterprise Lakehouse: Typed Metadata Configuration Parser
Parses and validates pipeline_metadata.yaml according to Principal Data Engineer standards.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import yaml

@dataclass
class DataQualityRule:
    column: str
    check: str  # NOT_NULL, GREATER_THAN, BETWEEN, REGEX, UNIQUE
    description: str = ""
    value: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None

@dataclass
class SCDConfig:
    scd_type: str  # SCD_TYPE_1 or SCD_TYPE_2
    primary_keys: List[str]
    tracked_columns: List[str]
    surrogate_key: Optional[str] = None
    effective_from_col: str = "valid_from"
    effective_to_col: str = "valid_to"
    is_current_col: str = "is_current"
    hash_col: str = "row_hash"
    future_date_literal: str = "9999-12-31 23:59:59"

@dataclass
class SourceConfig:
    format: str  # parquet, jsonl, csv, delta
    default_path: str
    schema_mode: str = "infer_or_evolve"

@dataclass
class TargetConfig:
    layer: str  # bronze, silver, gold
    table_name: str
    format: str = "delta"
    path: str = ""
    partition_by: List[str] = field(default_factory=list)

@dataclass
class EntityConfig:
    entity_id: str
    description: str
    source: SourceConfig
    target: TargetConfig
    scd_config: SCDConfig
    data_quality_rules: List[DataQualityRule] = field(default_factory=list)
    dq_enabled: bool = True
    dq_on_violation: str = "QUARANTINE"  # QUARANTINE, DROP, FAIL

class MetadataRegistry:
    def __init__(self, metadata_path: Optional[str] = None):
        if metadata_path is None:
            project_root = Path(__file__).resolve().parents[2]
            metadata_path = str(project_root / "databricks" / "metadata" / "pipeline_metadata.yaml")
        
        self.metadata_path = metadata_path
        self.config_data = self._load_yaml()
        self.entities: Dict[str, EntityConfig] = self._parse_entities()

    def _load_yaml(self) -> Dict[str, Any]:
        with open(self.metadata_path, "r") as f:
            return yaml.safe_load(f)

    def _parse_entities(self) -> Dict[str, EntityConfig]:
        entities_dict = {}
        project_root = Path(__file__).resolve().parents[2]

        for item in self.config_data.get("entities", []):
            eid = item["entity_id"]
            src_raw = item["source"]
            tgt_raw = item["target"]
            scd_raw = item["scd_config"]
            dq_raw = item.get("data_quality", {})

            # Resolve paths relative to project root
            src_path = src_raw["default_path"]
            if not src_path.startswith("/") and not src_path.startswith("abfss://"):
                src_path = str(project_root / src_path)

            tgt_path = tgt_raw.get("path", "")
            if tgt_path and not tgt_path.startswith("/") and not tgt_path.startswith("abfss://"):
                tgt_path = str(project_root / tgt_path)

            source = SourceConfig(
                format=src_raw["format"],
                default_path=src_path,
                schema_mode=src_raw.get("schema_mode", "infer_or_evolve")
            )

            target = TargetConfig(
                layer=tgt_raw["layer"],
                table_name=tgt_raw["table_name"],
                format=tgt_raw.get("format", "delta"),
                path=tgt_path,
                partition_by=tgt_raw.get("partition_by", [])
            )

            scd = SCDConfig(
                scd_type=scd_raw["scd_type"],
                primary_keys=scd_raw["primary_keys"],
                tracked_columns=scd_raw["tracked_columns"],
                surrogate_key=scd_raw.get("surrogate_key"),
                effective_from_col=scd_raw.get("effective_from_col", "valid_from"),
                effective_to_col=scd_raw.get("effective_to_col", "valid_to"),
                is_current_col=scd_raw.get("is_current_col", "is_current"),
                hash_col=scd_raw.get("hash_col", "row_hash"),
                future_date_literal=scd_raw.get("future_date_literal", "9999-12-31 23:59:59")
            )

            dq_rules = []
            for r in dq_raw.get("rules", []):
                dq_rules.append(
                    DataQualityRule(
                        column=r["column"],
                        check=r["check"],
                        description=r.get("description", ""),
                        value=r.get("value"),
                        min=r.get("min"),
                        max=r.get("max")
                    )
                )

            entity = EntityConfig(
                entity_id=eid,
                description=item.get("description", ""),
                source=source,
                target=target,
                scd_config=scd,
                data_quality_rules=dq_rules,
                dq_enabled=dq_raw.get("enabled", True),
                dq_on_violation=dq_raw.get("on_violation", "QUARANTINE")
            )
            entities_dict[eid] = entity

        return entities_dict

    def get_entity(self, entity_id: str) -> EntityConfig:
        if entity_id not in self.entities:
            raise KeyError(f"Entity '{entity_id}' not found in metadata registry {list(self.entities.keys())}")
        return self.entities[entity_id]
