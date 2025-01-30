import functools
from api.errors import TokenExpired


def retry_on_failure(before_retry_func=None):
    @functools.wraps
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except TokenExpired:
                if before_retry_func:
                    before_retry_func(self)
                return func(self, *args, **kwargs)

        return wrapper
    return decorator
