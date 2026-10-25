# Model Card: Multilingual Calibrated Injection Classifier
**Model Architecture**: Char n-gram (1–5) TF-IDF + Calibrated Logistic Regression (Platt scaling / sigmoid)
**Framework**: scikit-learn
**Hardware**: CPU-only (<15ms latency per inference)
**Training Samples**: 1954
**Validation Metrics**:
- Accuracy: 0.9545
- Precision: 0.9661
- Recall: 0.9540
- F1-Score: 0.9600

## Data Provenance & Leakage Protection
Trained strictly on synthetic `injection_train` and `benign_train`.
The held-out test splits (`test_heldout`, `test_adaptive`) are guaranteed untouched.
