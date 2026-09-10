"""Run with python3 -m unittest discover -s tests."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class HookTests(unittest.TestCase):
    def test_installed_hooks_deliver_complete_soul(self):
        source = Path(__file__).resolve().parents[1]
        expected = (source / "SOUL.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "plugin with spaces"
            shutil.copytree(source / "hooks", installed / "hooks")
            shutil.copyfile(source / "SOUL.md", installed / "SOUL.md")
            config = json.loads((installed / "hooks/hooks.json").read_text())
            env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(installed))
            env.pop("PLUGIN_ROOT", None)
            for event in ("SessionStart", "SubagentStart"):
                with self.subTest(event=event):
                    command = config["hooks"][event][0]["hooks"][0]["command"]
                    result = subprocess.run(
                        command, shell=True, cwd=directory, env=env,
                        input=json.dumps({"hook_event_name": event}),
                        text=True, capture_output=True, check=True,
                    )
                    self.assertEqual(json.loads(result.stdout), {
                        "hookSpecificOutput": {
                            "hookEventName": event,
                            "additionalContext": expected,
                        },
                    })

    def test_invalid_input_produces_no_context(self):
        script = Path(__file__).resolve().parents[1] / "hooks/inject.py"
        for payload in ('{}', 'not json', '{"hook_event_name": "Stop"}'):
            with self.subTest(payload=payload):
                result = subprocess.run(
                    ["python3", str(script)], input=payload,
                    text=True, capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
