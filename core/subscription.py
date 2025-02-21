import json
import os
import time
import importlib
import ruamel.yaml
import yaml
from typing import Dict, List, Optional
from urllib.parse import urlparse

from core import tool
from core.models import SubscriptionConfig


class SubscriptionManager:
    """Manages subscription processing and node configurations."""

    def __init__(self, config_path: str):
        """Initialize the subscription manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.parsers = {}  # 存储解析器模块
        self._init_parsers()

    def _load_config(self, path: str) -> Dict:
        """Load configuration from file."""
        return json.loads(tool.readFile(path))

    def _init_parsers(self):
        """Initialize parsers from parsers directory."""
        # 获取当前文件(subscription.py)所在的core目录
        core_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取项目根目录
        root_dir = os.path.dirname(core_dir)
        # 构建 parsers 目录的绝对路径
        parsers_path = os.path.join(root_dir, 'parsers')
        print(parsers_path)
        for file in os.listdir(parsers_path):
            if file.endswith('.py') and not file.startswith('__'):
                module_name = os.path.splitext(file)[0]
                self.parsers[module_name] = importlib.import_module(f'parsers.{module_name}')

    def process_subscribes(self, subscribes: List[SubscriptionConfig]) -> Dict[str, List[Dict]]:
        """Process subscriptions and return node configurations.

        Args:
            subscribes: List of subscription configurations

        Returns:
            Dict mapping subscription tags to node lists
        """
        nodes = {}
        for subscribe in subscribes:
            # 使用 subscribe 的属性而不是字典访问
            if hasattr(subscribe, 'enabled') and not subscribe.enabled:
                continue

            print('处理: \033[31m' + subscribe.url + '\033[0m')
            _nodes = self._get_nodes(subscribe)
            if not _nodes:
                print('没有在此订阅下找到节点，跳过')
                continue

            # 过滤无效节点
            _nodes = list(filter(self._is_valid_node, _nodes))

            if _nodes:
                # 处理节点配置
                if subscribe.prefix:
                    self._add_prefix(_nodes, subscribe.prefix)
                if subscribe.emoji:
                    self._add_emoji(_nodes)

                # 根据subgroup处理标签
                tag = subscribe.tag
                if subscribe.subgroup:
                    tag = f"{tag}-{subscribe.subgroup}-subgroup"

                if not nodes.get(tag):
                    nodes[tag] = []
                nodes[tag].extend(_nodes)

        tool.proDuplicateNodeName(nodes)
        return nodes

    def _get_nodes(self, subscribe: SubscriptionConfig) -> Optional[List[Dict]]:
        """Get and parse nodes from subscription URL."""
        url = subscribe.url
        if url.startswith('sub://'):
            url = tool.b64Decode(url[6:]).decode('utf-8')

        urlstr = urlparse(url)
        if not urlstr.scheme:
            try:
                content = tool.b64Decode(url).decode('utf-8')
                return self._parse_content(content)
            except:
                return self._get_content_from_file(url)
        else:
            return self._get_content_from_url(url, subscribe.user_agent if subscribe.user_agent else '', insecure = subscribe.insecure)

    def _get_content_from_url(self, url: str, custom_ua: str = '', retry_count: int = 10, insecure: bool = False) -> Optional[List[Dict]]:
        """Get content from URL with retry mechanism."""

        headers = {}
        if custom_ua:
            headers['User-Agent'] = custom_ua

        response = tool.getResponse(url, custom_user_agent=custom_ua)
        count = 1
        while count <= retry_count and not response:
            print(f'连接出错，正在进行第 {count} 次重试，最多重试 {retry_count} 次...')
            response = tool.getResponse(url, custom_user_agent=custom_ua)
            count += 1
            time.sleep(1)

        if not response:
            print('获取错误，跳过此订阅')
            return None

        try:
            content = response.content
            text = content.decode('utf-8-sig')

            if text.isspace():
                print('没有从订阅链接获取到任何内容')
                return None

            # 处理不同格式的响应
            if text.startswith('proxies'):
                yaml = ruamel.yaml.YAML()
                data = dict(yaml.load(text.replace('\t', ' ')))
                share_links = []
                for proxy in data['proxies']:
                    share_links.append(tool.clash2v2ray(proxy))
                return self._parse_content('\n'.join(share_links), insecure)
            elif 'outbounds' in text:
                data = json.loads(text)
                excluded_types = {"selector", "urltest", "direct", "block", "dns"}
                return [outbound for outbound in data['outbounds']
                        if outbound.get("type") not in excluded_types]
            else:
                try:
                    decoded = tool.b64Decode(text).decode('utf-8')
                    return self._parse_content(decoded, insecure)
                except:
                    return self._parse_content(text, insecure)
        except Exception as e:
            print(f'Error processing URL content: {str(e)}')
            return None

    def _get_content_from_file(self, path: str) -> Optional[List[Dict]]:
        """Get content from local file."""
        print('处理: \033[31m' + path + '\033[0m')

        file_extension = os.path.splitext(path)[1].lower()
        if file_extension == '.yaml':
            with open(path, 'rb') as file:
                content = file.read()
            yaml_data = dict(yaml.safe_load(content))
            share_links = []
            for proxy in yaml_data['proxies']:
                share_links.append(tool.clash2v2ray(proxy))
            return self._parse_content('\n'.join(share_links))
        else:
            data = tool.readFile(path)
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return self._parse_content(data)

    def _parse_content(self, content: str, insecure: bool) -> List[Dict]:
        """Parse node configurations from content."""
        nodelist = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            protocol = tool.get_protocol(line)
            # 检查是否在排除协议列表中
            if self.config.get('exclude_protocol'):
                excluded = self.config['exclude_protocol'].split(',')
                excluded = [p.strip() for p in excluded]
                if 'hy2' in excluded:
                    excluded[excluded.index('hy2')] = 'hysteria2'
                if protocol in excluded:
                    continue

            if not protocol or protocol not in self.parsers:
                continue

            try:
                # 假设原字符串存储在 tag_value 中

                node = self.parsers[protocol].parse(line)
                tag_value = node['tag']
                tag_value = tag_value[tag_value.find(next(c for c in tag_value if c.isalnum())):]
                node['tag'] = tag_value
                if node:
                    # 如果节点包含 tls 配置，应用订阅的 insecure 设置
                    if 'tls' in node and isinstance(node['tls'], dict):
                        node['tls']['insecure'] = insecure
                    nodelist.append(node)
            except Exception as e:
                print(f'Node parse error: {str(e)}')

        return nodelist

    def _is_valid_node(self, node: Dict) -> bool:
        """Check if node is valid."""
        tag = node.get('tag', '')
        return not any(x in tag for x in ['流量', '剩余', '套餐'])

    def _add_prefix(self, nodes: List[Dict], prefix: str):
        """Add prefix to node tags."""
        for node in nodes:
            node['tag'] = prefix + node['tag']
            if node.get('detour'):
                node['detour'] = prefix + node['detour']

    def _add_emoji(self, nodes: List[Dict]):
        """Add emoji to node tags."""
        for node in nodes:
            node['tag'] = tool.rename(node['tag'])
            if node.get('detour'):
                node['detour'] = tool.rename(node['detour'])

    def _filter_nodes(self, nodes: List[Dict], ex_node_name: str):
        """Filter nodes by exclude name patterns."""
        patterns = ex_node_name.split(',')
        nodes[:] = [n for n in nodes if not any(p in n['tag'] for p in patterns)]