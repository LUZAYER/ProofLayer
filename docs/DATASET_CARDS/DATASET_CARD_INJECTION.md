# Dataset Card: Multilingual Prompt Injection Benchmark
**Version**: 1.0.0
**Generator Seed**: 42
**Origin**: 100% Synthetic, curated templates and lexical slots for benign banking support and adversarial probes.

## Splits and Counts
- `injection_train`: 64 samples
- `injection_val`: 21 samples
- `injection_test_heldout`: 23 samples
- `injection_test_adaptive`: 23 samples (mutated with unseen transforms)
- `benign_train`: 216 samples
- `benign_val`: 72 samples
- `benign_test`: 72 samples

## SHA-256 Checksums
```json
{
  "injection_train": "74c8b9558766738eca5bfc8e2fc2aef879c9f679ca412a24ed3c10ae7f11150d",
  "injection_val": "decf680ba22a0a28d9d1b41e2a401ae983a13f40faa982243a873de57c1398fc",
  "injection_test_heldout": "6902b0f64600b49a15cb4293171aea13195d0580f7f7b2a66f2c92c3326ec500",
  "injection_test_adaptive": "5e1dc564c791904c14c80489c0dd2149c7af98c43d7a4a98631e6b6b155a8337",
  "benign_train": "ca93b172a6f5cf4a78012f1025199226daae5747482afbb6bed338eb0b991392",
  "benign_val": "68aebfab929f8fc137d9c983d15954e3e91ceca26cc5228d22414b673557cd80",
  "benign_test": "d9403150348247bcbb10915ffee708e879dae26cf1e11d2c1baff777a68f4851",
  "pii_secrets_synthetic": "1a8fa0c7b3fccdfda6aea2e2d02e75e6a8e4a7d1850818cfe76000748c2ee8dd"
}
```

## Isolation Guarantee
The classifier and rules engine are trained exclusively on `*_train` and `*_val`. The `test_heldout` and `test_adaptive` sets are strictly reserved for final evaluation.
