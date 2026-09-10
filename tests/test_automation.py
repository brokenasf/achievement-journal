import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('achievements', Path(__file__).resolve().parents[1] / 'scripts/achievements.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class AutomationTests(unittest.TestCase):
    def check(self, status='completed', conclusion='success', name='test', id=1):
        return {'id': id, 'name': name, 'status': status, 'conclusion': conclusion}

    def test_missing_checks_never_merge(self):
        self.assertFalse(app.checks_ready([], [], ['test']))
        self.assertFalse(app.checks_ready([self.check(name='unrelated')], [], ['test']))

    def test_pending_skipped_and_failed_checks(self):
        self.assertFalse(app.checks_ready([self.check(status='in_progress', conclusion=None)], [], ['test']))
        self.assertFalse(app.checks_ready([self.check(conclusion='skipped')], [], ['test']))
        with self.assertRaises(app.AutomationError):
            app.checks_ready([self.check(conclusion='failure')], [], ['test'])

    def test_success_and_latest_rerun(self):
        self.assertTrue(app.checks_ready([self.check()], [], ['test']))
        self.assertTrue(app.checks_ready([self.check(conclusion='failure'), self.check(id=2)], [], ['test']))
        self.assertFalse(app.checks_ready([self.check()], [{'context':'external', 'state':'pending'}], ['test']))

    def test_secret_paths(self):
        for path in ['token.txt', 'foo/token.txt', '.env', '.env.production', '.git/config', '.artifacts/report.json', 'private.key']:
            self.assertTrue(app.sensitive_path(Path(path)), path)
        self.assertFalse(app.sensitive_path(Path('scripts/achievements.py')))

    def test_progress_thresholds(self):
        self.assertEqual(app.tier_progress(15, [2,16,128,1024])['remaining'], 1)
        self.assertEqual(app.tier_progress(16, [2,16,128,1024])['estimated_level'], 2)
        self.assertIsNone(app.tier_progress(1024, [2,16,128,1024])['next_threshold'])


if __name__ == '__main__':
    unittest.main()
