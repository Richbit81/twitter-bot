#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config_loader import (
    load_collections,
    load_config,
    load_credentials,
    load_history,
    load_system_prompt,
    pick_collection,
    save_history,
)
from src.generate import generate_unique_tweet, record_tweet
from src.post import post_tweet

ROOT = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Richart.app auto-tweet bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate a tweet but do not post to X",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root directory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.root / ".env")

    config = load_config(args.root)
    collections = load_collections(args.root)
    system_prompt = load_system_prompt(args.root)
    history = load_history(args.root)

    collection, collection_index = pick_collection(collections, history)
    angles = config.angles or ["creative_process"]

    print(f"Collection: {collection.name} ({collection.id})")
    print(f"Image: {collection.image}")

    if args.dry_run:
        credentials = None
        try:
            credentials = load_credentials(args.root)
        except RuntimeError:
            import os

            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                print("Error: OPENAI_API_KEY required even for dry-run", file=sys.stderr)
                return 1
            from src.config_loader import Credentials

            credentials = Credentials(
                openai_api_key=openai_key,
                x_api_key="",
                x_api_secret="",
                x_access_token="",
                x_access_token_secret="",
            )
    else:
        credentials = load_credentials(args.root)

    tweet, angle = generate_unique_tweet(
        credentials=credentials,
        system_prompt=system_prompt,
        collection=collection,
        history_entries=history.get("entries", []),
        config=config,
        angles=angles,
    )

    print(f"Angle: {angle}")
    print(f"Tweet ({len(tweet)} chars):\n{tweet}\n")

    tweet_id = None
    if args.dry_run:
        print("[DRY RUN] Tweet not posted to X.")
        print(f"[DRY RUN] Would attach image: {collection.image}")
    else:
        tweet_id = post_tweet(credentials, tweet, collection.image, args.root)
        print(f"Posted successfully with image. Tweet ID: {tweet_id}")

    if args.dry_run:
        print("[DRY RUN] History not updated.")
    else:
        record_tweet(
            history=history,
            tweet=tweet,
            collection_id=collection.id,
            collection_index=collection_index,
            angle=angle,
            dry_run=False,
            tweet_id=tweet_id,
        )
        save_history(history, args.root)
        print("History updated.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
