class SubscriptionError(Exception):
    """Base exception for subscription processing errors."""
    pass

class ParserError(Exception):
    """Raised when node parsing fails."""
    pass

class ConfigError(Exception):
    """Raised when configuration processing fails."""
    pass