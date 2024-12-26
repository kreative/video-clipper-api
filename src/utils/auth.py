from os import environ
from typing import Callable

from flask import current_app as app
from flask import g, request
from requests import post

from src.constants.external_services import KREATIVE_ID_API_URL
from src.constants.roles import (
    VIDCLIP_BASE,
)
from src.constants.status_codes import FORBIDDEN, INTERNAL_SERVER_ERROR, KEYCHAIN_NOT_FOUND, NOT_FOUND, UNAUTHORIZED

KREATIVE_ID_KEY_HEADER = "Kreative-Id-Key"
AIDN = environ["AIDN"]
APP_CHAIN = environ["APP_CHAIN"]

def has_intersection(s0, s1) -> bool:
    return bool(set(s0) & set(s1))

def verify_kreative_cookie():
    if request.path == "/":
        return None

    # get KREATIVE_COOKIE from request headers
    kreative_id_key = request.headers.get(KREATIVE_ID_KEY_HEADER)
    if not kreative_id_key:
        app.logger.warning(f"received request without auth: {request.method} {request.url}")
        return UNAUTHORIZED

    verification = post(f"{KREATIVE_ID_API_URL}/keychains/verify", json={
        "key": kreative_id_key,
        "aidn": int(AIDN),
        "appchain": APP_CHAIN,
    })

    # check for errors
    match verification.status_code:
        case 401:
            app.logger.warning(f"received unauthorized request: {request.method} {request.url}")
            return UNAUTHORIZED
        case 403:
            app.logger.warning(f"received forbidden request: {request.method} {request.url}")
            return FORBIDDEN
        case 500 | 400:
            app.logger.error(f"failed to verify request: {request.method} {request.url}")
            return INTERNAL_SERVER_ERROR
        case 404:
            app.logger.warning(f"request with invalid session: {request.method} {request.url}")

            if verification.json()["message"] == "keychain not found":
                return KEYCHAIN_NOT_FOUND

            return NOT_FOUND

    # if no errors, set user data to g (request context)
    data = verification.json()["data"]

    g.ksn = data["account"]["ksn"]
    g.first_name = data["account"]["firstName"]
    g.last_name = data["account"]["lastName"]
    g.roles = {role["rid"] for role in data["account"]["roles"]}
    g.email = data["account"]["email"]
    g.phone_number = data["account"]["phoneNumber"]
    g.key_chain = data["keychain"]
    g.has_base = VIDCLIP_BASE in g.roles

    app.logger.info(f"received authenticated request {request.method} {request.url} by user {g.ksn}")

    # return nothing to continue request
    return None


def authorize(authorize_logic: Callable = lambda: False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            verify_result = verify_kreative_cookie()

            if verify_result:
                return verify_result

            if not hasattr(g, "roles"):
                return UNAUTHORIZED

            vidclip_roles = { VIDCLIP_BASE }

            if has_intersection(vidclip_roles, g.roles) and authorize_logic():
                return func(*args, **kwargs)

            app.logger.info(f"unauthorized request {request.method} {request.url} by user {g.ksn}")

            return FORBIDDEN
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
