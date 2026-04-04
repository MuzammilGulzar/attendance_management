# This file makes 'config' a Python package.
# We use strings mapped to class paths — configs are imported LAZILY
# inside create_app() only when actually needed.
# This prevents ProductionConfig from being evaluated during development.

from config.development import DevelopmentConfig
from config.production  import ProductionConfig

config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
