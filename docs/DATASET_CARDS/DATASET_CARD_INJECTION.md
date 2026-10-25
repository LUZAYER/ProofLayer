# Dataset Card: Multilingual Prompt Injection Benchmark
**Version**: 1.0.0
**Generator Seed**: 42
**Origin**: 100% Synthetic, curated templates and lexical slots for benign banking support and adversarial probes.

## Splits and Counts
- `injection_train`: 1118 samples
- `injection_val`: 239 samples
- `injection_test_heldout`: 241 samples
- `injection_test_adaptive`: 241 samples (mutated with unseen transforms)
- `benign_train`: 836 samples
- `benign_val`: 179 samples
- `benign_test`: 180 samples
- `pii_secrets_synthetic`: 7 samples

## SHA-256 Checksums
```json
{
  "injection_train": "55e188b56f01dd09ac09d1d30db8f5a39659a704300c108905378851b29f7ef6",
  "injection_val": "589bd95a3504239013cd4f284673d906c7e51c95c6ec224c3d51dfc034dc4eb6",
  "injection_test_heldout": "6a6d5ac6985bdb912cb80d4192b65a740b8411a213730d2f8009ff12a3fbe238",
  "injection_test_adaptive": "04bfe79365f9992e1e3ca885f6e6160483c19befc371477964a413f37cf895be",
  "benign_train": "a16a915f6530203e8adea00cd91d34ce57f50b488d5a3062e8191fbc8d3ec5e8",
  "benign_val": "1d006ddf9f8d7afcb84e54569291df58e029ab7869cfbbd3d17da361455cf180",
  "benign_test": "9ae056b4922de8bdbd2c327ae5e40c6d37fa9fd7601198746488db32d7abdf45",
  "pii_secrets_synthetic": "1a8fa0c7b3fccdfda6aea2e2d02e75e6a8e4a7d1850818cfe76000748c2ee8dd"
}
```

## Isolation Guarantee
The classifier and rules engine are trained exclusively on `*_train` and `*_val`. The `test_heldout` and `test_adaptive` sets are strictly reserved for final evaluation.
