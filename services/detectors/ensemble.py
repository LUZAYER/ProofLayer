"""Production ensemble decision engine combining rules, ML, PII, and provenance signals."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from services.detectors.banglish import BanglishCanonicalizer
from services.detectors.classifier import InjectionClassifier
from services.detectors.normalizer import TextNormalizer
from services.detectors.pii import Finding, PIIScanner
from services.detectors.provenance import ProvenanceAnalyzer, ProvenanceTag
from services.detectors.rules_engine import RuleMatch, RulesEngine

DecisionType = Literal["ALLOW", "ALLOW_WITH_REDACTION", "REQUIRE_APPROVAL", "BLOCK"]


@dataclass
class Explanation:
    """Bilingual deterministic explanation."""

    en: str
    bn: str


@dataclass
class ScanResult:
    """Complete scan result emitted by the ProofLayer ensemble detector."""

    decision: DecisionType
    risk_score: float  # 0.0 to 1.0
    categories: list[str] = field(default_factory=list)
    rule_matches: list[RuleMatch] = field(default_factory=list)
    pii_findings: list[Finding] = field(default_factory=list)
    sanitized_text: str = ""
    spotlighted_text: str = ""
    explanation: Explanation = field(default_factory=lambda: Explanation(en="", bn=""))
    latency_ms: float = 0.0
    has_canary_leak: bool = False


class DetectorEnsemble:
    """Production-grade multilingual detector ensemble."""

    def __init__(
        self,
        rules_dir: Path | str | None = None,
        model_dir: Path | str | None = None,
        block_threshold: float = 0.70,
        approval_threshold: float = 0.35,
    ) -> None:
        self.normalizer = TextNormalizer()
        self.banglish = BanglishCanonicalizer()
        self.rules_engine = RulesEngine(rules_dir=rules_dir)
        self.classifier = InjectionClassifier()
        if model_dir:
            self.classifier.load(model_dir)
        self.pii_scanner = PIIScanner(redaction_mode="mask")
        self.provenance_analyzer = ProvenanceAnalyzer()

        self.block_threshold = block_threshold
        self.approval_threshold = approval_threshold

    def scan(
        self,
        text: str,
        provenance: ProvenanceTag = "USER",
        policy_block_threshold: float | None = None,
    ) -> ScanResult:
        """Execute full inspection pipeline and return calibrated decision."""
        start_time = time.perf_counter()

        threshold_block = policy_block_threshold or self.block_threshold

        # Stage 1: Normalisation
        norm_res = self.normalizer.normalize(text)
        normalized_text = norm_res.normalized_text

        # Stage 2: Banglish Canonicalization
        banglish_res = self.banglish.process(normalized_text)
        canonical_text = banglish_res.canonical_text

        # Stage 3: Provenance analysis & Spotlighting
        prov_analysis = self.provenance_analyzer.analyze_segment(text, provenance)

        # Stage 4: Rules evaluation (test both normalized text and canonical Banglish)
        rule_eval_1 = self.rules_engine.evaluate(normalized_text)
        rule_eval_2 = self.rules_engine.evaluate(canonical_text)

        all_matches = rule_eval_1.matches + [
            m
            for m in rule_eval_2.matches
            if m.rule_id not in {x.rule_id for x in rule_eval_1.matches}
        ]
        all_categories = sorted(set(rule_eval_1.categories + rule_eval_2.categories))
        rule_score = max(rule_eval_1.rule_score, rule_eval_2.rule_score)

        # Check for canary tokens explicitly
        has_canary = any(m.category == "CANARY_EXFILTRATION" for m in all_matches)

        # Stage 5: ML Classifier
        clf_res = self.classifier.predict(normalized_text)
        ml_score = clf_res.probability if self.classifier.is_trained else 0.0

        # Stage 6: PII and Secret Scanning
        pii_res = self.pii_scanner.scan(text)

        # Stage 7: Composite Scoring
        # Weighted combination: 55% rules, 35% ML, 10% structural/encoding anomalies
        structural_bump = 0.0
        if norm_res.has_zero_width_chars or norm_res.has_homoglyphs or norm_res.detected_encodings:
            structural_bump += 0.20
        if prov_analysis.has_untrusted_instruction:
            structural_bump += 0.40
            all_categories.append("UNTRUSTED_INSTRUCTION_IN_DOCUMENT")

        if pii_res.has_leakage:
            for f in pii_res.findings:
                if f.category == "SECRET":
                    structural_bump += 0.30
                    all_categories.append("SECRET_EXPOSURE")
                    if "CANARY" in f.entity_type:
                        has_canary = True

        # Ensemble combination: Take maximum of rule and ML scores plus structural anomalies
        base_threat = max(rule_score, ml_score * 0.95 if ml_score > 0.65 else ml_score * 0.5)
        raw_score = base_threat + structural_bump
        if ml_score >= 0.70:
            all_categories.append("ML_CLASSIFIER_ANOMALY")
        all_categories = sorted(set(all_categories))

        # If a CRITICAL rule fired or canary leaked, force risk score to >= 0.95
        if (
            rule_eval_1.max_severity == "CRITICAL"
            or rule_eval_2.max_severity == "CRITICAL"
            or has_canary
        ):
            raw_score = max(raw_score, 0.95)

        risk_score = round(min(1.0, raw_score), 4)

        # Stage 8: Decision Logic
        decision: DecisionType
        en_expl: str
        bn_expl: str

        if has_canary or risk_score >= threshold_block:
            decision = "BLOCK"
            if has_canary:
                en_expl = (
                    "Blocked: Sensitive canary token or secret credential detected in content."
                )
                bn_expl = "প্রতিরোধ করা হয়েছে: সংবেদনশীল ক্যানারি টোকেন বা গোপন তথ্য সনাক্ত হয়েছে।"
            elif prov_analysis.has_untrusted_instruction:
                en_expl = "Blocked: Untrusted document segment contains directive instructions."
                bn_expl = "প্রতিরোধ করা হয়েছে: বিশ্বস্ত নয় এমন ডকুমেন্টে নির্দেশাবলী অন্তর্ভুক্ত রয়েছে।"
            else:
                cat_str = ", ".join(all_categories) if all_categories else "PROMPT_INJECTION"
                en_expl = f"Blocked: High-risk prompt injection attempt detected ({cat_str})."
                bn_expl = (
                    f"প্রতিরোধ করা হয়েছে: উচ্চ-ঝুঁকিপূর্ণ প্রম্পট ইনজেকশন প্রচেষ্টা সনাক্ত হয়েছে ({cat_str})।"
                )

        elif risk_score >= self.approval_threshold:
            decision = "REQUIRE_APPROVAL"
            en_expl = f"Requires Approval: Potential policy violation or elevated risk score ({risk_score:.2f})."
            bn_expl = f"অনুমোদন প্রয়োজন: সম্ভাব্য নীতিমালা লঙ্ঘন বা উচ্চ ঝুঁকি স্কোর ({risk_score:.2f})।"

        elif pii_res.has_leakage:
            decision = "ALLOW_WITH_REDACTION"
            en_expl = "Allowed with Redaction: Personal data masked prior to transmission."
            bn_expl = "সংশোধনসহ অনুমোদিত: প্রেরণের পূর্বে ব্যক্তিগত তথ্য গোপন করা হয়েছে।"

        else:
            decision = "ALLOW"
            en_expl = "Allowed: Content verified safe and compliant with active policies."
            bn_expl = "অনুমোদিত: বিষয়বস্তু নিরাপদ এবং সক্রিয় নীতিমালার সাথে সামঞ্জস্যপূর্ণ।"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ScanResult(
            decision=decision,
            risk_score=risk_score,
            categories=sorted(set(all_categories)),
            rule_matches=all_matches,
            pii_findings=pii_res.findings,
            sanitized_text=pii_res.sanitized_text,
            spotlighted_text=prov_analysis.spotlighted_text,
            explanation=Explanation(en=en_expl, bn=bn_expl),
            latency_ms=elapsed_ms,
            has_canary_leak=has_canary,
        )
