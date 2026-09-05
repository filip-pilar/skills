from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UNINSTALL = REPO_ROOT / "socket-audit" / "scripts" / "uninstall.sh"
DETECT = REPO_ROOT / "socket-audit" / "scripts" / "detect-package-managers.sh"


class UninstallSafetyTests(unittest.TestCase):
    def run_uninstall(self, home: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["PATH"] = "/usr/bin:/bin"
        return subprocess.run(
            ["/bin/bash", str(UNINSTALL), "--yes"],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_unmatched_alias_begin_leaves_entire_file_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            zshrc = home / ".zshrc"
            original = (
                "before\n"
                "# BEGIN socket-audit aliases\n"
                "alias npm='sfw npm'\n"
                "unrelated trailing config\n"
            )
            zshrc.write_text(original, encoding="utf-8")

            result = self.run_uninstall(home)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(zshrc.read_text(encoding="utf-8"), original)
            self.assertIn("alias markers are unbalanced", result.stdout + result.stderr)
            self.assertFalse((home / ".zshrc.socket-audit-backup").exists())

    def test_balanced_alias_block_is_removed_without_touching_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            zshrc = home / ".zshrc"
            zshrc.write_text(
                "before\n"
                "# BEGIN socket-audit aliases\n"
                "alias npm='sfw npm'\n"
                "# END socket-audit aliases\n"
                "after\n",
                encoding="utf-8",
            )

            result = self.run_uninstall(home)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(zshrc.read_text(encoding="utf-8"), "before\nafter\n")
            self.assertTrue((home / ".zshrc.socket-audit-backup").exists())

    def test_creation_header_does_not_claim_unmarked_bun_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            bunfig = home / ".bunfig.toml"
            bunfig.write_text(
                "# Created by the socket-audit skill.\n"
                "[install.security]\n"
                'scanner = "@socketsecurity/bun-security-scanner"\n'
                "[install]\n"
                "minimumReleaseAge = 7200\n",
                encoding="utf-8",
            )

            result = self.run_uninstall(home)
            content = bunfig.read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Created by the socket-audit", content)
            self.assertIn('scanner = "@socketsecurity/bun-security-scanner"', content)
            self.assertIn("minimumReleaseAge = 7200", content)
            self.assertIn("ownership is uncertain", result.stdout + result.stderr)

    def test_user_comment_prevents_deleting_a_created_bunfig(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            bunfig = home / ".bunfig.toml"
            bunfig.write_text(
                "# Created by the socket-audit skill.\n"
                "# Keep this user note.\n"
                "[install]\n"
                "minimumReleaseAge = 3600 # socket-audit\n",
                encoding="utf-8",
            )

            result = self.run_uninstall(home)
            content = bunfig.read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(bunfig.exists())
            self.assertIn("# Keep this user note.", content)
            self.assertNotIn("minimumReleaseAge", content)
            self.assertNotIn("Created by the socket-audit", content)


class PackageManagerDetectionTests(unittest.TestCase):
    def run_detect(
        self,
        output: Path,
        repos: Path,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/bash", str(DETECT), str(output), str(repos)],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_empty_survey_produces_valid_zero_count_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repos = root / "repos.txt"
            output = root / "report.json"
            repos.write_text("", encoding="utf-8")

            result = self.run_detect(output, repos)
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(report["total_repos_surveyed"], 0)

    def test_surveyed_audit_only_ecosystems_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            go_repo = root / "go-repo"
            maven_repo = root / "maven-repo"
            gradle_repo = root / "gradle-repo"
            for repo in (go_repo, maven_repo, gradle_repo):
                repo.mkdir()
            (go_repo / "go.mod").touch()
            (maven_repo / "pom.xml").touch()
            (gradle_repo / "build.gradle.kts").touch()
            bin_dir = root / "bin"
            bin_dir.mkdir()
            mvn = bin_dir / "mvn"
            mvn.write_text("#!/bin/sh\n", encoding="utf-8")
            mvn.chmod(0o755)
            repos = root / "repos.txt"
            repos.write_text(
                "\n".join(str(repo) for repo in (go_repo, maven_repo, gradle_repo)) + "\n",
                encoding="utf-8",
            )
            output = root / "report.json"
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

            result = self.run_detect(output, repos, env)
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(report["total_repos_surveyed"], 3)
            for manager in ("go", "maven", "gradle"):
                self.assertEqual(report["managers"][manager]["repo_count"], 1)
                self.assertFalse(report["managers"][manager]["wrapper_supported"])
                self.assertFalse(report["managers"][manager]["bun_scanner"])
            self.assertTrue(report["managers"]["maven"]["on_path"])


if __name__ == "__main__":
    unittest.main()
