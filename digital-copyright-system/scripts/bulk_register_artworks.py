from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import sys
import time
from pathlib import Path
from typing import Any

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA_CSV = PROJECT_ROOT / "evaluation_dataset" / "metadata_met.csv"
DEFAULT_STATE_CSV = PROJECT_ROOT / "reports" / "bulk_artwork_registration.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register an Open Access artwork dataset through the complete application workflow."
    )
    parser.add_argument("--base-url", default="http://localhost:8080/api/v1")
    parser.add_argument("--metadata-csv", type=Path, default=DEFAULT_METADATA_CSV)
    parser.add_argument("--state-csv", type=Path, default=DEFAULT_STATE_CSV)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--high-threshold", type=float, default=0.98)
    parser.add_argument("--medium-threshold", type=float, default=0.97)
    parser.add_argument("--low-threshold", type=float, default=0.96)
    parser.add_argument(
        "--approve-review",
        action="store_true",
        help="Approve review/blocked results for this known CC0 test dataset.",
    )
    parser.add_argument("--request-timeout", type=float, default=180.0)
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def dataset_marker(image_id: str) -> str:
    return f"dataset_image_id={image_id}"


def registered_metadata_by_dataset_id(
    metadata_items: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    for item in metadata_items:
        description = str(item.get("description") or "")
        for part in description.split(";"):
            part = part.strip()
            if part.startswith("dataset_image_id="):
                found[part.split("=", 1)[1].strip()] = item

    return found


def response_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]

    detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
    return json.dumps(detail, ensure_ascii=False)[:1000]


