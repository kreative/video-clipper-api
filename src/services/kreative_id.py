import os
import random
import string

import requests
from flask import current_app as app

from src.constants.external_services import KREATIVE_ID_API_URL


def generate_random_string(size: int) -> str:
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits
    # Generate a random string of specified size
    return "".join(random.choice(characters) for _ in range(size))


def generate_random_numbers(size: int) -> str:
    # Define the characters to choose from
    characters = string.digits
    # Generate a random string of specified size
    return "".join(random.choice(characters) for _ in range(size))


def get_info_for_accounts(ksn_list: list[int]) -> list | None:
    accounts = None
    try:
        url = f"{KREATIVE_ID_API_URL}/accounts/list"
        headers = {
            "KREATIVE_ID_APPCHAIN": os.environ.get("KREATIVE_ID_APPCHAIN"),
        }
        response = requests.post(url, json={"ksnList": ksn_list}, headers=headers).json()
        accounts = response["data"]
    except Exception as e:
        # handle the exception here
        app.logger.error(f"Error getting user info for {ksn_list}:", e)

    return accounts


def generate_keychain(ksn: int) -> list | None:
    key = None

    try:
        url = f"{KREATIVE_ID_API_URL}/keychains"
        headers = {
            "KREATIVE_ID_APPCHAIN": os.environ.get("KREATIVE_ID_APPCHAIN"),
        }
        json = {
            "ksn": ksn,
            "rememberMe": True,
            "aidn": int(os.environ.get("AIDN")),
            "environment": os.environ.get("FLASK_ENV"),
        }

        response = requests.post(url, json=json, headers=headers).json()

        key = response["key"]
    except Exception as e:
        # handle the exception here
        app.logger.error(f"Error generating keychian for user {ksn}:", e)

    return key
