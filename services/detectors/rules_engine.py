"""YAML-driven multilingual rules engine with ReDoS safety and evidence extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RuleMatch:
    """Represents a single rule match with evidence span and metadata."""

    rule_id: str
    category: str
    severity: str
    rationale: str
    owasp_mapping: str
    language: str
    matched_text: str
    start: int
    end: int


@dataclass
class RulesEvaluationResult:
    """Result of running rule packs on input text."""

    matches: list[RuleMatch] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    max_severity: str = "NONE"
    rule_score: float = 0.0  # 0.0 to 1.0


SEVERITY_WEIGHTS = {
    "CRITICAL": 1.0,
    "HIGH": 0.8,
    "MEDIUM": 0.5,
    "LOW": 0.2,
    "NONE": 0.0,
}


class RulesEngine:
    """Loads and executes declarative regex rules with length bounding."""

    def __init__(self, rules_dir: Path | str | None = None) -> None:
        if rules_dir is None:
            rules_dir = Path(__file__).parent / "rules"
        self.rules_dir = Path(rules_dir)
        self.rules: list[dict[str, Any]] = []
        self._compiled_rules: list[tuple[dict[str, Any], re.Pattern[str]]] = []
        self.load_rules()

    def load_rules(self) -> None:
        """Load all YAML rule files from rules directory."""
        self.rules.clear()
        self._compiled_rules.clear()

        if not self.rules_dir.exists():
            return

        for yaml_path in sorted(self.rules_dir.glob("*.yaml")):
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data or "rules" not in data:
                    continue
                for r in data["rules"]:
                    self.rules.append(r)
                    try:
                        compiled = re.compile(r["pattern"])
                        self._compiled_rules.append((r, compiled))
                    except re.error as e:
                        # Log and skip invalid regex to maintain resilience
                        print(f"Warning: Failed to compile rule {r.get('id')}: {e}")

    def evaluate(self, text: str, max_eval_length: int = 16384) -> RulesEvaluationResult:
        """Evaluate text against all compiled rules, returning matched evidence spans."""
        if not text:
            return RulesEvaluationResult()

        eval_text = text[:max_eval_length]
        matches: list[RuleMatch] = []
        categories_set: set[str] = set()
        highest_weight = 0.0
        highest_severity = "NONE"

        for rule, pattern in self._compiled_rules:
            # Find all non-overlapping matches
            for m in pattern.finditer(eval_text):
                category = rule.get("category", "UNKNOWN")
                severity = rule.get("severity", "MEDIUM")
                categories_set.add(category)

                weight = SEVERITY_WEIGHTS.get(severity, 0.5)
                if weight > highest_weight:
                    highest_weight = weight
                    highest_severity = severity

                matches.append(
                    RuleMatch(
                        rule_id=rule["id"],
                        category=category,
                        severity=severity,
                        rationale=rule.get("rationale", ""),
                        owasp_mapping=rule.get("owasp_mapping", "LLM01:2025-Prompt-Injection"),
                        language=rule.get("languages", ["all"])[0],
                        matched_text=m.group(0),
                        start=m.start(),
                        end=m.end(),
                    )
                )

        # Compute composite rule score based on number and severity of matches
        if matches:
            # Base is highest weight, bumped slightly for multiple distinct rules
            rule_score = min(1.0, highest_weight + (len(matches) - 1) * 0.05)
        else:
            rule_score = 0.0

        return RulesEvaluationResult(
            matches=matches,
            categories=sorted(categories_set),
            max_severity=highest_severity,
            rule_score=rule_score,
        )
