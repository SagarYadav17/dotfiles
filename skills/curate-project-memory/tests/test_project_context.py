"""Isolated behavioral tests; never touch the real vault or user instructions."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import project_context as pm
from build_context_pack import rank_context
import candidate_lifecycle as lifecycle


class SharedContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pmc-tests-")
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "PMC fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "code.py").write_text("value = 1\n")
        self.git("add", "code.py")
        self.git("commit", "-m", "fixture")
        self.vault = self.base / "vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.folder = self.vault / "Projects/Example"
        self.folder.mkdir(parents=True)
        for name, kind in (("Project.md", "project"), ("Project Home.md", "project-home"),
                           ("Current State.md", "current-state"), ("Handoff.md", "handoff")):
            (self.folder / name).write_text(f"---\ntype: {kind}\nproject_id: example\nstatus: active\nupdated: 2026-10-04\n---\n\n# {name}\n\nKeep this canonical text.\n")
        (self.folder / "Decisions").mkdir()
        (self.folder / "Decisions/Policy.md").write_text("---\ntype: decision\nproject_id: example\nstatus: accepted\nconfidence: confirmed\nupdated: 2026-10-04\n---\n# Policy\nKeep PKCE.\n")
        self.config = self.base / "configuration/config.json"
        self.config.parent.mkdir()
        self.data = {"schema_version": 1, "mode": "review", "vault_path": str(self.vault),
                     "session_summaries": {"enabled": False, "path": None},
                     "projects": {"example": {"name": "Example", "repo_path": str(self.repo), "vault_folder": "Projects/Example"}},
                     "automation": dict.fromkeys(pm.AUTO_DEFAULTS, True)}
        self.save_config()

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *arguments, repo=None):
        return subprocess.run(["git", "-C", str(repo or self.repo), *arguments], check=True, capture_output=True).stdout.decode().strip()

    def save_config(self):
        self.config.write_text(json.dumps(self.data))

    def payload(self, **updates):
        data = {"objective": "Fix redirect URI validation", "agent": "claude", "status": "active",
                "constraints": ["Preserve mandatory PKCE"], "completed": ["Inspected the current API"],
                "verification": ["Focused tests: 12 passed; production unverified"], "blockers": [],
                "next_actions": ["Update the Bruno request"], "decision_links": ["[[Decisions/Policy]]"]}
        data.update(updates)
        return data

    def save_task(self, **updates):
        return pm.checkpoint(self.config, self.repo, self.payload(**updates))

    def test_existing_configuration_keeps_automation_disabled(self):
        del self.data["automation"]
        self.save_config()
        found = pm.resume(self.config, self.repo, "continue")
        self.assertEqual(found["automation"], pm.AUTO_DEFAULTS)
        self.assertFalse(self.data["session_summaries"]["enabled"])
        with self.assertRaisesRegex(ValueError, "disabled"):
            self.save_task()
        self.assertFalse((self.folder / "Tasks").exists())

    def test_nested_and_worktree_resolution(self):
        nested = self.repo / "subdirectory"
        nested.mkdir()
        worktree = self.base / "worktree"
        self.git("worktree", "add", "-b", "feature", str(worktree))
        for path in (nested, worktree):
            found = pm.resolve(self.config, path)
            self.assertEqual(found["project_id"], "example")
            self.assertTrue(found["available"])

    def test_both_directions_resume_exact_progress_and_constraints(self):
        first = self.save_task()
        manifest = pm.resume(self.config, self.repo, "continue")
        task = manifest["selected_task"]
        self.assertEqual(task["task_id"], first["task_id"])
        self.assertEqual(task["constraints"], ["Preserve mandatory PKCE"])
        self.assertEqual(task["verification"], ["Focused tests: 12 passed; production unverified"])
        self.assertEqual(task["next_actions"], ["Update the Bruno request"])
        second = self.save_task(agent="codex", task_id=task["task_id"], expected_revision=task["saved_revision"],
                                completed=["Inspected the current API", "Updated Bruno"], next_actions=["Run integration checks"])
        resumed = pm.resume(self.config, self.repo, "continue")["selected_task"]
        self.assertEqual(resumed["agent"], "codex")
        self.assertEqual(resumed["saved_revision"], second["saved_revision"])
        self.assertEqual(resumed["completed"][-1], "Updated Bruno")
        self.assertEqual(resumed["next_actions"], ["Run integration checks"])

    def test_ambiguous_tasks_are_not_merged(self):
        first = self.save_task()
        second = self.save_task(objective="Optimize inventory lookup", next_actions=["Measure inventory query"])
        generic = pm.resume(self.config, self.repo, "continue")
        self.assertEqual(generic["selection"], "ambiguous")
        self.assertIsNone(generic["selected_task"])
        self.assertEqual(len(generic["task_candidates"]), 2)
        named = pm.resume(self.config, self.repo, "continue inventory")
        self.assertEqual(named["selected_task"]["task_id"], second["task_id"])
        explicit = pm.resume(self.config, self.repo, "continue " + first["task_id"])
        self.assertEqual(explicit["selected_task"]["task_id"], first["task_id"])
        self.assertEqual(pm.resume(self.config, self.repo, "Build unrelated notification flow")["selection"], "no_matching_task")

    def test_wrong_branch_and_detached_revision_do_not_resume(self):
        saved = self.save_task()
        self.git("checkout", "-b", "feature")
        result = pm.resume(self.config, self.repo, "continue", saved["task_id"])
        self.assertEqual(result["selection"], "branch_mismatch")
        self.assertIsNone(result["selected_task"])
        with self.assertRaisesRegex(ValueError, "another project, branch"):
            self.save_task(task_id=saved["task_id"], expected_revision=saved["saved_revision"])
        self.git("checkout", "--detach")
        detached = self.save_task()
        (self.repo / "code.py").write_text("value = 2\n")
        self.git("add", "code.py")
        self.git("commit", "-m", "different revision")
        self.assertEqual(pm.resume(self.config, self.repo, "continue", detached["task_id"])["selection"], "branch_mismatch")

    def test_dirty_contents_invalidate_saved_verification(self):
        (self.repo / "code.py").write_text("value = 2\n")
        self.save_task()
        (self.repo / "code.py").write_text("value = 3\n")
        result = pm.resume(self.config, self.repo, "continue")
        self.assertTrue(result["warnings"])
        self.assertEqual(result["selected_task"]["changed_paths"], ["code.py"])
        self.assertNotEqual(result["git"]["git_fingerprint"], result["selected_task"]["git_fingerprint"])

    def test_staged_and_unstaged_changes_are_both_in_snapshot(self):
        (self.repo / "code.py").write_text("value = 2\n")
        self.git("add", "code.py")
        (self.repo / "code.py").write_text("value = 1\n")
        first = pm.snapshot(self.repo)
        self.assertEqual(first["changed_paths"], ["code.py"])
        (self.repo / "code.py").write_text("value = 3\n")
        self.git("add", "code.py")
        (self.repo / "code.py").write_text("value = 1\n")
        self.assertNotEqual(first["git_fingerprint"], pm.snapshot(self.repo)["git_fingerprint"])

    def test_unchanged_payload_keeps_timestamp_and_file_revision(self):
        first = self.save_task()
        before = Path(first["file"]).read_bytes()
        second = self.save_task(agent="codex", task_id=first["task_id"], expected_revision=first["saved_revision"])
        self.assertTrue(second["unchanged"])
        self.assertEqual(first["saved_revision"], second["saved_revision"])
        self.assertEqual(before, Path(first["file"]).read_bytes())
        self.assertFalse(second["handoff_updated"])

    def test_stale_and_missing_revision_cannot_overwrite(self):
        first = self.save_task()
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.save_task(task_id=first["task_id"])
        second = self.save_task(task_id=first["task_id"], expected_revision=first["saved_revision"], blockers=["Waiting for API"])
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.save_task(task_id=first["task_id"], expected_revision=first["saved_revision"])
        self.assertEqual(pm.read_task(Path(first["file"]))["saved_revision"], second["saved_revision"])

    def test_competing_processes_keep_one_new_revision(self):
        first = self.save_task()
        processes = []
        for agent in ("claude", "codex"):
            payload = self.payload(agent=agent, task_id=first["task_id"], expected_revision=first["saved_revision"], completed=[agent + " milestone"])
            process = subprocess.Popen([sys.executable, str(SCRIPTS / "project_context.py"), "--config", str(self.config),
                                        "checkpoint", "--repo", str(self.repo)], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
            process.stdin = None
            processes.append(process)
        outputs = [process.communicate(timeout=10) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 1])
        self.assertTrue(any("Stale checkpoint" in error for _, error in outputs))
        task = pm.read_task(Path(first["file"]))
        self.assertEqual(len(task["completed"]), 1)
        self.assertIn(task["completed"][0], ["claude milestone", "codex milestone"])

    def test_completed_tasks_leave_resume_and_handoff_without_rewriting_canonical(self):
        handoff = self.folder / "Handoff.md"
        original = handoff.read_text()
        first = self.save_task()
        self.assertTrue(handoff.read_text().startswith(original))
        self.save_task(task_id=first["task_id"], expected_revision=first["saved_revision"], status="completed", next_actions=[])
        self.assertTrue(Path(first["file"]).exists())
        self.assertEqual(pm.resume(self.config, self.repo, "continue")["selection"], "no_matching_task")
        self.assertNotIn("[[Tasks/", handoff.read_text())
        ranked = rank_context(self.folder, "redirect")
        self.assertFalse(any(item["file"].startswith("Tasks/") for item in ranked["selected"]))
        history = rank_context(self.folder, "redirect", include_history=True)
        self.assertTrue(any(item["file"].startswith("Tasks/") for item in history["selected"]))

    def test_secrets_transcripts_and_escaping_links_are_rejected(self):
        for payload in (self.payload(completed=["password=fixture-secret"]),
                        self.payload(verification=["Bearer abcdefghijklmnopqrst"]),
                        self.payload(next_actions=["Inspect /home/fixture/private-file"]),
                        self.payload(decision_links=["[[../Other/Policy]]"]),
                        self.payload(transcript="Raw transcript")):
            with self.assertRaises(ValueError):
                pm.checkpoint(self.config, self.repo, payload)
        self.assertFalse((self.folder / "Tasks").exists())

    def test_missing_vault_and_unregistered_checkout_return_clear_context_state(self):
        self.assertFalse(pm.resolve(self.base / "absent.json", self.repo)["registered"])
        other = self.base / "unregistered"
        other.mkdir()
        self.git("init", "-b", "main", repo=other)
        self.assertEqual(pm.resume(self.config, other, "continue")["reason"], "repository_not_registered")
        (self.vault / ".obsidian").rmdir()
        result = pm.resume(self.config, self.repo, "continue")
        self.assertFalse(result["available"])
        self.assertTrue(result["warnings"])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.save_task()

    def test_install_is_idempotent_and_preserves_imports_symlinks_and_overrides(self):
        agents = self.repo / "AGENTS.md"
        original = "# Existing conventions\n\nPreserve unrelated work.\n"
        agents.write_text(original)
        claude = self.repo / "CLAUDE.md"
        claude.symlink_to("AGENTS.md")
        home = self.base / "user"
        (home / ".codex").mkdir(parents=True)
        (home / ".codex/AGENTS.override.md").write_text("Global override.\n")
        dry = pm.install(self.config, home=home, codex_home=home / ".codex", dry_run=True)
        self.assertTrue(dry["changed_files"])
        self.assertEqual(agents.read_text(), original)
        first = pm.install(self.config, home=home, codex_home=home / ".codex")
        self.assertTrue(first["changed_files"])
        self.assertTrue(claude.is_symlink())
        self.assertTrue(agents.read_text().startswith(original))
        self.assertEqual(agents.read_text().count("project-memory:start"), 1)
        self.assertEqual(pm.install(self.config, home=home, codex_home=home / ".codex")["changed_files"], [])
        claude.unlink()
        wrapper = "@AGENTS.md\n\nClaude-specific preference.\n"
        claude.write_text(wrapper)
        pm.install(self.config, home=home, codex_home=home / ".codex")
        self.assertEqual(claude.read_text(), wrapper)
        self.assertTrue((home / ".codex/AGENTS.override.md").read_text().startswith("Global override.\n"))
        self.assertFalse((home / ".codex/AGENTS.md").exists())

    def test_install_nine_registrations_preserves_existing_three(self):
        registrations = {}
        for number in range(1, 9):
            project_id = f"example-{number}"
            repo = self.base / project_id
            repo.mkdir()
            self.git("init", "-b", "main", repo=repo)
            folder = self.vault / "Projects" / project_id
            folder.mkdir()
            (folder / "Project.md").write_text(f"---\ntype: project\nproject_id: {project_id}\nstatus: active\n---\n# Example\n")
            registrations[project_id] = {"name": project_id, "repo_path": str(repo), "vault_folder": "Projects/" + project_id}
        self.data["projects"].update({key: registrations.pop(key) for key in ("example-1", "example-2")})
        del self.data["automation"]
        self.save_config()
        existing = dict(self.data["projects"])
        home = self.base / "user"
        installed = pm.install(self.config, registrations, enable=True, home=home, codex_home=home / ".codex")
        self.assertEqual(len(installed["projects"]), 9)
        loaded = pm.load_config(self.config)
        self.assertTrue(all(loaded["projects"][key] == value for key, value in existing.items()))
        self.assertFalse(loaded["session_summaries"]["enabled"])
        for entry in loaded["projects"].values():
            self.assertTrue(pm.resolve(self.config, Path(entry["repo_path"]))["registered"])

    def test_unavailable_registration_stops_before_instruction_changes(self):
        self.data["projects"]["missing"] = {"name": "Missing", "repo_path": str(self.base / "absent"), "vault_folder": "Projects/Missing"}
        self.save_config()
        with self.assertRaises(ValueError):
            pm.install(self.config, home=self.base / "user")
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_malformed_guidance_stops_install_without_overwriting(self):
        agents = self.repo / "AGENTS.md"
        original = "Original rules.\n<!-- project-memory:start -->\nUnfinished user edit.\n"
        agents.write_text(original)
        with self.assertRaisesRegex(ValueError, "Malformed"):
            pm.install(self.config, home=self.base / "user")
        self.assertEqual(agents.read_text(), original)

    def test_claude_only_and_codex_override_guidance_are_preserved(self):
        claude = self.repo / "CLAUDE.md"
        original = "# Existing build rules\n\nUse the pinned runtime.\n"
        claude.write_text(original)
        home = self.base / "user"
        pm.install(self.config, home=home, codex_home=home / ".codex")
        self.assertTrue(claude.read_text().startswith(original))
        self.assertIn("Read `CLAUDE.md`", (self.repo / "AGENTS.md").read_text())
        override = self.repo / "AGENTS.override.md"
        override.write_text("Keep the override rules.\n")
        pm.install(self.config, home=home, codex_home=home / ".codex")
        self.assertTrue(override.read_text().startswith("Keep the override rules.\n"))
        self.assertIn("project-memory:start", override.read_text())

    def test_busy_project_lock_stops_writer_without_partial_checkpoint(self):
        with pm.project_lock(self.config, "example"):
            process = subprocess.run([sys.executable, str(SCRIPTS / "project_context.py"), "--config", str(self.config),
                                      "checkpoint", "--repo", str(self.repo)], input=json.dumps(self.payload()),
                                     capture_output=True, text=True, timeout=5)
        self.assertEqual(process.returncode, 1)
        self.assertIn("being updated", process.stderr)
        self.assertFalse((self.folder / "Tasks").exists())

    def test_health_checker_accepts_generated_checkpoint(self):
        self.save_task()
        result = subprocess.run([sys.executable, str(SCRIPTS / "check_vault_health.py"), str(self.folder)], capture_output=True, text=True)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"]["errors"], 0)

    def test_handoff_failure_does_not_hide_saved_checkpoint(self):
        handoff = self.folder / "Handoff.md"
        original = handoff.read_text() + "\n<!-- project-memory:tasks:start -->\nUnfinished edit.\n"
        handoff.write_text(original)
        saved = self.save_task()
        self.assertTrue(saved["warnings"])
        self.assertTrue(Path(saved["file"]).exists())
        self.assertEqual(handoff.read_text(), original)
        self.assertEqual(pm.resume(self.config, self.repo, "continue")["selected_task"]["task_id"], saved["task_id"])

    def test_bad_config_and_missing_task_fail_without_writes(self):
        self.data["automation"]["save_progress"] = "true"
        self.save_config()
        with self.assertRaisesRegex(ValueError, "booleans"):
            self.save_task()
        self.data["automation"]["save_progress"] = True
        self.save_config()
        with self.assertRaisesRegex(ValueError, "not found"):
            self.save_task(task_id="task-000000000000", expected_revision="0" * 64)
        self.assertFalse((self.folder / "Tasks").exists())

    def test_conflicting_decision_cannot_bypass_review_fingerprint(self):
        text = "### PM-001 - Change OAuth policy\n- Status: pending\n- Operation: conflict\n- Target: Decisions/Policy.md\n- Confidence: confirmed\n- Evidence: user choice\n- Proposed change: retain PKCE\n- Conflicts: existing policy\n- Existing claim: retain PKCE\n- Existing evidence: accepted note\n- Conflict resolution: undecided\n"
        with self.assertRaises(ValueError):
            lifecycle.transition(text, "PM-001", "applying")
        approved = lifecycle.transition(text, "PM-001", "approved", actor="user", at="2026-10-04")
        changed = approved.replace("- Proposed change: retain PKCE", "- Proposed change: disable PKCE")
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            lifecycle.transition(changed, "PM-001", "applying")


if __name__ == "__main__":
    unittest.main()
