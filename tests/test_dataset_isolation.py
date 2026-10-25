"""Split isolation and no-tuning verification tests."""

import hashlib
import json
from pathlib import Path


def test_split_isolation_and_no_data_leakage() -> None:
    """Verify that train, heldout, and adaptive test sets have zero overlap."""
    datasets_dir = Path("eval/datasets")
    train_path = datasets_dir / "injection_train.jsonl"
    heldout_path = datasets_dir / "injection_test_heldout.jsonl"
    adaptive_path = datasets_dir / "injection_test_adaptive.jsonl"

    assert train_path.exists(), "injection_train.jsonl must exist"
    assert heldout_path.exists(), "injection_test_heldout.jsonl must exist"
    assert adaptive_path.exists(), "injection_test_adaptive.jsonl must exist"

    def load_texts(p: Path) -> set[str]:
        texts = set()
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    texts.add(rec["text"])
        return texts

    train_texts = load_texts(train_path)
    heldout_texts = load_texts(heldout_path)
    adaptive_texts = load_texts(adaptive_path)

    # Assert strictly disjoint sets
    train_heldout_overlap = train_texts.intersection(heldout_texts)
    assert len(train_heldout_overlap) == 0, f"Data leakage detected: {train_heldout_overlap}"

    train_adaptive_overlap = train_texts.intersection(adaptive_texts)
    assert len(train_adaptive_overlap) == 0, f"Data leakage detected: {train_adaptive_overlap}"


def test_dataset_card_checksums_match_files() -> None:
    """Verify SHA-256 checksums in dataset card match actual dataset files on disk."""
    card_path = Path("docs/DATASET_CARDS/DATASET_CARD_INJECTION.md")
    assert card_path.exists()
    card_content = card_path.read_text(encoding="utf-8")

    datasets_dir = Path("eval/datasets")
    for jsonl_file in datasets_dir.glob("*.jsonl"):
        hasher = hashlib.sha256()
        with jsonl_file.open("rb") as f:
            hasher.update(f.read())
        digest = hasher.hexdigest()
        assert digest in card_content, f"Checksum mismatch for {jsonl_file.name}"
