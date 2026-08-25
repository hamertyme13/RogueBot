"""
RogueBot automated test suite.

Run with:  venv/bin/python -m pytest tests/ -v
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# memory.py
# ---------------------------------------------------------------------------

class TestMemoryManager:

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        from memory import MemoryManager
        self.mem = MemoryManager(self.tmp.name)

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_remember_and_recall(self):
        self.mem.remember("favourite colour", "blue")
        assert self.mem.recall("favourite colour") == "blue"

    def test_recall_missing(self):
        assert self.mem.recall("nonexistent") is None

    def test_forget(self):
        self.mem.remember("pet", "dog")
        assert self.mem.forget("pet") is True
        assert self.mem.recall("pet") is None

    def test_forget_missing(self):
        assert self.mem.forget("ghost") is False

    def test_get_all(self):
        self.mem.remember("a", "1")
        self.mem.remember("b", "2")
        data = self.mem.get_all()
        assert data == {"a": "1", "b": "2"}

    def test_keys_normalised_lowercase(self):
        self.mem.remember("My Key", "value")
        assert self.mem.recall("my key") == "value"


# ---------------------------------------------------------------------------
# skills/memory_skill.py
# ---------------------------------------------------------------------------

class TestMemorySkill:

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        import skills.memory_skill as ms
        from memory import MemoryManager
        ms.memory = MemoryManager(self.tmp.name)
        self.ms = ms

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_remember_fact(self):
        resp = self.ms.remember_fact("remember that my city is Austin")
        assert "Austin" in resp

    def test_remember_fact_missing_is(self):
        resp = self.ms.remember_fact("remember that something")
        assert "format" in resp.lower() or "remember" in resp.lower()

    def test_recall_fact(self):
        self.ms.remember_fact("remember that my dog is Rex")
        resp = self.ms.recall_fact("what is my dog")
        assert "Rex" in resp

    def test_recall_fact_missing(self):
        resp = self.ms.recall_fact("what is purple elephant")
        assert "don't remember" in resp.lower()

    def test_forget_fact(self):
        self.ms.remember_fact("remember that test key is test value")
        resp = self.ms.forget_fact("forget test key")
        assert "forgot" in resp.lower()

    def test_list_memories_empty(self):
        resp = self.ms.list_memories()
        assert "no saved" in resp.lower() or "don't have" in resp.lower()

    def test_list_memories(self):
        self.ms.remember_fact("remember that colour is red")
        resp = self.ms.list_memories()
        assert "colour" in resp and "red" in resp


# ---------------------------------------------------------------------------
# skills/notes_skill.py
# ---------------------------------------------------------------------------

class TestNotesSkill:

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        import skills.notes_skill as ns
        ns._NOTES_FILE = Path(self.tmp.name)
        # Start fresh
        Path(self.tmp.name).write_text("{}")
        self.ns = ns

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_add_and_read(self):
        self.ns.add_note("add milk to my shopping list")
        resp = self.ns.read_list("read my shopping list")
        assert "milk" in resp

    def test_add_duplicate_not_doubled(self):
        self.ns.add_note("add milk to my shopping list")
        self.ns.add_note("add milk to my shopping list")
        resp = self.ns.read_list("read my shopping list")
        assert resp.count("milk") == 1

    def test_read_empty(self):
        resp = self.ns.read_list("read my shopping list")
        assert "empty" in resp.lower()

    def test_clear_list(self):
        self.ns.add_note("add eggs to my shopping list")
        resp = self.ns.clear_list("clear my shopping list")
        assert "cleared" in resp.lower()
        assert "empty" in self.ns.read_list("read my shopping list").lower()

    def test_clear_nonexistent(self):
        resp = self.ns.clear_list("clear my shopping list")
        assert "don't have" in resp.lower()


# ---------------------------------------------------------------------------
# skills/timer_skill.py
# ---------------------------------------------------------------------------

class TestTimerSkill:

    def test_parse_seconds(self):
        from skills.timer_skill import set_timer
        resp = set_timer("set a timer for 30 seconds")
        assert "30 second" in resp

    def test_parse_minutes(self):
        from skills.timer_skill import set_timer
        resp = set_timer("set a timer for 5 minutes")
        assert "5 minute" in resp

    def test_parse_hours(self):
        from skills.timer_skill import set_timer
        resp = set_timer("timer 2 hours")
        assert "2 hour" in resp

    def test_parse_singular(self):
        from skills.timer_skill import set_timer
        resp = set_timer("set a timer for 1 minute")
        assert "1 minute." in resp  # no trailing 's'

    def test_invalid(self):
        from skills.timer_skill import set_timer
        resp = set_timer("set a timer")
        assert "didn't catch" in resp.lower()

    def test_list_timers_empty(self):
        from skills.timer_skill import list_timers, _active_timers
        _active_timers.clear()
        resp = list_timers()
        assert "no active" in resp.lower()

    def test_cancel_timers_none(self):
        from skills.timer_skill import cancel_timers, _active_timers
        _active_timers.clear()
        resp = cancel_timers()
        assert "no active" in resp.lower()


# ---------------------------------------------------------------------------
# skills/reminder_skill.py
# ---------------------------------------------------------------------------

class TestReminderSkill:

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        import skills.reminder_skill as rs
        rs._REMINDERS_FILE = Path(self.tmp.name)
        Path(self.tmp.name).write_text("[]")
        self.rs = rs

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_add_invalid_no_at(self):
        resp = self.rs.add_reminder("remind me something")
        assert "try saying" in resp.lower() or "tell me" in resp.lower()

    def test_add_invalid_no_to(self):
        resp = self.rs.add_reminder("remind me at 3pm")
        assert "tell me" in resp.lower() or "example" in resp.lower()

    def test_list_empty(self):
        resp = self.rs.list_reminders()
        assert "no" in resp.lower()

    def test_cancel_all_empty(self):
        resp = self.rs.cancel_reminder("cancel all reminders")
        assert "no reminders" in resp.lower()


# ---------------------------------------------------------------------------
# skills/calc_skill.py
# ---------------------------------------------------------------------------

class TestCalcSkill:

    def setup_method(self):
        from skills.calc_skill import calculate
        self.calc = calculate

    def test_addition(self):
        assert "12" in self.calc("what is 7 plus 5")

    def test_multiplication(self):
        assert "56" in self.calc("what is 7 times 8")

    def test_percentage(self):
        resp = self.calc("what is 10% of 200")
        assert "20" in resp

    def test_f_to_c(self):
        resp = self.calc("convert 32 fahrenheit to celsius")
        assert "0" in resp

    def test_c_to_f(self):
        resp = self.calc("convert 100 celsius to fahrenheit")
        assert "212" in resp

    def test_km_to_miles(self):
        resp = self.calc("convert 1 kilometre to miles")
        assert "0.621" in resp

    def test_invalid(self):
        resp = self.calc("calculate flibbertigibbet")
        assert "couldn't" in resp.lower()


# ---------------------------------------------------------------------------
# plugin_loader.py
# ---------------------------------------------------------------------------

class TestPluginLoader:

    def test_load_and_dispatch(self, tmp_path):
        """Write a minimal plugin and verify dispatch works."""
        plugin_src = (
            'TRIGGERS = ["hello plugin"]\n'
            'def handle(command): return "plugin response"\n'
        )
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text(plugin_src)

        from plugin_loader import _load_plugin, dispatch_plugins
        module = _load_plugin(plugin_file)
        assert module is not None

        resp = dispatch_plugins([module], "hello plugin today")
        assert resp == "plugin response"

    def test_no_triggers_not_loaded(self, tmp_path):
        """A file without TRIGGERS should not be treated as a plugin."""
        plugin_file = tmp_path / "no_trigger.py"
        plugin_file.write_text("def handle(cmd): return 'hi'\n")

        from plugin_loader import _load_plugin
        assert _load_plugin(plugin_file) is None

    def test_no_handle_not_loaded(self, tmp_path):
        plugin_file = tmp_path / "no_handle.py"
        plugin_file.write_text('TRIGGERS = ["x"]\n')

        from plugin_loader import _load_plugin
        assert _load_plugin(plugin_file) is None

    def test_dispatch_no_match(self, tmp_path):
        plugin_src = 'TRIGGERS = ["special trigger"]\ndef handle(cmd): return "hi"\n'
        plugin_file = tmp_path / "p.py"
        plugin_file.write_text(plugin_src)

        from plugin_loader import _load_plugin, dispatch_plugins
        module = _load_plugin(plugin_file)
        resp = dispatch_plugins([module], "something completely different")
        assert resp is None


# ---------------------------------------------------------------------------
# startup_check.py (mocked network)
# ---------------------------------------------------------------------------

class TestStartupCheck:

    def test_all_ok(self):
        with (
            patch("startup_check._check_ollama", return_value=True),
            patch("startup_check._check_openai", return_value=True),
            patch("startup_check._check_internet", return_value=True),
        ):
            from startup_check import run_startup_checks
            result = run_startup_checks()
        assert "local ai is online" in result.lower()
        assert "cloud ai is configured" in result.lower()

    def test_ollama_down(self):
        with (
            patch("startup_check._check_ollama", return_value=False),
            patch("startup_check._check_openai", return_value=True),
            patch("startup_check._check_internet", return_value=True),
        ):
            from startup_check import run_startup_checks
            result = run_startup_checks()
        assert "offline" in result.lower()

    def test_no_internet(self):
        with (
            patch("startup_check._check_ollama", return_value=True),
            patch("startup_check._check_openai", return_value=True),
            patch("startup_check._check_internet", return_value=False),
        ):
            from startup_check import run_startup_checks
            result = run_startup_checks()
        assert "internet" in result.lower()
