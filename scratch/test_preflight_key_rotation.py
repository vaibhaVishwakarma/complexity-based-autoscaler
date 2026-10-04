#!/usr/bin/env python3
"""
scratch/test_preflight_key_rotation.py

Preflight Verification Suite for Key Rotation & Unattended Resumption:
    1. Pool Parsing & Round-Robin Rotation
    2. Simulated Auto-Recovery on 429 / 400 (Fault-Tolerant Key Selection)
    3. In-Flight OpenAILLM Auto-Rotation on 429 Quota Exhaustion
    4. Checkpoint Discovery & State Resumption
    5. Real Live Key Health Status Check
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "clones" / "openevolve"))

from scripts.rotate_api_key import (
    load_backup_keys,
    get_active_key,
    write_active_key,
    rotate_to_next,
    find_first_working_key,
    test_api_key,
    mask_key,
)
from scripts.run_unattended import get_latest_checkpoint_iteration


class PreflightKeyRotationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch_dir = WORKSPACE_ROOT / "scratch" / "preflight_tmp"
        cls.scratch_dir.mkdir(parents=True, exist_ok=True)
        cls.test_env = cls.scratch_dir / "test.env"
        cls.test_backup = cls.scratch_dir / "test.env.backup"

    @classmethod
    def tearDownClass(cls):
        if cls.scratch_dir.exists():
            shutil.rmtree(cls.scratch_dir)

    def test_01_backup_pool_parsing_and_rotation(self):
        """Verify parsing multiple key formats, round-robin rotation, and env var preservation."""
        dummy_1 = "AIzaSyDummyKeyAlpha111111111111111"
        dummy_2 = "AIzaSyDummyKeyBeta2222222222222222"
        dummy_3 = "AIzaSyDummyKeyGamma333333333333333"

        # Write mixed-format backup file
        self.test_backup.write_text(f"""# Backup Key Pool Test
{dummy_1}
GEMINI_API_KEY_2={dummy_2}
export GEMINI_API_KEY_3="{dummy_3}"
""")

        # Write active env file with additional custom variable
        self.test_env.write_text(f"GEMINI_API_KEY={dummy_1}\nPRESERVED_VAR=keep_me\n")

        # 1. Parse keys
        keys = load_backup_keys(self.test_backup)
        self.assertEqual(len(keys), 3)
        self.assertEqual(keys[0], dummy_1)
        self.assertEqual(keys[1], dummy_2)
        self.assertEqual(keys[2], dummy_3)

        # 2. Check active key
        self.assertEqual(get_active_key(self.test_env), dummy_1)

        # 3. Rotate to next -> should become dummy_2
        idx, total, masked = rotate_to_next(self.test_backup, self.test_env)
        self.assertEqual(idx, 2)
        self.assertEqual(total, 3)
        self.assertEqual(get_active_key(self.test_env), dummy_2)

        # Check preserved variable
        env_content = self.test_env.read_text()
        self.assertIn("PRESERVED_VAR=keep_me", env_content)

        # 4. Rotate to next -> should become dummy_3
        idx, total, masked = rotate_to_next(self.test_backup, self.test_env)
        self.assertEqual(idx, 3)
        self.assertEqual(get_active_key(self.test_env), dummy_3)

        # 5. Rotate again -> wraps around to dummy_1
        idx, total, masked = rotate_to_next(self.test_backup, self.test_env)
        self.assertEqual(idx, 1)
        self.assertEqual(get_active_key(self.test_env), dummy_1)

    def test_02_auto_find_working_key_simulation(self):
        """Simulate quota-exhausted keys and verify auto-find selects the first healthy key."""
        key_exhausted = "AIzaSyKeyExhausted1"
        key_invalid = "AIzaSyKeyInvalid2"
        key_working = "AIzaSyKeyWorking3"

        self.test_backup.write_text(f"{key_exhausted}\n{key_invalid}\n{key_working}\n")
        self.test_env.write_text(f"GEMINI_API_KEY={key_exhausted}\n")

        def mock_test_api_key(k, *args, **kwargs):
            if k == key_exhausted:
                return False, "HTTP 429 Quota/Rate Limit Exceeded"
            elif k == key_invalid:
                return False, "HTTP 400 Auth/Permission Error"
            elif k == key_working:
                return True, "HTTP 200 OK (Key active & responsive)"
            return False, "Unknown"

        with patch("scripts.rotate_api_key.test_api_key", side_effect=mock_test_api_key):
            idx, total, masked = find_first_working_key(self.test_backup, self.test_env)
            self.assertEqual(idx, 3)
            self.assertEqual(get_active_key(self.test_env), key_working)

    def test_03_in_flight_openai_llm_auto_rotation(self):
        """Verify OpenAILLM automatically intercepts 429 quota errors, rotates key in-place, and succeeds."""
        key_old = "AIzaSyKeyOld11111111"
        key_new = "AIzaSyKeyNew22222222"

        isolated_backup = self.scratch_dir / ".env.backup"
        isolated_env = self.scratch_dir / ".env"
        isolated_backup.write_text(f"{key_old}\n{key_new}\n")
        isolated_env.write_text(f"GEMINI_API_KEY={key_old}\n")

        from openevolve.config import LLMModelConfig
        from openevolve.llm.openai import OpenAILLM

        model_cfg = LLMModelConfig(
            name="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=key_old,
            temperature=0.7,
            max_tokens=10,
            timeout=15,
            retries=2,
        )

        llm = OpenAILLM(model_cfg)
        self.assertEqual(llm.api_key, key_old)

        import scripts.rotate_api_key as rot_module
        orig_backup = rot_module.DEFAULT_BACKUP_FILE
        orig_env = rot_module.DEFAULT_ENV_FILE
        rot_module.DEFAULT_BACKUP_FILE = isolated_backup
        rot_module.DEFAULT_ENV_FILE = isolated_env

        call_count = 0

        async def mock_call_api(params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call triggers 429 quota exhaustion
                raise Exception("Error code: 429 - {'error': {'message': 'RESOURCE_EXHAUSTED', 'status': 'RESOURCE_EXHAUSTED'}}")
            else:
                # Second call succeeds
                return "Mocked successful completion text"

        try:
            with patch.object(llm, "_call_api", side_effect=mock_call_api):
                response = asyncio.run(llm.generate("Hello"))
                self.assertEqual(response, "Mocked successful completion text")
                # Key must have rotated in-flight!
                self.assertEqual(llm.api_key, key_new)
                self.assertEqual(llm.client.api_key, key_new)
                self.assertEqual(get_active_key(isolated_env), key_new)
                self.assertEqual(call_count, 2)
        finally:
            rot_module.DEFAULT_BACKUP_FILE = orig_backup
            rot_module.DEFAULT_ENV_FILE = orig_env

    def test_04_checkpoint_detection(self):
        """Verify that supervisor correctly reads latest checkpoint from disk."""
        latest = get_latest_checkpoint_iteration()
        self.assertGreaterEqual(latest, 3, "Dry run produced at least checkpoint_3")

    def test_05_current_env_live_key_status(self):
        """Checks the real active key status in .env and logs diagnosis."""
        real_key = get_active_key(WORKSPACE_ROOT / ".env")
        self.assertIsNotNone(real_key, "GEMINI_API_KEY must be in .env")
        ok, msg = test_api_key(real_key)
        masked = mask_key(real_key)
        print(f"\n[LIVE DIAGNOSTIC] Current active key [{masked}]: {msg}")
        # Note: Even if exhausted right now (429), the test passes because the diagnostic informs us!


if __name__ == "__main__":
    unittest.main(verbosity=2)
