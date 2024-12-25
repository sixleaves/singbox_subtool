import json
import os
from datetime import datetime
from typing import Dict, List

from core.exceptions import ConfigError
from core.models import NodeConfig


class ConfigManager:
    def generate_ios_config(self, config: Dict) -> Dict:
        """Generate iOS version configuration file.

        Args:
            config: Original configuration dictionary

        Returns:
            Modified configuration for iOS
        """
        ios_config = config.copy()

        # 修改 inbounds 配置
        ios_config['inbounds'] = [{
            "type": "tun",
            "tag": "tun-in",
            "address": ["172.19.0.1/30"],
            "mtu": 1500,
            "auto_route": True,
            "stack": "system",
            "route_exclude_address_set" : ["geosite-private", "geosite-ctm_cn", "geoip-cn"]
        }]

        # 修改 experimental 配置
        ios_config['experimental'] = {
                "clash_api": {
                      "external_controller": "127.0.0.1:9095", "external_ui": "/etc/sing-box/ui", "secret": "", "external_ui_download_detour": "全球直连", "default_mode": "rule",
                      "external_ui_download_url": "https://gh-proxy.com/https://github.com/MetaCubeX/Yacd-meta/archive/gh-pages.zip"
                },
                "cache_file": {
                        "enabled": True,
                         "store_fakeip": True
                }
        }

        ios_config["dns"]["fakeip"] = {
            "enabled": True,
            "inet4_range": "198.18.0.0/15",
            "inet6_range": "fc00::/18"
        }

        return ios_config

    def save_config(self, config: Dict, path: str, generate_ios: bool = False):
        """Save configuration to file, optionally generating iOS version."""
        try:
            # 保存原始配置
            if os.path.exists(path):
                backup_path = f"{path}_copy.json"
                os.rename(path, backup_path)

            with open(path, 'w') as f:
                # 将 Python 的 True/False 转换为 JSON 的 true/false
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)

            # 如果需要生成 iOS 版本
            if generate_ios:
                ios_config = self.generate_ios_config(config)
                ios_path = path.rsplit('.', 1)[0] + '_ios.json'

                with open(ios_path, 'w') as f:
                    json.dump(ios_config, f, indent=2, ensure_ascii=False, default=str)
                print(f"iOS 配置已保存到: {ios_path}")

        except Exception as e:
            raise ConfigError(f"Failed to save config: {str(e)}")

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
                    filtered = result.copy()
                    for tag in result:
                        for keyword in keywords:
                            # 处理包含 | 的关键词
                            if '|' in keyword:
                                patterns = keyword.split('|')
                                if any(pattern in tag for pattern in patterns):
                                    filtered.remove(tag)
                                    break
                            elif keyword in tag:
                                filtered.remove(tag)
                                break
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