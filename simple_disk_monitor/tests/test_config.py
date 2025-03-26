import unittest
from src.utils.config import ConfigManager

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager("test_config.json")

    def test_load_config(self):
        config = self.config_manager.load_config()
        self.assertIsInstance(config, dict)

    def test_save_config(self):
        test_data = {"key": "value"}
        self.config_manager.save_config(test_data)
        loaded_data = self.config_manager.load_config()
        self.assertEqual(loaded_data, test_data)

    def test_default_config(self):
        default_config = self.config_manager.default_config
        self.assertIn("critical_threshold", default_config)
        self.assertIn("warning_threshold", default_config)
        self.assertIn("check_interval", default_config)

if __name__ == "__main__":
    unittest.main()