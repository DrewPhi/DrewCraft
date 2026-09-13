import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluate_world_candidates", ROOT / "tools/evaluate_world_candidates.py")
evaluator = importlib.util.module_from_spec(spec)
sys.modules["evaluate_world_candidates"] = evaluator
spec.loader.exec_module(evaluator)


class ProductionWorldCandidateLockTest(unittest.TestCase):
    def plan(self):
        return json.loads((ROOT / "world/production-world.plan.json").read_text("utf-8"))

    def report(self):
        return {
            "schemaVersion": 1,
            "candidateId": "seed-123-radius-4096",
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "generationPackVersion": "drewcraft-worldgen-1",
            "seed": 123,
            "pregenRadiusBlocks": 4096,
            "worldArchiveSha256": "a" * 64,
            "metrics": {
                "generationSeconds": 1200,
                "worldBytes": 10_000_000,
                "archiveBytes": 5_000_000,
                "backupSeconds": 10,
                "restoreSeconds": 12,
                "restartSeconds": 90,
                "cleanRestoreVerified": True,
            },
            "reviews": {
                "visualTerrainQuality": {"pass": True, "notes": "mountains, rivers and valleys look coherent"},
                "sourceDistribution": {"pass": True, "notes": "hostile sources are sparse enough for strategic travel"},
                "herdCorridorQuality": {"pass": True, "notes": "open corridors exist away from player livestock"},
            },
        }

    def test_fully_measured_and_reviewed_candidate_can_lock_seed_and_radius(self):
        locked = evaluator.lock_candidate(self.plan(), self.report())
        self.assertEqual("locked", locked["status"])
        self.assertEqual("drewcraft-worldgen-1", locked["generationPackVersion"])
        self.assertEqual(123, locked["terrain"]["seed"])
        self.assertEqual(4096, locked["terrain"]["pregenRadiusBlocks"])
        self.assertEqual("drewcraft-worldgen-1", locked["terrain"]["lockedCandidate"]["generationPackVersion"])
        self.assertEqual("a" * 64, locked["terrain"]["lockedCandidate"]["worldArchiveSha256"])

    def test_visual_or_restore_failure_refuses_false_production_lock(self):
        bad = self.report()
        bad["reviews"]["visualTerrainQuality"]["pass"] = False
        with self.assertRaisesRegex(RuntimeError, "visualTerrainQuality"):
            evaluator.lock_candidate(self.plan(), bad)

        bad = self.report()
        bad["metrics"]["cleanRestoreVerified"] = False
        with self.assertRaisesRegex(RuntimeError, "clean off-host restore"):
            evaluator.lock_candidate(self.plan(), bad)

    def test_unapproved_radius_invalid_hash_or_wrong_generation_pack_is_rejected(self):
        bad = self.report()
        bad["pregenRadiusBlocks"] = 9999
        with self.assertRaisesRegex(RuntimeError, "approved experiment radius"):
            evaluator.lock_candidate(self.plan(), bad)

        bad = self.report()
        bad["worldArchiveSha256"] = "not-a-hash"
        with self.assertRaisesRegex(RuntimeError, "archive SHA-256"):
            evaluator.lock_candidate(self.plan(), bad)

        bad = self.report()
        bad["generationPackVersion"] = "wrong-worldgen"
        with self.assertRaisesRegex(RuntimeError, "generationPackVersion"):
            evaluator.lock_candidate(self.plan(), bad)


if __name__ == "__main__":
    unittest.main()
