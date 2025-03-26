import unittest
from src.monitor.disk_monitor import SimpleDiskMonitor

class TestSimpleDiskMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = SimpleDiskMonitor()

    def test_initialization(self):
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.config.get("critical_threshold"), 90)
        self.assertEqual(self.monitor.config.get("warning_threshold"), 75)

    def test_get_available_drives(self):
        drives = self.monitor.get_available_drives()
        self.assertIsInstance(drives, list)

    def test_check_disk_usage(self):
        usage = self.monitor.check_disk_usage()
        self.assertIn("critical", usage)
        self.assertIn("warning", usage)
        self.assertIn("notice", usage)

    def test_load_config(self):
        config = self.monitor.load_config()
        self.assertIsInstance(config, dict)

    def test_set_autostart(self):
        self.monitor.set_autostart(True)
        self.assertTrue(self.monitor.config["run_at_startup"])

if __name__ == '__main__':
    unittest.main()