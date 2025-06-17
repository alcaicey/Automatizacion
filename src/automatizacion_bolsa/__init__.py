from importlib import import_module
import sys

_modules = [
    'config_loader',
    'login',
    'playwright_session',
    'page_manager',
    'resources',
    'data_capture',
    'utils',
    'error_handling',
]

for name in _modules:
    mod = import_module(f'src._automatizacion_bolsa.{name}')
    sys.modules[f'{__name__}.{name}'] = mod

__all__ = _modules
