from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def run(*arguments: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def executable(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def skill(path: Path, name: str) -> None:
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Fixture skill.\n---\n\n# {name}\n",
        encoding="utf-8",
    )


class DevSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "dev-skill", self.repo / "scripts" / "dev-skill")
        skill(self.repo / "skills" / "alpha", "alpha")
        skill(self.repo / "skills" / "beta", "beta")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return run(str(self.repo / "scripts" / "dev-skill"), *arguments, cwd=self.repo)

    def test_link_switch_status_and_remove(self) -> None:
        first = self.command("alpha")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        link = self.repo / "local" / "sandbox" / ".agents" / "skills" / "alpha"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), (self.repo / "skills" / "alpha").resolve())

        second = self.command("beta")
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertFalse(link.exists())
        beta = link.parent / "beta"
        self.assertEqual(beta.resolve(), (self.repo / "skills" / "beta").resolve())

        status = self.command("--status")
        self.assertEqual(status.returncode, 0)
        self.assertIn("dev_skill=linked skill=beta", status.stdout)

        removed = self.command("--remove")
        self.assertEqual(removed.returncode, 0)
        self.assertFalse(beta.exists())
        self.assertIn("dev_skill=removed", removed.stdout)

    def test_same_skill_activation_is_idempotent(self) -> None:
        first = self.command("alpha")
        second = self.command("alpha")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        self.assertEqual([path.name for path in target.iterdir()], ["alpha"])

    def test_remove_preserves_unmanaged_entry(self) -> None:
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        target.mkdir(parents=True)
        unmanaged = target / "notes"
        unmanaged.write_text("keep\n", encoding="utf-8")
        result = self.command("--remove")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(unmanaged.exists())
        self.assertIn(f"dev_skill=unmanaged path={unmanaged}", result.stdout)
        self.assertNotIn("dev_skill=inactive", result.stdout)
        self.assertIn("unmanaged sandbox entries remain active", result.stderr)

    def test_remove_deletes_managed_link_but_reports_remaining_unmanaged_entry(self) -> None:
        linked = self.command("alpha")
        self.assertEqual(linked.returncode, 0, linked.stdout + linked.stderr)
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        unmanaged = target / "notes"
        unmanaged.write_text("keep\n", encoding="utf-8")
        result = self.command("--remove")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((target / "alpha").exists())
        self.assertTrue(unmanaged.exists())
        self.assertIn("dev_skill=removed", result.stdout)
        self.assertIn(f"dev_skill=unmanaged path={unmanaged}", result.stdout)

    def test_unknown_and_malformed_names_fail(self) -> None:
        unknown = self.command("missing")
        self.assertEqual(unknown.returncode, 1)
        self.assertIn("unknown skill", unknown.stderr)
        malformed = self.command("../alpha")
        self.assertEqual(malformed.returncode, 1)
        self.assertIn("invalid skill name", malformed.stderr)

    def test_unmanaged_entry_is_preserved(self) -> None:
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        target.mkdir(parents=True)
        unmanaged = target / "notes"
        unmanaged.write_text("keep\n", encoding="utf-8")
        result = self.command("alpha")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(unmanaged.exists())
        self.assertIn("unmanaged sandbox entry", result.stderr)

    def test_hidden_unmanaged_entry_is_preserved(self) -> None:
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        target.mkdir(parents=True)
        unmanaged = target / ".hidden"
        unmanaged.write_text("keep\n", encoding="utf-8")
        result = self.command("alpha")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(unmanaged.exists())
        self.assertIn("unmanaged sandbox entry", result.stderr)

    def test_unmanaged_entry_does_not_remove_current_managed_link(self) -> None:
        linked = self.command("alpha")
        self.assertEqual(linked.returncode, 0, linked.stdout + linked.stderr)
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        unmanaged = target / "notes"
        unmanaged.write_text("keep\n", encoding="utf-8")
        result = self.command("beta")
        self.assertEqual(result.returncode, 1)
        self.assertTrue((target / "alpha").is_symlink())
        self.assertTrue(unmanaged.exists())

    def test_symlinked_source_skill_is_rejected(self) -> None:
        outside = Path(self.temporary.name) / "outside-skill"
        skill(outside, "linked")
        (self.repo / "skills" / "linked").symlink_to(outside, target_is_directory=True)
        result = self.command("linked")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing symlinked source skill", result.stderr)

    def test_broken_managed_link_is_reported(self) -> None:
        target = self.repo / "local" / "sandbox" / ".agents" / "skills"
        target.mkdir(parents=True)
        (target / "missing").symlink_to("../../../../skills/missing")
        result = self.command("--status")
        self.assertEqual(result.returncode, 1)
        self.assertIn("dev_skill=broken skill=missing", result.stdout)

    def test_symlinked_sandbox_parent_is_rejected(self) -> None:
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (self.repo / "local").symlink_to(outside, target_is_directory=True)
        result = self.command("alpha")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing to use symlinked sandbox directory", result.stderr)

    def test_file_in_sandbox_parent_path_is_rejected(self) -> None:
        (self.repo / "local").write_text("not a directory\n", encoding="utf-8")
        result = self.command("alpha")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sandbox path is not a directory", result.stderr)


class ReadmeCatalogueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "check-readme-links.py", self.repo / "scripts" / "check-readme-links.py")
        skill(self.repo / "skills" / "alpha", "alpha")
        skill(self.repo / "skills" / "beta", "beta")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def check(self, catalogue: str) -> subprocess.CompletedProcess[str]:
        (self.repo / "README.md").write_text(
            f"# Fixture\n\n## Skills\n\n{catalogue}\n\n## Install\n",
            encoding="utf-8",
        )
        return run(str(self.repo / "scripts" / "check-readme-links.py"), cwd=self.repo)

    def test_exact_catalogue_passes(self) -> None:
        result = self.check("- [alpha](skills/alpha/)\n- [beta](skills/beta/)")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_skill_fails(self) -> None:
        result = self.check("- [alpha](skills/alpha/)")
        self.assertEqual(result.returncode, 1)
        self.assertIn("catalogue omits public skills: beta", result.stderr)

    def test_duplicate_skill_fails(self) -> None:
        result = self.check(
            "- [alpha](skills/alpha/)\n- [alpha again](skills/alpha/)\n- [beta](skills/beta/)"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("catalogue lists skills more than once: alpha", result.stderr)

    def test_missing_catalogue_section_fails(self) -> None:
        (self.repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
        result = run(str(self.repo / "scripts" / "check-readme-links.py"), cwd=self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing a '## Skills' catalogue", result.stderr)

    def test_repository_escaping_link_fails(self) -> None:
        result = self.check(
            "- [alpha](skills/alpha/)\n- [beta](skills/beta/)\n- [outside](../outside.md)"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("link escapes the repository", result.stderr)


class CheckRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "check-repo", self.repo / "scripts" / "check-repo")
        shutil.copy2(
            SCRIPTS / "check-readme-links.py",
            self.repo / "scripts" / "check-readme-links.py",
        )
        builder = self.repo / "skills" / "skill-builder"
        skill(builder, "skill-builder")
        executable(
            builder / "scripts" / "validate_skill.py",
            "#!/usr/bin/env python3\nprint('fixture_validation=passed')\n",
        )
        (self.repo / "README.md").write_text(
            "# Fixture\n\n## Skills\n\n- [skill-builder](skills/skill-builder/)\n\n## Install\n",
            encoding="utf-8",
        )
        (self.repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        run("git", "init", "-q", cwd=self.repo)
        run("git", "add", ".", cwd=self.repo)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def command(self, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return run(str(self.repo / "scripts" / "check-repo"), cwd=self.repo, env=env)

    def test_invalid_size_limit_fails_early(self) -> None:
        environment = os.environ.copy()
        environment["MAX_TRACKED_FILE_BYTES"] = "invalid"
        result = self.command(env=environment)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be a positive integer", result.stderr)

    def test_tracked_local_artifact_is_rejected(self) -> None:
        leak = self.repo / "local" / "leak.txt"
        leak.parent.mkdir()
        leak.write_text("private fixture\n", encoding="utf-8")
        run("git", "add", "-f", "local/leak.txt", cwd=self.repo)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked development artifact", result.stderr)

    def test_oversized_tracked_file_is_rejected(self) -> None:
        environment = os.environ.copy()
        environment["MAX_TRACKED_FILE_BYTES"] = "10"
        result = self.command(env=environment)
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked file exceeds 10 bytes", result.stderr)

    def test_non_executable_repository_command_is_rejected(self) -> None:
        helper = self.repo / "scripts" / "helper"
        helper.write_text("fixture\n", encoding="utf-8")
        helper.chmod(0o644)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("repository command is not executable: scripts/helper", result.stderr)

    def test_root_cache_artifact_is_rejected(self) -> None:
        cache = self.repo / "__pycache__" / "state.bin"
        cache.parent.mkdir()
        cache.write_bytes(b"cache")
        run("git", "add", "-f", "__pycache__/state.bin", cwd=self.repo)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked development artifact", result.stderr)

    def test_tracked_symlink_cannot_escape_repository(self) -> None:
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        (self.repo / "escape").symlink_to(outside)
        run("git", "add", "escape", cwd=self.repo)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked symlink escapes the repository", result.stderr)

    def test_broken_tracked_symlink_is_rejected(self) -> None:
        (self.repo / "broken").symlink_to("missing-target")
        run("git", "add", "broken", cwd=self.repo)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("tracked symlink is broken", result.stderr)

    def test_public_skill_directory_cannot_be_a_symlink(self) -> None:
        original = self.repo / "skills" / "skill-builder"
        outside = Path(self.temporary.name) / "outside-builder"
        shutil.move(original, outside)
        original.symlink_to(outside, target_is_directory=True)
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("public skill directory must not be a symlink", result.stderr)


class FullCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "check-full", self.repo / "scripts" / "check-full")
        executable(self.repo / "scripts" / "check-repo", "#!/bin/sh\necho repository_check=passed\n")
        fake_bin = Path(self.temporary.name) / "bin"
        executable(
            fake_bin / "python3",
            '#!/bin/sh\nprintf "%s\\n" "$*" > "$PYTHON_LOG"\nexit 0\n',
        )
        self.env = os.environ.copy()
        self.env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
        self.python_log = Path(self.temporary.name) / "python.log"
        self.env["PYTHON_LOG"] = str(self.python_log)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_optional_gateway_dependency_is_reported(self) -> None:
        result = run(str(self.repo / "scripts" / "check-full"), cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("integrations_run=1 integrations_skipped=1", result.stdout)
        arguments = self.python_log.read_text(encoding="utf-8")
        self.assertIn("-m unittest discover -s", arguments)
        self.assertIn("test_companion_integration.py", arguments)

    def test_strict_mode_rejects_skipped_integration(self) -> None:
        result = run(str(self.repo / "scripts" / "check-full"), "--strict", cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("--strict requires", result.stderr)

    def test_custom_gateway_binary_override_runs_integration(self) -> None:
        fake_bin = Path(self.temporary.name) / "bin"
        executable(fake_bin / "jq", "#!/bin/sh\nexit 0\n")
        custom_proxy = fake_bin / "custom-proxy"
        executable(custom_proxy, "#!/bin/sh\nexit 0\n")
        gateway_test = (
            self.repo
            / "skills"
            / "setup-cli-proxy-gateway"
            / "scripts"
            / "test_custom_endpoint_mock.sh"
        )
        executable(gateway_test, "#!/bin/sh\necho gateway_fixture=passed\n")
        environment = self.env.copy()
        environment["CLI_PROXY_BIN"] = str(custom_proxy)
        result = run(str(self.repo / "scripts" / "check-full"), cwd=self.repo, env=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("integrations_run=2 integrations_skipped=0", result.stdout)

    def test_fast_check_failure_stops_full_check(self) -> None:
        executable(self.repo / "scripts" / "check-repo", "#!/bin/sh\nexit 7\n")
        result = run(str(self.repo / "scripts" / "check-full"), cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 7)
        self.assertNotIn("Web Traffic Inspector", result.stdout)


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "check-release", self.repo / "scripts" / "check-release")
        executable(self.repo / "scripts" / "check-repo", "#!/bin/sh\necho repository_check=passed\n")
        executable(
            self.repo / "scripts" / "check-full",
            "#!/bin/sh\nprintf 'full_check_args=%s\\n' \"$#\"\n",
        )
        skill(self.repo / "skills" / "alpha", "alpha")
        skill(self.repo / "skills" / "beta", "beta")
        (self.repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        self.fake_npx = Path(self.temporary.name) / "fake-npx"
        executable(
            self.fake_npx,
            textwrap.dedent(
                """\
                #!/bin/sh
                printf '◇  Found 2 skills\n'
                printf '│    alpha\n'
                printf '│    beta\n'
                """
            ),
        )
        self.env = os.environ.copy()
        self.env["SKILLS_NPX_BIN"] = str(self.fake_npx)
        self.env["SKILLS_CLI_PACKAGE"] = "fixture-cli"

        run("git", "init", "-q", cwd=self.repo)
        run("git", "config", "user.email", "fixture@example.com", cwd=self.repo)
        run("git", "config", "user.name", "Fixture", cwd=self.repo)
        run("git", "add", ".", cwd=self.repo)
        committed = run("git", "commit", "-qm", "fixture", cwd=self.repo)
        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.branch = run("git", "branch", "--show-current", cwd=self.repo).stdout.strip()
        self.commit = run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        self.fake_git = Path(self.temporary.name) / "fake-git"
        self.set_remote_head(self.commit, self.branch)
        self.env["SKILLS_GIT_BIN"] = str(self.fake_git)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return run(
            str(self.repo / "scripts" / "check-release"),
            "--skip-full",
            *arguments,
            cwd=self.repo,
            env=self.env,
        )

    def set_remote_head(self, commit: str, branch: str) -> None:
        real_git = shutil.which("git")
        assert real_git is not None
        executable(
            self.fake_git,
            textwrap.dedent(
                f"""\
                #!/bin/sh
                if [ "$1" = "ls-remote" ]; then
                  printf 'ref: refs/heads/{branch}\\tHEAD\\n'
                  printf '{commit}\\tHEAD\\n'
                  exit 0
                fi
                exec {real_git} "$@"
                """
            ),
        )

    def test_clean_local_discovery_passes(self) -> None:
        result = self.command()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("release_check=passed", result.stdout)
        self.assertIn("skills=2", result.stdout)

    def test_default_full_check_passes_without_arguments(self) -> None:
        result = run(
            str(self.repo / "scripts" / "check-release"),
            cwd=self.repo,
            env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("full_check_args=0", result.stdout)

    def test_dirty_worktree_fails_without_override(self) -> None:
        (self.repo / "README.md").write_text("dirty\n", encoding="utf-8")
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("clean worktree", result.stderr)
        allowed = self.command("--allow-dirty")
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
        self.assertIn("uncommitted changes are excluded", allowed.stderr)
        self.assertIn("worktree_dirty=yes", allowed.stdout)

    def test_discovery_mismatch_fails(self) -> None:
        executable(self.fake_npx, "#!/bin/sh\nprintf '│    alpha\\n'\n")
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("CLI discovery does not match", result.stderr)

    def test_duplicate_discovery_fails(self) -> None:
        executable(
            self.fake_npx,
            "#!/bin/sh\nprintf '│    alpha\\n│    alpha\\n│    beta\\n'\n",
        )
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("CLI discovery contains duplicate skill names", result.stderr)
        self.assertIn("alpha", result.stderr)

    def test_discovery_command_failure_is_reported(self) -> None:
        executable(self.fake_npx, "#!/bin/sh\necho fixture failure >&2\nexit 9\n")
        result = self.command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("fixture failure", result.stderr)
        self.assertIn("skills CLI discovery failed", result.stderr)

    def test_remote_source_syntax_is_validated(self) -> None:
        result = self.command("--remote", "not-a-repository")
        self.assertEqual(result.returncode, 2)
        self.assertIn("OWNER/REPO", result.stderr)

    def test_strict_and_skip_full_are_incompatible(self) -> None:
        result = self.command("--strict")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot be combined", result.stderr)

    def test_remote_discovery_passes(self) -> None:
        result = self.command("--remote", "owner/repository")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source=owner/repository", result.stdout)
        self.assertIn("remote_head=passed", result.stdout)
        self.assertIn("remote_checked=yes", result.stdout)

    def test_remote_commit_must_match_local_head(self) -> None:
        self.set_remote_head("0" * 40, self.branch)
        result = self.command("--remote", "owner/repository")
        self.assertEqual(result.returncode, 1)
        self.assertIn("is not at local HEAD", result.stderr)

    def test_remote_default_branch_must_match_current_branch(self) -> None:
        other_branch = "other" if self.branch != "other" else "different"
        self.set_remote_head(self.commit, other_branch)
        result = self.command("--remote", "owner/repository")
        self.assertEqual(result.returncode, 1)
        self.assertIn("is not the public default branch", result.stderr)

    def test_missing_mit_license_is_rejected(self) -> None:
        (self.repo / "LICENSE").write_text("Different license\n", encoding="utf-8")
        result = self.command("--allow-dirty")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not recognizably MIT", result.stderr)


if __name__ == "__main__":
    unittest.main()
