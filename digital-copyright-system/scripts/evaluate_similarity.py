from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
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
    transformation: str
    pair_type: str
    clip_score: float
    cnn_score: float
    final_score: float
    prediction: str
    correct: bool


FEATURE_CACHE: dict[Path, tuple[np.ndarray, np.ndarray]] = {}


def cosine_similarity(vec1: list[float] | np.ndarray, vec2: list[float] | np.ndarray) -> float:
    arr1 = np.array(vec1, dtype=np.float32)
    arr2 = np.array(vec2, dtype=np.float32)

    if arr1.shape != arr2.shape:
        return 0.0

    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(arr1, arr2) / (norm1 * norm2))


async def extract_features_cached(image_path: Path) -> tuple[np.ndarray, np.ndarray]:
    cache_key = image_path.resolve()

    if cache_key not in FEATURE_CACHE:
        features = await extract_features(cache_key.read_bytes())
        FEATURE_CACHE[cache_key] = (
            np.asarray(features["clip_embedding"], dtype=np.float32),
            np.asarray(features["cnn_embedding"], dtype=np.float32),
        )

    return FEATURE_CACHE[cache_key]


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


def predict_label(final_score: float, final_threshold: float) -> str:
    if final_score >= final_threshold:
        return "plagiarized"

    return "not_plagiarized"


async def evaluate_pair(
    image_a: Path,
    image_b: Path,
    label: str,
    transformation: str,
    pair_type: str,
    clip_weight: float,
    cnn_weight: float,
    final_threshold: float,
) -> PairResult:
    clip_a, cnn_a = await extract_features_cached(image_a)
    clip_b, cnn_b = await extract_features_cached(image_b)

    clip_score = cosine_similarity(clip_a, clip_b)
    cnn_score = cosine_similarity(cnn_a, cnn_b)
    final_score = (clip_score * clip_weight) + (cnn_score * cnn_weight)

    expected = normalize_label(label)
    prediction = predict_label(
        final_score=final_score,
        final_threshold=final_threshold,
    )

    return PairResult(
        image_a=str(image_a),
        image_b=str(image_b),
        label=expected,
        transformation=transformation,
        pair_type=pair_type,
        clip_score=clip_score,
        cnn_score=cnn_score,
        final_score=final_score,
        prediction=prediction,
        correct=prediction == expected,
    )


def read_pairs(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required_columns = {"image_a", "image_b", "label"}
        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing_columns))}")

        for row in reader:
            row["transformation"] = (row.get("transformation") or "overall").strip()
            row["pair_type"] = (
                row.get("pair_type")
                or ("positive" if normalize_label(row["label"]) == "plagiarized" else "negative")
            ).strip()
            yield row


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


def write_results(output_path: Path, results: list[PairResult]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "image_a",
            "image_b",
            "label",
            "transformation",
            "pair_type",
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
                    "transformation": result.transformation,
                    "pair_type": result.pair_type,
                    "clip_score": f"{result.clip_score:.6f}",
                    "cnn_score": f"{result.cnn_score:.6f}",
                    "final_score": f"{result.final_score:.6f}",
                    "prediction": result.prediction,
                    "correct": result.correct,
                }
            )



def calculate_grouped_metrics(results: list[PairResult]) -> dict[str, dict[str, float]]:
    grouped_results: dict[str, list[PairResult]] = defaultdict(list)

    for result in results:
        grouped_results[result.transformation].append(result)

    return {
        transformation: calculate_metrics(group)
        for transformation, group in sorted(grouped_results.items())
    }


def write_metrics(
    output_path: Path,
    overall_metrics: dict[str, float],
    grouped_metrics: dict[str, dict[str, float]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metric_names = [
        "total",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "true_positive",
        "false_positive",
        "false_negative",
        "true_negative",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["transformation", *metric_names])
        writer.writeheader()
        writer.writerow({"transformation": "overall", **overall_metrics})
        for transformation, metrics in grouped_metrics.items():
            writer.writerow({"transformation": transformation, **metrics})


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CLIP/CNN similarity accuracy on labeled image pairs.")
    parser.add_argument("--pairs", required=True, type=Path, help="CSV file with image_a,image_b,label columns.")
    parser.add_argument("--output", default=Path("reports/similarity_evaluation.csv"), type=Path)
    parser.add_argument(
        "--metrics-output",
        type=Path,
        help="CSV summary containing confusion matrix and metrics per transformation.",
    )
    parser.add_argument("--clip-weight", default=0.1, type=float)
    parser.add_argument("--cnn-weight", default=0.9, type=float)
    parser.add_argument("--final-threshold", default=0.82, type=float)
    args = parser.parse_args()
    metrics_output = args.metrics_output or args.output.with_name(
        f"{args.output.stem}_metrics{args.output.suffix}"
    )

    rows = list(read_pairs(args.pairs))
    results: list[PairResult] = []

    for index, row in enumerate(rows, start=1):
        image_a = (args.pairs.parent / row["image_a"]).resolve()
        image_b = (args.pairs.parent / row["image_b"]).resolve()

        if index == 1 or index % 25 == 0 or index == len(rows):
            print(
                f"[{index}/{len(rows)}] Evaluating {row['transformation']} pairs; "
                f"cached embeddings={len(FEATURE_CACHE)}"
            )

        result = await evaluate_pair(
            image_a=image_a,
            image_b=image_b,
            label=row["label"],
            transformation=row["transformation"],
            pair_type=row["pair_type"],
            clip_weight=args.clip_weight,
            cnn_weight=args.cnn_weight,
            final_threshold=args.final_threshold,
        )
        results.append(result)

    metrics = calculate_metrics(results)
    grouped_metrics = calculate_grouped_metrics(results)
    write_results(args.output, results)
    write_metrics(metrics_output, metrics, grouped_metrics)

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
    print("\nMetrics per transformation")
    for transformation, group_metrics in grouped_metrics.items():
        print(
            f"{transformation}: accuracy={group_metrics['accuracy']:.4f}, "
            f"precision={group_metrics['precision']:.4f}, "
            f"recall={group_metrics['recall']:.4f}, f1={group_metrics['f1']:.4f}, "
            f"TP={int(group_metrics['true_positive'])}, "
            f"FP={int(group_metrics['false_positive'])}, "
            f"FN={int(group_metrics['false_negative'])}, "
            f"TN={int(group_metrics['true_negative'])}"
        )
    print(f"Detailed results: {args.output}")
    print(f"Metrics summary: {metrics_output}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())



