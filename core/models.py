from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union


@dataclass
class SubscriptionConfig:
    """Configuration for a single subscription."""
    url: str
    tag: str
    enabled: bool = True
    emoji: Union[bool, int] = False
    subgroup: str = ""
    prefix: str = ""
    user_agent: str = ""

    def __post_init__(self):
        if isinstance(self.emoji, int):
            self.emoji = bool(self.emoji)


@dataclass
class NodeConfig:
    """Configuration for a single node."""
    tag: str
    type: str
    server: str
    port: int
    settings: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the node configuration to a dictionary."""
        return {
            "tag": self.tag,
            "type": self.type,
            "server": self.server,
            "port": self.port,
            **self.settings
        }