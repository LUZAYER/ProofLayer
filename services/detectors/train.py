"""Training script for multilingual calibrated injection classifier."""

from __future__ import annotations

import json
from pathlib import Path

from services.detectors.classifier import InjectionClassifier


def load_split(split_path: Path) -> list[dict[str, str | int]]:
    """Load JSONL dataset split."""
    records = []
    with split_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def train_classifier(
    datasets_dir: Path | None = None, model_dir: Path | None = None
) -> dict[str, float]:
    """Train classifier strictly on training and validation splits."""
    if datasets_dir is None:
        datasets_dir = Path(__file__).resolve().parent.parent.parent / "eval" / "datasets"
    if model_dir is None:
        model_dir = Path(__file__).resolve().parent / "model"

    inj_train_path = datasets_dir / "injection_train.jsonl"
    ben_train_path = datasets_dir / "benign_train.jsonl"
    inj_val_path = datasets_dir / "injection_val.jsonl"
    ben_val_path = datasets_dir / "benign_val.jsonl"

    if not inj_train_path.exists() or not ben_train_path.exists():
        raise FileNotFoundError(
            f"Dataset splits missing in {datasets_dir}. Please run 'eval/build_datasets.py' first."
        )

    inj_train = load_split(inj_train_path)
    ben_train = load_split(ben_train_path)
    inj_val = load_split(inj_val_path)
    ben_val = load_split(ben_val_path)

    train_texts = [str(r["text"]) for r in inj_train] + [str(r["text"]) for r in ben_train]
    train_labels = [1] * len(inj_train) + [0] * len(ben_train)

    val_texts = [str(r["text"]) for r in inj_val] + [str(r["text"]) for r in ben_val]
    val_labels = [1] * len(inj_val) + [0] * len(ben_val)

    classifier = InjectionClassifier()
    print(
        f"Training classifier on {len(train_texts)} samples ({len(inj_train)} injections, {len(ben_train)} benign)..."
    )
    classifier.train(train_texts, train_labels)

    # Evaluate on validation split
    val_correct = 0
    tp, fp, fn, tn = 0, 0, 0, 0
    for text, label in zip(val_texts, val_labels, strict=False):
        res = classifier.predict(text)
        pred = 1 if res.is_injection else 0
        if pred == label:
            val_correct += 1
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 1:
            fn += 1
        elif pred == 0 and label == 0:
            tn += 1

    val_acc = val_correct / len(val_texts) if val_texts else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(
        f"Validation Accuracy: {val_acc:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}"
    )

    # Save model
    classifier.save(model_dir)
    print(f"Model saved to {model_dir}")

    # Generate Model Card
    card_path = model_dir / "MODEL_CARD.md"
    card_path.write_text(
        f"""# Model Card: Multilingual Calibrated Injection Classifier
**Model Architecture**: Char n-gram (1–5) TF-IDF + Calibrated Logistic Regression (Platt scaling / sigmoid)
**Framework**: scikit-learn
**Hardware**: CPU-only (<15ms latency per inference)
**Training Samples**: {len(train_texts)}
**Validation Metrics**:
- Accuracy: {val_acc:.4f}
- Precision: {precision:.4f}
- Recall: {recall:.4f}
- F1-Score: {f1:.4f}

## Data Provenance & Leakage Protection
Trained strictly on synthetic `injection_train` and `benign_train`.
The held-out test splits (`test_heldout`, `test_adaptive`) are guaranteed untouched.
""",
        encoding="utf-8",
    )

    return {
        "val_accuracy": val_acc,
        "val_precision": precision,
        "val_recall": recall,
        "val_f1": f1,
    }


if __name__ == "__main__":
    train_classifier()
