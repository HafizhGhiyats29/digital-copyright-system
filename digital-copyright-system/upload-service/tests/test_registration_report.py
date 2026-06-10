import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("INTERNAL_API_KEY", "upload-test-internal-key")

from routers import upload_router
from services.temporary_embedding_store import (
    delete_temporary_embedding,
    get_temporary_embedding,
    review_temporary_embedding,
    save_temporary_embedding,
)


class RegistrationReportTest(unittest.TestCase):
    def test_register_metadata_persists_temporary_report(self):
        check_id = "report-registration-test"
        captured_payload = {}
        report = {
            "status": "processed",
            "check_id": check_id,
            "can_register": True,
            "registration_status": "allowed",
            "registration_reason": "Registrasi diizinkan.",
            "web_search_result": {"found_on_web": False, "matches": []},
            "similarity_result": {
                "overall_score": 0.42,
                "results": {"internal_top3": [], "external_top3": []},
            },
            "decision_result": {
                "decision": {
                    "status": "no_significant_similarity",
                    "risk_level": "very_low",
                    "requires_review": False,
                },
            },
        }

        save_temporary_embedding(
            check_id=check_id,
            feature={
                "clip_embedding": [0.1, 0.2],
                "cnn_embedding": [0.3, 0.4],
            },
            decision=report["decision_result"],
            can_register=True,
            report=report,
        )

        async def fake_create_metadata(payload):
            captured_payload.update(payload)
            return {"id": "metadata-report-test", **payload}

        async def fake_insert_embedding(metadata_id, feature, embedding_version):
            return {
                "milvus_collection": "copyright_embeddings",
                "milvus_id": "123",
                "embedding_version": embedding_version,
            }

        async def fake_update_embedding_reference(metadata_id, embedding_reference):
            return {
                "id": metadata_id,
                **captured_payload,
                **embedding_reference,
            }

        request = upload_router.RegisterMetadataRequest(
            check_id=check_id,
            title="Karya dengan laporan",
            image_url="https://example.com/karya.jpg",
        )

        with (
            patch.object(upload_router, "create_metadata", fake_create_metadata),
            patch.object(upload_router, "insert_embedding", fake_insert_embedding),
            patch.object(
                upload_router,
                "update_embedding_reference",
                fake_update_embedding_reference,
            ),
        ):
            response = asyncio.run(upload_router.register_metadata(request))

        self.assertEqual(captured_payload["report"]["check_id"], check_id)
        self.assertEqual(
            captured_payload["report"]["similarity_result"]["overall_score"],
            0.42,
        )
        self.assertEqual(captured_payload["report"]["registration_status"], "allowed")
        self.assertTrue(captured_payload["report"]["saved_at"])
        self.assertEqual(
            captured_payload["report_saved_at"],
            captured_payload["report"]["saved_at"],
        )
        self.assertEqual(response["metadata"]["report"]["check_id"], check_id)
        self.assertIsNone(get_temporary_embedding(check_id))


    def test_manual_review_updates_report_snapshot(self):
        check_id = "manual-review-report-test"
        save_temporary_embedding(
            check_id=check_id,
            feature={},
            decision={},
            can_register=False,
            report={
                "check_id": check_id,
                "can_register": False,
                "registration_status": "review_required",
                "registration_reason": "Memerlukan review manual.",
            },
        )

        reviewed = review_temporary_embedding(
            check_id=check_id,
            approved=True,
            reason="Karya dinyatakan orisinal oleh reviewer.",
        )

        self.assertTrue(reviewed["can_register"])
        self.assertEqual(reviewed["report"]["registration_status"], "allowed")
        self.assertEqual(reviewed["report"]["manual_review_status"], "approved")
        self.assertEqual(
            reviewed["report"]["manual_review_reason"],
            "Karya dinyatakan orisinal oleh reviewer.",
        )
        delete_temporary_embedding(check_id)

if __name__ == "__main__":
    unittest.main()