import os

from core.config_manager import ConfigManager
from core.models import SubscriptionConfig
from core.subscription import SubscriptionManager


def main():
    """Main entry point."""
    try:
        # Initialize managers
        sub_manager = SubscriptionManager('providers.json')
        config_manager = ConfigManager(sub_manager.config.get('config_template'))

        # Load and validate subscriptions
        subscriptions = [SubscriptionConfig(**sub) for sub in sub_manager.config['subscribes']]

        # Process subscriptions
        nodes = sub_manager.process_subscribes(subscriptions)

        # Generate final config
        final_config = config_manager.merge_nodes(nodes)

        # Save both normal and iOS configurations
        config_manager.save_config(final_config, 'config.json', generate_ios=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())