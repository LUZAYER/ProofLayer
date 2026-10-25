"""Declarative YAML policy schema, validation, and serialization."""

from __future__ import annotations

from typing import Literal

import jsonschema
import yaml
from pydantic import BaseModel, Field

POLICY_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ProofLayerPolicy",
    "type": "object",
    "required": ["version", "id", "name", "mode", "tools"],
    "properties": {
        "version": {"type": "string"},
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "mode": {"type": "string", "enum": ["enforce", "monitor", "shadow"]},
        "detector_thresholds": {
            "type": "object",
            "properties": {
                "block_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "approval_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        },
        "tools": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["allow", "deny", "require_approval"]},
                    "max_amount_per_call": {"type": "number"},
                    "max_amount_per_session": {"type": "number"},
                    "approval_threshold_amount": {"type": "number"},
                    "allowed_recipient_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "forbid_sensitive_data_in_arguments": {"type": "boolean"},
                },
            },
        },
        "provenance_rules": {
            "type": "object",
            "properties": {
                "disallow_untrusted_tool_triggers": {"type": "boolean"},
                "require_user_intent_match": {"type": "boolean"},
            },
        },
        "data_flow_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source_tag", "sink_tool", "action"],
                "properties": {
                    "source_tag": {"type": "string"},
                    "sink_tool": {"type": "string"},
                    "sink_field": {"type": "string"},
                    "action": {"type": "string", "enum": ["block", "require_approval", "redact"]},
                },
            },
        },
    },
}


class ToolConstraint(BaseModel):
    action: Literal["allow", "deny", "require_approval"] = "allow"
    max_amount_per_call: float | None = None
    max_amount_per_session: float | None = None
    approval_threshold_amount: float | None = None
    allowed_recipient_domains: list[str] = Field(default_factory=list)
    forbid_sensitive_data_in_arguments: bool = True


class DataFlowRule(BaseModel):
    source_tag: str
    sink_tool: str
    sink_field: str | None = None
    action: Literal["block", "require_approval", "redact"] = "block"


class DetectorThresholds(BaseModel):
    block_score: float = 0.70
    approval_score: float = 0.35


class ProvenanceRules(BaseModel):
    disallow_untrusted_tool_triggers: bool = True
    require_user_intent_match: bool = True


class PolicyDefinition(BaseModel):
    version: str = "1.0.0"
    id: str
    name: str
    description: str = ""
    mode: Literal["enforce", "monitor", "shadow"] = "enforce"
    detector_thresholds: DetectorThresholds = Field(default_factory=DetectorThresholds)
    tools: dict[str, ToolConstraint] = Field(default_factory=dict)
    provenance_rules: ProvenanceRules = Field(default_factory=ProvenanceRules)
    data_flow_rules: list[DataFlowRule] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> PolicyDefinition:
        """Parse and validate YAML against JSONSchema and Pydantic."""
        raw_data = yaml.safe_load(yaml_content)
        jsonschema.validate(instance=raw_data, schema=POLICY_JSON_SCHEMA)
        return cls(**raw_data)

    def to_yaml(self) -> str:
        """Dump policy to canonical YAML string."""
        data = self.model_dump(exclude_none=True)
        return yaml.dump(data, sort_keys=False)
