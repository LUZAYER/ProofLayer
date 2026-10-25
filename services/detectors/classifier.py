"""Char n-gram TF-IDF and calibrated linear classifier for prompt injection detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@dataclass
class ClassificationResult:
    """Result of ML injection classification."""

    probability: float  # 0.0 to 1.0
    is_injection: bool
    top_ngrams: list[str] = field(default_factory=list)
    confidence: float = 1.0


class InjectionClassifier:
    """Fast, CPU-efficient, calibrated ML classifier for prompt injection."""

    def __init__(self) -> None:
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(1, 5),
            max_features=15000,
            sublinear_tf=True,
        )
        base_lr = LogisticRegression(
            C=2.0,
            solver="liblinear",
            random_state=42,
            max_iter=500,
        )
        self.model: CalibratedClassifierCV = CalibratedClassifierCV(
            estimator=base_lr,
            method="sigmoid",
            cv=3,
        )
        self.is_trained: bool = False
        self.feature_names: np.ndarray | None = None

    def train(self, texts: list[str], labels: list[int]) -> dict[str, Any]:
        """Train vectorizer and calibrated classifier on language-balanced corpus."""
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_trained = True
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())

        train_score = float(self.model.score(X, labels))
        return {
            "samples_count": len(texts),
            "features_count": X.shape[1],
            "train_accuracy": train_score,
        }

    def predict(self, text: str, threshold: float = 0.5) -> ClassificationResult:
        """Predict injection probability and extract top contributing char n-grams."""
        if not self.is_trained:
            # Fallback if model not trained yet
            return ClassificationResult(probability=0.0, is_injection=False)

        if not text.strip():
            return ClassificationResult(probability=0.0, is_injection=False)

        vec = self.vectorizer.transform([text])
        proba = float(self.model.predict_proba(vec)[0][1])

        # Extract top feature n-grams active in the text
        top_ngrams: list[str] = []
        if self.feature_names is not None and vec.nnz > 0:
            active_indices = vec.indices
            active_values = vec.data
            sorted_order = np.argsort(active_values)[::-1]
            top_active = active_indices[sorted_order[:5]]
            top_ngrams = [str(self.feature_names[idx]) for idx in top_active]

        return ClassificationResult(
            probability=proba,
            is_injection=proba >= threshold,
            top_ngrams=top_ngrams,
            confidence=abs(proba - 0.5) * 2.0,
        )

    def save(self, model_dir: Path | str) -> None:
        """Save serialized model and metadata."""
        dir_path = Path(model_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, dir_path / "vectorizer.joblib")
        joblib.dump(self.model, dir_path / "calibrated_model.joblib")
        meta = {
            "version": "1.0.0",
            "features_count": len(self.feature_names) if self.feature_names is not None else 0,
        }
        with (dir_path / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def load(self, model_dir: Path | str) -> bool:
        """Load model artifacts from disk if present."""
        dir_path = Path(model_dir)
        vec_path = dir_path / "vectorizer.joblib"
        model_path = dir_path / "calibrated_model.joblib"

        if not vec_path.exists() or not model_path.exists():
            return False

        self.vectorizer = joblib.load(vec_path)
        self.model = joblib.load(model_path)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())
        self.is_trained = True
        return True
