import yaml
from .interfaces import ConfigProvider


class YamlConfigProvider(ConfigProvider):
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None

    def get_config(self):
        if self._config is None: ######
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        return self._config