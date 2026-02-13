"""Tests for demo script engine."""
from django.test import TestCase
from demo.demo_script import DEMO_SCRIPTS, get_script, list_scripts


class DemoScriptTest(TestCase):
    def test_scripts_not_empty(self):
        self.assertGreater(len(DEMO_SCRIPTS), 0)

    def test_full_showcase_exists(self):
        script = get_script("full_showcase")
        self.assertIsNotNone(script)
        self.assertEqual(script.name, "full_showcase")

    def test_behavioral_focus_exists(self):
        script = get_script("behavioral_focus")
        self.assertIsNotNone(script)

    def test_all_steps_have_required_fields(self):
        for name, script in DEMO_SCRIPTS.items():
            for step in script.steps:
                self.assertGreater(step.step_number, 0, f"Step in {name} has invalid number")
                self.assertTrue(step.title, f"Step {step.step_number} in {name} has no title")
                self.assertTrue(step.narration, f"Step {step.step_number} in {name} has no narration")
                self.assertTrue(step.api_endpoint, f"Step {step.step_number} in {name} has no endpoint")

    def test_duration_reasonable(self):
        for name, script in DEMO_SCRIPTS.items():
            self.assertGreater(script.total_duration_sec, 0)
            self.assertLessEqual(script.total_duration_sec, 600, f"{name} too long")

    def test_list_scripts(self):
        scripts = list_scripts()
        self.assertIsInstance(scripts, list)
        self.assertEqual(len(scripts), 2)
        names = {s["name"] for s in scripts}
        self.assertIn("full_showcase", names)
        self.assertIn("behavioral_focus", names)

    def test_nonexistent_script(self):
        result = get_script("does_not_exist")
        self.assertIsNone(result)

    def test_scripts_have_opening_closing(self):
        for name, script in DEMO_SCRIPTS.items():
            self.assertTrue(script.opening_line, f"{name} missing opening line")
            self.assertTrue(script.closing_line, f"{name} missing closing line")