def write_state(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "image_id",
        "file_path",
        "title",
        "status",
        "check_id",
        "registration_status",
        "review_action",
        "overall_score",
        "metadata_id",
        "embedding_status",
        "image_url",
        "duration_seconds",
        "error",
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def register_one(
    client: httpx.Client,
    base_url: str,
    metadata_csv: Path,
    row: dict[str, str],
    thresholds: dict[str, float],
    approve_review: bool,
) -> dict[str, Any]:
    image_id = row["image_id"]
    image_path = (metadata_csv.parent / row["file_path"]).resolve()
    started_at = time.perf_counter()
    result: dict[str, Any] = {
        "image_id": image_id,
        "file_path": row["file_path"],
        "title": row.get("title") or image_id,
        "status": "failed",
        "check_id": "",
        "registration_status": "",
        "review_action": "",
        "overall_score": "",
        "metadata_id": "",
        "embedding_status": "",
        "image_url": "",
        "duration_seconds": "",
        "error": "",
    }

    try:
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        content_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        with image_path.open("rb") as image_file:
            upload_response = client.post(
                f"{base_url}/upload",
                data={
                    "high_threshold": str(thresholds["high"]),
                    "medium_threshold": str(thresholds["medium"]),
                    "low_threshold": str(thresholds["low"]),
                },
                files={"file": (image_path.name, image_file, content_type)},
            )

        if not upload_response.is_success:
            raise RuntimeError(
                f"Upload HTTP {upload_response.status_code}: {response_error(upload_response)}"
            )

        upload_result = upload_response.json()
        check_id = upload_result["check_id"]
        result["check_id"] = check_id
        result["registration_status"] = upload_result.get("registration_status", "")
        result["overall_score"] = (
            upload_result.get("similarity_result", {}).get("overall_score", "")
        )

        if not upload_result.get("can_register", False):
            if not approve_review:
                result["status"] = "requires_review"
                return result

            review_response = client.post(
                f"{base_url}/review-check/{check_id}/approve",
                json={
                    "reason": (
                        "Bulk import dataset pengujian CC0/Public Domain; "
                        f"source={row.get('source', '')}; image_id={image_id}"
                    )
                },
            )
            if not review_response.is_success:
                raise RuntimeError(
                    f"Review HTTP {review_response.status_code}: {response_error(review_response)}"
                )
            result["review_action"] = "approved_test_dataset"

        description_parts = [
            dataset_marker(image_id),
            f"source={row.get('source', '')}",
            f"license={row.get('license', '')}",
            f"artist={row.get('artist', '')}",
            f"date={row.get('date', '')}",
            f"medium={row.get('medium', '')}",
            f"source_url={row.get('source_url', '')}",
        ]
        registration_payload = {
            "check_id": check_id,
            "title": row.get("title") or image_id,
            "description": "; ".join(description_parts),
            "category": "HAK CIPTA",
            "sub_category": "karya seni",
            "copyright_category": "karya seni",
            "copyright_sub_category": "karya seni visual",
        }
        register_response = client.post(
            f"{base_url}/register-metadata",
            json=registration_payload,
        )

        if not register_response.is_success:
            raise RuntimeError(
                f"Register HTTP {register_response.status_code}: {response_error(register_response)}"
            )

        registered = register_response.json()
        metadata = registered.get("metadata", {})
        result.update(
            {
                "status": "registered",
                "metadata_id": metadata.get("id", ""),
                "embedding_status": registered.get(
                    "embedding_status", metadata.get("embedding_status", "")
                ),
                "image_url": metadata.get("image_url", ""),
            }
        )
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        result["duration_seconds"] = f"{time.perf_counter() - started_at:.2f}"

    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    rows = load_csv(args.metadata_csv)
    selected_rows = rows[args.start : args.start + args.limit]
    state_rows = load_csv(args.state_csv) if args.state_csv.exists() else []
    state_by_id = {row["image_id"]: row for row in state_rows}
    thresholds = {
        "high": args.high_threshold,
        "medium": args.medium_threshold,
        "low": args.low_threshold,
    }

    if not 0 < thresholds["low"] < thresholds["medium"] < thresholds["high"] <= 1:
        raise ValueError("Threshold order must be 0 < low < medium < high <= 1")

    base_url = args.base_url.rstrip("/")
    with httpx.Client(timeout=args.request_timeout) as client:
        metadata_response = client.get(f"{base_url}/metadata")
        metadata_response.raise_for_status()
        registered_metadata = registered_metadata_by_dataset_id(metadata_response.json())
        already_registered = set(registered_metadata)

        for index, row in enumerate(selected_rows, start=args.start + 1):
            image_id = row["image_id"]
            previous = state_by_id.get(image_id)

            if image_id in already_registered:
                stored = registered_metadata[image_id]
                if not previous or previous.get("status") != "registered":
                    state_by_id[image_id] = {
                        "image_id": image_id,
                        "file_path": row["file_path"],
                        "title": row.get("title") or image_id,
                        "status": "registered",
                        "check_id": stored.get("check_id", ""),
                        "registration_status": "already_registered",
                        "review_action": "",
                        "overall_score": "",
                        "metadata_id": stored.get("id", ""),
                        "embedding_status": stored.get("embedding_status", ""),
                        "image_url": stored.get("image_url", ""),
                        "duration_seconds": "0.00",
                        "error": "",
                    }
                    write_state(args.state_csv, list(state_by_id.values()))
                print(f"[{index}/{len(rows)}] SKIP {image_id}: already registered", flush=True)
                continue

            if previous and previous.get("status") == "registered":
                print(f"[{index}/{len(rows)}] SKIP {image_id}: checkpoint registered", flush=True)
                continue

            print(f"[{index}/{len(rows)}] PROCESS {image_id}: {row.get('title', '')}", flush=True)
            result = register_one(
                client=client,
                base_url=base_url,
                metadata_csv=args.metadata_csv,
                row=row,
                thresholds=thresholds,
                approve_review=args.approve_review,
            )
            state_by_id[image_id] = result
            write_state(args.state_csv, list(state_by_id.values()))
            print(
                f"[{index}/{len(rows)}] {result['status'].upper()} "
                f"score={result['overall_score']} duration={result['duration_seconds']}s "
                f"error={result['error']}",
                flush=True,
            )

    final_rows = list(state_by_id.values())
    registered_count = sum(row.get("status") == "registered" for row in final_rows)
    failed_count = sum(row.get("status") == "failed" for row in final_rows)
    review_count = sum(row.get("status") == "requires_review" for row in final_rows)
    print(
        f"Complete: registered={registered_count}, failed={failed_count}, "
        f"requires_review={review_count}, state={args.state_csv}"
    )


if __name__ == "__main__":
    main()
