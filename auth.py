import jwt as pyjwt
import time
import requests
from pathlib import Path

from constants import APP_ID, PRIVATE_KEY_PATH


def get_token(installation_id):
    private_key = Path(PRIVATE_KEY_PATH).read_text(encoding="utf8")

    # Generate the JWT
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }
    jwt_token = pyjwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    access_token_url = (
        f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    )
    response = requests.post(access_token_url, headers=headers, timeout=120)
    return response.json()["token"]
