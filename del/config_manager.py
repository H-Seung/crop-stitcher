import yaml
from typing import Dict, Any


class YamlConfigProvider(ConfigProvider):
    """Single Responsibility: YAML 파일로부터 설정 로드"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None

    def get_config(self) -> Dict[str, Any]:
        if self._config is None:
            self._load_config()
        return self._config

    def _load_config(self) -> None:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
