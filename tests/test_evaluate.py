"""Behavioral tests: evaluation must detect drift without exposing command output."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/evaluate.py'


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.exists():
            return
        spec = importlib.util.spec_from_file_location('evaluate', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_effective_config_uses_last_setting_in_correct_section(self):
        self.assertTrue(hasattr(self.module, 'config_values'), 'effective power policy parser missing')
        if hasattr(self.module, 'config_values'):
            text = '[Sleep]\nAllowSuspend=no\n[Other]\nAllowSuspend=no\n[Sleep]\nAllowSuspend=yes\n'
            self.assertEqual(self.module.config_values(text, 'Sleep')['AllowSuspend'], 'yes')

    def test_tailscale_version_redacts_extra_output(self):
        self.assertTrue(hasattr(self.module, 'tailscale_checks'), 'Tailscale validation missing')
        if hasattr(self.module, 'tailscale_checks'):
            outputs = ['1.102.4\nPRIVATE DETAILS', 'tailscale 1.102.4-1\n', 'Repository : extra\nVersion : 1.102.4-1\n']
            with patch.object(self.module, 'run', side_effect=[subprocess.CompletedProcess([], 0, s, '') for s in outputs]):
                checks = self.module.tailscale_checks()
            self.assertEqual(checks[0]['version'], '1.102.4')
            self.assertNotIn('PRIVATE', str(checks))
            self.assertEqual(checks[1]['status'], 'pass')

    def test_tailscale_outdated_package_is_failure(self):
        if not hasattr(self.module, 'tailscale_checks'):
            self.skipTest('implementation missing')
        outputs = ['1.100.0\n', 'tailscale 1.100.0-1\n', 'Repository : extra\nVersion : 1.102.4-1\n']
        with patch.object(self.module, 'run', side_effect=[subprocess.CompletedProcess([], 0, s, '') for s in outputs]):
            self.assertEqual(self.module.tailscale_checks()[1]['status'], 'fail')

    def test_tailscale_daemon_mismatch_is_failure(self):
        completed = subprocess.CompletedProcess([], 0, 'Client: 1.102.4\nDaemon: 1.100.0\n', '')
        with patch.object(self.module, 'run', return_value=completed):
            self.assertEqual(self.module.tailscale_daemon_check()['status'], 'fail')

    def test_tailscale_daemon_match_passes(self):
        completed = subprocess.CompletedProcess([], 0, 'Client: 1.102.4\nDaemon: 1.102.4\n', '')
        with patch.object(self.module, 'run', return_value=completed):
            self.assertEqual(self.module.tailscale_daemon_check()['status'], 'pass')

    def test_evaluator_exists(self):
        self.assertTrue(SCRIPT.exists(), 'read-only profile evaluator is missing')

    def test_failed_probe_redacts_stdout_and_stderr(self):
        if not SCRIPT.exists():
            self.skipTest('implementation missing')
        result = subprocess.CompletedProcess([], 1, 'SECRET_OUTPUT', 'SECRET_ERROR')
        with patch.object(self.module.subprocess, 'run', return_value=result):
            check = self.module.probe('docker', ['docker', 'info'])
        self.assertEqual(check, {'name': 'docker', 'status': 'fail'})

    def test_missing_binary_is_failure(self):
        if not SCRIPT.exists():
            self.skipTest('implementation missing')
        check = self.module.probe('missing', ['/nonexistent-workbench-test'])
        self.assertEqual(check['status'], 'fail')

    def test_timeout_is_failure(self):
        if not SCRIPT.exists():
            self.skipTest('implementation missing')
        with patch.object(self.module.subprocess, 'run', side_effect=subprocess.TimeoutExpired('x', 20)):
            self.assertEqual(self.module.probe('slow', ['x'])['status'], 'fail')

    def test_server_rejects_installed_desktop(self):
        if not SCRIPT.exists():
            self.skipTest('implementation missing')
        packages = 'ubuntu-desktop\tinstalled\nxserver-xorg\tinstalled\n'
        with patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, packages, '')):
            self.assertEqual(self.module.server_gui_check()['status'], 'fail')

    def test_server_accepts_removed_desktop_config_files(self):
        if not SCRIPT.exists():
            self.skipTest('implementation missing')
        packages = 'ubuntu-desktop\tconfig-files\nvim-tiny\tinstalled\n'
        with patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, packages, '')):
            self.assertEqual(self.module.server_gui_check()['status'], 'pass')


if __name__ == '__main__':
    unittest.main()
