from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_SERVICE_DIR = PROJECT_ROOT / "feature-extraction-service"

sys.path.insert(0, str(FEATURE_SERVICE_DIR))

from services.feature_service import extract_features  # noqa: E402


POSITIVE_LABELS = {"plagiarized", "same", "copy", "duplicate", "1", "true", "yes"}
NEGATIVE_LABELS = {"not_plagiarized", "different", "semantic_only", "0", "false", "no"}


@dataclass
class PairResult:
    image_a: str
    image_b: str
    label: str
    clip_score: float
    cnn_score: float
    final_score: float
    prediction: str
    correct: bool


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    arr1 = np.array(vec1, dtype=np.float32)
    arr2 = np.array(vec2, dtype=np.float32)

    if arr1.shape != arr2.shape:
        return 0.0

    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(arr1, arr2) / (norm1 * norm2))


def normalize_label(label: str) -> str:
    normalized = label.strip().lower()

    if normalized in POSITIVE_LABELS:
        return "plagiarized"

    if normalized in NEGATIVE_LABELS:
        return "not_plagiarized"

    raise ValueError(
        f"Unknown label '{label}'. Use one of: "
        "plagiarized/same/copy/duplicate or not_plagiarized/different/semantic_only."
    )


def predict_label(
    clip_score: float,
    cnn_score: float,
    final_score: float,
    clip_threshold: float,
    cnn_threshold: float,
    final_threshold: float,
) -> str:
    if clip_score >= clip_threshold and cnn_score >= cnn_threshold:
        return "plagiarized"

    if final_score >= final_threshold and cnn_score >= cnn_threshold:
        return "plagiarized"

    return "not_plagiarized"


async def evaluate_pair(
    image_a: Path,
    image_b: Path,
    label: str,
    clip_weight: float,
    cnn_weight: float,
    clip_threshold: float,
    cnn_threshold: float,
    final_threshold: float,
) -> PairResult:
    features_a = await extract_features(image_a.read_bytes())
    features_b = await extract_features(image_b.read_bytes())

    clip_score = cosine_similarity(features_a["clip_embedding"], features_b["clip_embedding"])
    cnn_score = cosine_similarity(features_a["cnn_embedding"], features_b["cnn_embedding"])
    final_score = (clip_score * clip_weight) + (cnn_score * cnn_weight)

    expected = normalize_label(label)
    prediction = predict_label(
        clip_score=clip_score,
        cnn_score=cnn_score,
        final_score=final_score,
        clip_threshold=clip_threshold,
        cnn_threshold=cnn_threshold,
        final_threshold=final_threshold,
    )

    return PairResult(
        image_a=str(image_a),
        image_b=str(image_b),
        label=expected,
        clip_score=clip_score,
        cnn_score=cnn_score,
        final_score=final_score,
        prediction=prediction,
        correct=prediction == expected,
    )


def read_pairs(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required_columns = {"image_a", "image_b", "label"}
        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing_columns))}")

        yield from reader


def calculate_metrics(results: list[PairResult]) -> dict[str, float]:
    total = len(results)
    correct = sum(result.correct for result in results)
    true_positive = sum(
        result.label == "plagiarized" and result.prediction == "plagiarized"
        for result in results
    )
    false_positive = sum(
        result.label == "not_plagiarized" and result.prediction == "plagiarized"
        for result in results
    )
    false_negative = sum(
        result.label == "plagiarized" and result.prediction == "not_plagiarized"
        for result in results
    )
    true_negative = sum(
        result.label == "not_plagiarized" and result.prediction == "not_plagiarized"
        for result in results
    )

    accuracy = correct / total if total else 0.0
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "total": float(total),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive": float(true_positive),
        "false_positive": float(false_positive),
        "false_negative": float(false_negative),
        "true_negative": float(true_negative),
    }


def write_results(output_path: Path, results: list[PairResult], metrics: dict[str, float]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "image_a",
            "image_b",
            "label",
            "clip_score",
            "cnn_score",
            "final_score",
            "prediction",
            "correct",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "image_a": result.image_a,
                    "image_b": result.image_b,
                    "label": result.label,
                    "clip_score": f"{result.clip_score:.6f}",
                    "cnn_score": f"{result.cnn_score:.6f}",
                    "final_score": f"{result.final_score:.6f}",
                    "prediction": result.prediction,
                    "correct": result.correct,
                }
            )

        writer.writerow({})
        writer.writerow({"image_a": "metrics"})
        for name, value in metrics.items():
            writer.writerow({"image_a": name, "image_b": f"{value:.6f}"})


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CLIP/CNN similarity accuracy on labeled image pairs.")
    parser.add_argument("--pairs", required=True, type=Path, help="CSV file with image_a,image_b,label columns.")
    parser.add_argument("--output", default=Path("reports/similarity_evaluation.csv"), type=Path)
    parser.add_argument("--clip-weight", default=0.4, type=float)
    parser.add_argument("--cnn-weight", default=0.6, type=float)
    parser.add_argument("--clip-threshold", default=0.88, type=float)
    parser.add_argument("--cnn-threshold", default=0.75, type=float)
    parser.add_argument("--final-threshold", default=0.82, type=float)
    args = parser.parse_args()

    rows = list(read_pairs(args.pairs))
    results: list[PairResult] = []

    for index, row in enumerate(rows, start=1):
        image_a = (args.pairs.parent / row["image_a"]).resolve()
        image_b = (args.pairs.parent / row["image_b"]).resolve()

        print(f"[{index}/{len(rows)}] Evaluating {image_a.name} vs {image_b.name}")

        result = await evaluate_pair(
            image_a=image_a,
            image_b=image_b,
            label=row["label"],
            clip_weight=args.clip_weight,
            cnn_weight=args.cnn_weight,
            clip_threshold=args.clip_threshold,
            cnn_threshold=args.cnn_threshold,
            final_threshold=args.final_threshold,
        )
        results.append(result)

    metrics = calculate_metrics(results)
    write_results(args.output, results, metrics)

    print("\nEvaluation complete")
    print(f"Total: {int(metrics['total'])}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"True Positives: {int(metrics['true_positive'])}")
    print(f"False Positives: {int(metrics['false_positive'])}")
    print(f"False Negatives: {int(metrics['false_negative'])}")
    print(f"True Negatives: {int(metrics['true_negative'])}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

