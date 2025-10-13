import yaml
import os
from .interfaces import ConfigProvider


class YamlConfigProvider(ConfigProvider):
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_path = os.path.join(project_root, config_path)
        print("config_path : ", self.config_path)

    def get_config(self):
        if self._config is None:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                print("config : ", self._config)
        return self._config