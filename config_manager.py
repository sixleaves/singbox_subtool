import json
import os
from datetime import datetime
from typing import Dict, List

from exceptions import ConfigError
from models import NodeConfig


class ConfigManager:
    """Manages configuration templates and final config generation."""

    def __init__(self, template_path: str):
        self.template = self._load_template(template_path)

    def _load_template(self, path: str) -> Dict:
        """Load configuration template."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load template: {str(e)}")

    def _load_template(self, path: str) -> Dict:
        """Load configuration template."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load template: {str(e)}")

    def merge_nodes(self, nodes: Dict[str, List[Dict]]) -> Dict:
        """Merge node configurations with template.

        Args:
            nodes: Dictionary mapping group tags to lists of node dictionaries
        """
        config = self.template.copy()

        # 直接使用节点字典，不再转换为 NodeConfig
        outbounds = []
        for tag, node_list in nodes.items():
            # 节点已经是字典格式，直接添加
            outbounds.extend(node_list)

        if config.get('outbounds'):
            config['outbounds'].extend(outbounds)
        else:
            config['outbounds'] = outbounds

        return config

    def save_config(self, config: Dict, path: str):
        """Save final configuration to file."""
        try:
            # Create backup if file exists
            if os.path.exists(path):
                backup_path = f"{path}_copy.json"
                os.rename(path, backup_path)

            with open(path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise ConfigError(f"Failed to save config: {str(e)}")