# Model Card: Multilingual Calibrated Injection Classifier
**Model Architecture**: Char n-gram (1–5) TF-IDF + Calibrated Logistic Regression (Platt scaling / sigmoid)
**Framework**: scikit-learn
**Hardware**: CPU-only (<15ms latency per inference)
**Training Samples**: 280
**Validation Metrics**:
- Accuracy: 1.0000
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

## Data Provenance & Leakage Protection
Trained strictly on synthetic `injection_train` and `benign_train`.
The held-out test splits (`test_heldout`, `test_adaptive`) are guaranteed untouched.
