import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app.restart import launch_restart, restart_component_state, wait_for_previous


class RestartTests(unittest.TestCase):
    def test_arguments_environment_and_component_states(self):
        with patch('app.restart.subprocess.Popen') as popen:
            launch_restart(True, False)
        args, kwargs = popen.call_args
        command = args[0]
        self.assertIn(f'--restart-after-pid={os.getpid()}', command)
        self.assertEqual(kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')
        self.assertTrue(restart_component_state(command, 'zapret', False))
        self.assertFalse(restart_component_state(command, 'tg', True))
        self.assertTrue(restart_component_state(['--restart-tg=0'], 'tg', True))

    def test_waits_until_old_process_exits(self):
        old = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1.2)'])
        start = time.monotonic()
        try:
            self.assertTrue(wait_for_previous([f'--restart-after-pid={old.pid}']))
            self.assertGreater(time.monotonic() - start, 0.5)
        finally:
            old.wait(timeout=5)
        self.assertFalse(wait_for_previous([f'--restart-after-pid={os.getpid()}']))


if __name__ == '__main__':
    unittest.main()
