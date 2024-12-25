from os import environ
from typing import Callable

from flask import current_app as app
from flask import g, request
from requests import post

from src.constants.external_services import KREATIVE_ID_API_URL
from src.constants.roles import (
    DOCUVET_BASE,
    DOCUVET_NONPROVIDER,
    DOCUVET_ORG_ADMIN,
    DOCUVET_PROVIDER,
    DOCUVET_SUBSCRIBER,
    DOCUVET_SUPER_USER,
    KREATIVE_ID_ADMIN,
    KREATIVE_ID_DEVELOPER,
)
from src.constants.status_codes import FORBIDDEN, INTERNAL_SERVER_ERROR, KEYCHAIN_NOT_FOUND, NOT_FOUND, UNAUTHORIZED
from src.services.veterinarians import get_user_by_id

KREATIVE_ID_KEY_HEADER = "Kreative-Id-Key"
KREATIVE_API_KEY_HEADER = "Docuvet-Api-Key"
AIDN = environ["AIDN"]
APP_CHAIN = environ["APP_CHAIN"]
DOCUVET_API_KEY = environ["DOCUVET_API_KEY"]

def has_intersection(s0, s1) -> bool:
    return bool(set(s0) & set(s1))

class User:
    def __init__(self, user_data: dict):
        self.id = user_data.get("id")
        self.ksn = user_data.get("ksn")
        self.title = user_data.get("title")
        self.clinic_id = user_data.get("clinic_id")
        self.is_active = user_data.get("is_active")
        self.is_provider = user_data.get("is_provider")
        self.audio_file_ttl = user_data.get("audio_file_ttl")
        self.species_served = user_data.get("species_served")
        self.created_at = user_data.get("created_at")


def verify_kreative_cookie():
    if request.path == "/":
        return None

    header_api_key = request.headers.get(KREATIVE_API_KEY_HEADER)
    if (header_api_key):
        if (DOCUVET_API_KEY and header_api_key == DOCUVET_API_KEY):
            g.is_super_user = True

            app.logger.info(f"received authorized request {request.method} {request.url} with api key")

            return None
        return FORBIDDEN

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
    g.is_subscriber = DOCUVET_SUBSCRIBER in g.roles
    g.is_org_admin = DOCUVET_ORG_ADMIN in g.roles
    g.is_super_user = has_intersection(g.roles, {KREATIVE_ID_ADMIN, KREATIVE_ID_DEVELOPER})

    try:
      g.user = User(data["claims"]["user"])
    except Exception as e:
      app.logger.info(f"no user data found in claims for {g.ksn} or it failed: {e}")
      user = get_user_by_id(g.ksn)

      if user:
        g.user = {
          "id": user.id,
          "ksn": user.ksn,
          "title": user.title,
          "clinic_id": user.clinic_id,
          "is_active": user.is_active,
          "is_provider": user.is_provider,
          "audio_file_ttl": user.audio_file_ttl,
          "species_served": user.species_served,
          "created_at": user.created_at,
        }
      else:
          # when a new user onboards, their user data is not immediately available
          app.logger.debug(f"failed to find user data for {g.ksn}")

    app.logger.info(f"received authenticated request {request.method} {request.url} by user {g.ksn}")

    # return nothing to continue request
    return None


def authorize(authorize_logic: Callable = lambda: False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            verify_result = verify_kreative_cookie()

            if verify_result:
                return verify_result

            if getattr(g, "is_super_user", False):
                authorize_logic()
                return func(*args, **kwargs)

            if not hasattr(g, "roles"):
                return UNAUTHORIZED

            docuvet_roles = {
                DOCUVET_SUBSCRIBER, DOCUVET_ORG_ADMIN,
                DOCUVET_SUPER_USER, DOCUVET_NONPROVIDER, DOCUVET_PROVIDER, DOCUVET_BASE,
            }

            if has_intersection(docuvet_roles, g.roles) and authorize_logic():
                return func(*args, **kwargs)

            app.logger.info(f"unauthorized request {request.method} {request.url} by user {g.ksn}")

            return FORBIDDEN
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
