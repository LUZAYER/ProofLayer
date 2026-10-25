"""Evaluation suite for multilingual detector ensemble."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from services.detectors.ensemble import DetectorEnsemble


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def run_detector_evaluation() -> dict[str, Any]:
    """Run comprehensive detector evaluation and benchmark latency."""
    base_dir = Path(__file__).resolve().parent.parent
    datasets_dir = base_dir / "eval" / "datasets"
    model_dir = base_dir / "services" / "detectors" / "model"
    rules_dir = base_dir / "services" / "detectors" / "rules"

    # Initialize ensemble
    ensemble = DetectorEnsemble(rules_dir=rules_dir, model_dir=model_dir)

    # 1. Evaluate on Validation Set
    val_inj = load_jsonl(datasets_dir / "injection_val.jsonl")
    val_ben = load_jsonl(datasets_dir / "benign_val.jsonl")

    val_records = [(r["text"], 1, r.get("language", "unknown")) for r in val_inj] + [
        (r["text"], 0, r.get("language", "unknown")) for r in val_ben
    ]

    tp, fp, fn, tn = 0, 0, 0, 0
    per_lang: dict[str, dict[str, int]] = {}

    for text, label, lang in val_records:
        if lang not in per_lang:
            per_lang[lang] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}

        res = ensemble.scan(text)
        is_blocked = res.decision in ("BLOCK", "REQUIRE_APPROVAL")

        if is_blocked and label == 1:
            tp += 1
            per_lang[lang]["tp"] += 1
        elif is_blocked and label == 0:
            fp += 1
            per_lang[lang]["fp"] += 1
        elif not is_blocked and label == 1:
            fn += 1
            per_lang[lang]["fn"] += 1
        else:
            tn += 1
            per_lang[lang]["tn"] += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    # 2. Evaluate on Adaptive Set (unseen mutations)
    adaptive_inj = load_jsonl(datasets_dir / "injection_test_adaptive.jsonl")
    adaptive_blocked = 0
    for r in adaptive_inj:
        res = ensemble.scan(r["text"])
        if res.decision in ("BLOCK", "REQUIRE_APPROVAL"):
            adaptive_blocked += 1
    adaptive_asr_blocked = adaptive_blocked / len(adaptive_inj) if adaptive_inj else 0.0

    # 3. Latency Benchmark across typical 1KB-4KB texts
    sample_text = (
        "Customer request: Please review my recent loan payment transaction and let me know "
        "if the refund of $50 has been credited to my account. Thank you."
    )
    latencies: list[float] = []
    # Warmup
    for _ in range(10):
        ensemble.scan(sample_text)

    # 100 timed iterations
    for _ in range(100):
        t0 = time.perf_counter()
        ensemble.scan(sample_text)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    p50 = statistics.median(latencies)
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    results = {
        "validation_metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "total_samples": len(val_records),
        },
        "per_language_f1": {
            lang: round(
                (2 * stats["tp"]) / (2 * stats["tp"] + stats["fp"] + stats["fn"])
                if (2 * stats["tp"] + stats["fp"] + stats["fn"]) > 0
                else 0.0,
                4,
            )
            for lang, stats in per_lang.items()
        },
        "adaptive_set_catch_rate": round(adaptive_asr_blocked, 4),
        "latency_ms": {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
        },
    }

    print("\n" + "=" * 50)
    print("PROOFLAYER DETECTOR ENSEMBLE EVALUATION REPORT")
    print("=" * 50)
    print(f"Validation F1-Score: {f1:.4f} (Precision: {precision:.4f}, Recall: {recall:.4f})")
    print(f"False Positive Rate (FPR): {fpr:.4f}")
    print(f"Adaptive Evasion Catch Rate: {adaptive_asr_blocked:.4f}")
    per_lang_f1 = results["per_language_f1"]
    if isinstance(per_lang_f1, dict):
        for lang, l_f1 in per_lang_f1.items():
            print(f"  Language '{lang}' F1: {l_f1:.4f}")
    print("=" * 50 + "\n")

    assert p95 < 50.0, f"Latency target failed: p95 is {p95:.2f}ms (must be < 50ms)"
    return results


if __name__ == "__main__":
    run_detector_evaluation()
