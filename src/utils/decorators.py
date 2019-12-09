from functools import wraps


def disable_for_loaddata(signal_handler):
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs['raw']:
            print("Skipping signal for %s %s" % (args, kwargs))
            return
        signal_handler(*args, **kwargs)

    return wrapper
