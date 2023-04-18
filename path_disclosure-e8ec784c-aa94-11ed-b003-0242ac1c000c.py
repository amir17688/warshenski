import os
import sys
import imp
import logging


def _is_package(directory):
    return os.path.exists(os.path.join(directory, '__init__.py'))


def _guess_import_path_and_name(file):
    current = os.path.dirname(file)
    base = os.path.splitext(os.path.basename(file))[0]
    name = [base] if base != '__init__' else []
    parent = None
    while current != parent and _is_package(current):
        parent = os.path.dirname(current)
        name.append(os.path.basename(current))
        current = parent

    return current, '.'.join(reversed(name))


def run_file(runfile, func_to_get='main'):
    # Make sure imports within the module behave as expected
    import_path, name = _guess_import_path_and_name(runfile)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)
    sys.modules['__tng_runfile__'] = module = imp.load_source(name, runfile)

    if hasattr(module, func_to_get):
        return getattr(module, func_to_get)
    else:
        logging.getLogger('tng').warn(
            'No {} function found in {}'.format(func_to_get, runfile))
