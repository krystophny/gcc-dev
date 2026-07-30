#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "gcc_workflow", ROOT / "scripts" / "gcc-workflow.py"
)
assert SPEC and SPEC.loader
WORKFLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORKFLOW)


def format_patch(non_test_lines: str, test_lines: str = "") -> str:
    test_diff = ""
    if test_lines:
        test_diff = f"""
diff --git a/gcc/testsuite/gfortran.dg/example.f90 b/gcc/testsuite/gfortran.dg/example.f90
new file mode 100644
--- /dev/null
+++ b/gcc/testsuite/gfortran.dg/example.f90
@@ -0,0 +1,3 @@
{test_lines}
"""
    return f"""From 0123456789abcdef0123456789abcdef01234567 Mon Sep 17 00:00:00 2001
From: A Contributor <a@example.invalid>
Subject: [PATCH] example

Assisted-by: GPT-5.6-sol (OpenAI)
Signed-off-by: A Contributor <a@example.invalid>
---
diff --git a/gcc/fortran/example.cc b/gcc/fortran/example.cc
--- a/gcc/fortran/example.cc
+++ b/gcc/fortran/example.cc
@@ -1 +1 @@
{non_test_lines}
{test_diff}"""


class AiEligibilityTest(unittest.TestCase):
    def audit(self, text: str, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            patch = Path(directory) / "example.patch"
            patch.write_text(text, encoding="utf-8")
            return WORKFLOW.ai_patch_eligibility(patch, **kwargs)

    def test_counts_changed_source_and_excludes_testsuite(self):
        result = self.audit(
            format_patch(
                "-old_value\n+new_value",
                "+program p\n+end program p\n+! comment",
            ),
            expected_assistant="GPT-5.6-sol (OpenAI)",
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["non_test"], {"added": 1, "deleted": 1, "changed": 2})
        self.assertEqual(result["tests"], {"added": 3, "deleted": 0, "changed": 3})

    def test_blocks_fifteen_non_test_changed_lines(self):
        lines = "\n".join(f"+line_{number}" for number in range(15))
        text = format_patch(lines).replace("@@ -1 +1 @@", "@@ -0,0 +1,15 @@")
        result = self.audit(text)
        self.assertFalse(result["eligible"])
        self.assertIn("15 non-test changed lines", " ".join(result["reasons"]))

    def test_blocks_missing_assisted_by(self):
        result = self.audit(
            format_patch("-old_value\n+new_value").replace(
                "Assisted-by: GPT-5.6-sol (OpenAI)\n", ""
            )
        )
        self.assertFalse(result["eligible"])
        self.assertIn("missing Assisted-by tag", result["reasons"])

    def test_blocks_wrong_expected_assistant(self):
        result = self.audit(
            format_patch("-old_value\n+new_value"),
            expected_assistant="Claude (Anthropic)",
        )
        self.assertFalse(result["eligible"])
        self.assertIn(
            "missing expected assistant: Claude (Anthropic)", result["reasons"]
        )

    def test_blocks_multi_commit_mbox(self):
        text = format_patch("-old_value\n+new_value")
        text += "\nFrom fedcba9876543210fedcba9876543210fedcba98 Mon Sep 17 00:00:00 2001\n"
        result = self.audit(text)
        self.assertFalse(result["eligible"])
        self.assertIn("exactly one commit, found 2", " ".join(result["reasons"]))

    def test_submission_requires_expected_assistant(self):
        with self.assertRaisesRegex(
            WORKFLOW.WorkflowError, "--expected-assistant is required"
        ):
            WORKFLOW.submit_bugzilla(123, "trunk", False)


class MetadataInferenceTest(unittest.TestCase):
    def test_open_status_advances_when_patch_exists(self):
        self.assertEqual(
            WORKFLOW.infer_fix_status("open", {}, ["0001-fix.patch"]),
            "patch-ready",
        )

    def test_sync_records_verified_bugzilla_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            pr_dir = Path(directory) / "123"
            pr_dir.mkdir()
            (pr_dir / "README.md").write_text(
                "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123\n",
                encoding="utf-8",
            )
            generated = {"submission_status": {"on_bugzilla": False}}
            with (
                mock.patch.object(WORKFLOW, "ROOT", Path(directory)),
                mock.patch.object(WORKFLOW, "build_status", return_value=generated),
                mock.patch.object(WORKFLOW, "write_json") as write_json,
            ):
                WORKFLOW.sync_metadata(
                    [pr_dir], False, mark_on_bugzilla=True
                )
            self.assertTrue(
                write_json.call_args.args[1]["submission_status"]["on_bugzilla"]
            )


if __name__ == "__main__":
    unittest.main()
