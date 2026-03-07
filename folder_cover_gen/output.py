from . import config

def print_debug(message):
    if config.is_debug:
        print(message)

def print_error(message):
    print(f"ERROR: {message}")

def print_warning(message):
    print(f"WARNING: {message}")

def print_verbose(message):
    if config.is_verbose or config.is_debug:
        print(message)
