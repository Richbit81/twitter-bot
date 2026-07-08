from __future__ import annotations

from pathlib import Path

import tweepy

from src.config_loader import Credentials
from src.media import resolve_image_path


def post_tweet(credentials: Credentials, text: str, image: str, root: Path) -> str:
    auth = tweepy.OAuth1UserHandler(
        credentials.x_api_key,
        credentials.x_api_secret,
        credentials.x_access_token,
        credentials.x_access_token_secret,
    )
    api = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=credentials.x_api_key,
        consumer_secret=credentials.x_api_secret,
        access_token=credentials.x_access_token,
        access_token_secret=credentials.x_access_token_secret,
    )

    image_path = resolve_image_path(image, root)
    media = api.media_upload(filename=str(image_path))
    if not media or not media.media_id:
        raise RuntimeError("X API did not return a media ID")

    response = client.create_tweet(text=text, media_ids=[media.media_id])
    if not response.data or not response.data.get("id"):
        raise RuntimeError("X API did not return a tweet ID")

    return str(response.data["id"])
