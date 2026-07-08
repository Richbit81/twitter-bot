from __future__ import annotations

import tweepy

from src.config_loader import Credentials


def post_tweet(credentials: Credentials, text: str) -> str:
    client = tweepy.Client(
        consumer_key=credentials.x_api_key,
        consumer_secret=credentials.x_api_secret,
        access_token=credentials.x_access_token,
        access_token_secret=credentials.x_access_token_secret,
    )

    response = client.create_tweet(text=text)
    if not response.data or not response.data.get("id"):
        raise RuntimeError("X API did not return a tweet ID")

    return str(response.data["id"])
