from functools import wraps

from flask import request


def check_missing_body_keys(required_keys: list[str]):
    def wrapper(f: callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            provided_keys: list[str] = request.json.keys()
            missing_keys: list[str] = [
                arg for arg in required_keys if arg not in provided_keys]

            if missing_keys:
                return f'missing parameters: {", ".join(missing_keys)}', 400
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


def check_missing_form_fields(required_fields: list[str]):
    def wrapper(f: callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            provided_fields: list[str] = request.form.keys()
            missing_keys: list[str] = [
                arg for arg in required_fields if arg not in provided_fields]

            if missing_keys:
                return f'missing parameters: {", ".join(missing_keys)}', 400
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
