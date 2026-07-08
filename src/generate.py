from __future__ import annotations

import random
from datetime import datetime, timezone

from openai import OpenAI

from src.config_loader import Collection, Config, Credentials
from src.dedup import is_duplicate, validate_tweet


ANGLE_HINTS = {
    "behind_the_scenes": "Share a behind-the-scenes insight about building this on-chain.",
    "collector_pov": "Write from a collector's perspective discovering this piece.",
    "tech_fact": "Highlight a specific technical or on-chain detail.",
    "community": "Mention community, collaboration, or shared culture around Ordinals.",
    "mint_reminder": "Gently remind people this exists on richart.app — no hard sell.",
    "creative_process": "Describe the creative or generative process briefly.",
    "on_chain_permanence": "Reflect on permanence, inscription, or Bitcoin as a canvas.",
}


def build_user_prompt(
    collection: Collection,
    angle: str,
    recent_tweets: list[str],
    config: Config,
) -> str:
    angle_hint = ANGLE_HINTS.get(angle, "Write a fresh, unique angle on this collection.")
    talking_points = "\n".join(f"- {point}" for point in collection.talking_points)
    recent_block = ""
    if recent_tweets:
        recent_lines = "\n".join(f"- {t}" for t in recent_tweets[-20:])
        recent_block = f"\n\nRecent tweets to avoid repeating (do not copy phrasing):\n{recent_lines}"

    return f"""Collection: {collection.name}
URL (must appear at end): {collection.url}
Description: {collection.description}
Talking points:
{talking_points}

Angle for this tweet: {angle} — {angle_hint}
Account voice: {config.account_voice}
Max characters: {config.max_chars} (including URL)
{recent_block}

Write one tweet now."""


def generate_tweet(
    client: OpenAI,
    system_prompt: str,
    collection: Collection,
    angle: str,
    recent_tweets: list[str],
    config: Config,
) -> str:
    response = client.chat.completions.create(
        model=config.openai_model,
        temperature=config.openai_temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": build_user_prompt(collection, angle, recent_tweets, config),
            },
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned empty tweet content")
    return content.strip().strip('"')


def generate_unique_tweet(
    credentials: Credentials,
    system_prompt: str,
    collection: Collection,
    history_entries: list[dict],
    config: Config,
    angles: list[str],
) -> tuple[str, str]:
    client = OpenAI(api_key=credentials.openai_api_key)
    recent_tweets = [e.get("text", "") for e in history_entries]
    shuffled_angles = angles[:]
    random.shuffle(shuffled_angles)

    last_error = "Unknown error"
    for attempt, angle in enumerate(shuffled_angles[: config.max_retries], start=1):
        tweet = generate_tweet(
            client, system_prompt, collection, angle, recent_tweets, config
        )

        if config.include_link and collection.url not in tweet:
            if config.link_placement == "end":
                tweet = f"{tweet.rstrip()} {collection.url}".strip()
            else:
                tweet = f"{collection.url} {tweet.lstrip()}".strip()

        valid, reason = validate_tweet(tweet, config.max_chars, collection.url)
        if not valid:
            last_error = reason
            continue

        if is_duplicate(
            tweet,
            history_entries,
            config.similarity_threshold,
            config.history_limit,
        ):
            last_error = "Too similar to a previous tweet"
            continue

        return tweet, angle

    raise RuntimeError(
        f"Failed to generate unique tweet after {config.max_retries} attempts: {last_error}"
    )


def record_tweet(
    history: dict,
    tweet: str,
    collection_id: str,
    collection_index: int,
    angle: str,
    dry_run: bool,
    tweet_id: str | None = None,
) -> None:
    entry = {
        "text": tweet,
        "collection_id": collection_id,
        "angle": angle,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
    }
    if tweet_id:
        entry["tweet_id"] = tweet_id

    history.setdefault("entries", []).append(entry)
    history["last_collection_index"] = collection_index
