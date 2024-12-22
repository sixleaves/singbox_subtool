import json
import os
from datetime import datetime
from typing import Dict, List

from core.exceptions import ConfigError
from core.models import NodeConfig


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

    def _process_outbound_template(self, outbound: Dict, nodes: Dict[str, List[Dict]], processed_groups: set) -> List[
        str]:
        """Process outbound template and return node tags."""
        result = []

        outbounds = outbound.get('outbounds', [])
        if isinstance(outbounds, str):
            outbounds = [outbounds]

        # 处理 {all} 和组名模板
        for item in outbounds:
            if isinstance(item, str) and item.startswith('{') and item.endswith('}'):
                group_name = item[1:-1]
                if group_name == 'all':
                    for group, node_list in nodes.items():
                        result.extend(node['tag'] for node in node_list)
                else:
                    if nodes.get(group_name):
                        result.extend(node['tag'] for node in nodes[group_name])
            else:
                result.append(item)

        # 应用过滤器规则
        if outbound.get('filter'):
            original_count = len(result)
            for filter_rule in outbound['filter']:
                action = filter_rule['action']
                keywords = filter_rule['keywords']

                if action == 'include':
                    # 对于 include，任意一个关键词匹配即可
                    filtered = []
                    for tag in result:
                        for keyword in keywords:
                            # 处理包含 | 的关键词
                            if '|' in keyword:
                                patterns = keyword.split('|')
                                if any(pattern in tag for pattern in patterns):
                                    filtered.append(tag)
                                    break
                            elif keyword in tag:
                                filtered.append(tag)
                                break
                    result = filtered
                elif action == 'exclude':
                    # 对于 exclude，所有关键词都要检查
                    filtered = []
                    for tag in result:
                        should_exclude = False
                        for keyword in keywords:
                            # 处理包含 | 的关键词
                            if '|' in keyword:
                                patterns = keyword.split('|')
                                if any(pattern in tag for pattern in patterns):
                                    should_exclude = True
                                    break
                            elif keyword in tag:
                                should_exclude = True
                                break
                        if not should_exclude:
                            filtered.append(tag)
                    result = filtered

            print(f"过滤器处理: {outbound['tag']} 从 {original_count} 个节点过滤后剩余 {len(result)} 个节点")

        return result

    def merge_nodes(self, nodes: Dict[str, List[Dict]]) -> Dict:
        """Merge node configurations with template."""
        config = self.template.copy()
        all_nodes = []  # 存储所有节点配置

        # 收集所有节点配置
        for group, node_list in nodes.items():
            all_nodes.extend(node_list)

        # 处理现有的 outbounds 配置
        if config.get('outbounds'):
            new_outbounds = []

            # 处理所有出站配置
            for outbound in config['outbounds']:
                if outbound.get('type') in ['selector', 'urltest']:
                    outbound_copy = outbound.copy()
                    processed_tags = self._process_outbound_template(outbound, nodes, set())
                    outbound_copy['outbounds'] = processed_tags
                    if 'filter' in outbound_copy:
                        del outbound_copy['filter']
                    new_outbounds.append(outbound_copy)
                else:
                    new_outbounds.append(outbound)

            # 添加所有实际节点配置
            new_outbounds.extend(all_nodes)
            config['outbounds'] = new_outbounds

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