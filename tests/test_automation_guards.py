import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('achievements',Path(__file__).resolve().parents[1]/'scripts/achievements.py')
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class Guards(unittest.TestCase):
    def setUp(self):
        self.runner=app.Runner(SimpleNamespace(repo='brokenasf/achievement-journal'), 'test-token-not-a-real-credential')

    def test_explicit_file_list_and_containment(self):
        for value in [None, [], 'dist/app.js', [None], ['../outside'], ['.'], ['token.txt']]:
            with self.assertRaises(app.AutomationError):
                self.runner.validate_paths(value)
        self.assertEqual(self.runner.validate_paths(['dist/app.js']), [str(Path('dist/app.js'))])

    def test_independent_checks_cannot_hide_failure(self):
        a={'id':1,'name':'test','status':'completed','conclusion':'success','app':{'id':1}}
        b={**a,'id':2,'conclusion':'failure','app':{'id':2}}
        with self.assertRaises(app.AutomationError):
            app.checks_ready([a,b],[],['test'])

    def test_status_failure_blocks_merge(self):
        with self.assertRaises(app.AutomationError):
            app.checks_ready([], [{'context':'external','state':'failure'}], ['external'])

    def test_api_rejects_other_origins_before_network(self):
        for value in ['https://example.com', '//example.com']:
            with self.assertRaises(app.AutomationError):
                app.GitHub('not-real').call(value)
