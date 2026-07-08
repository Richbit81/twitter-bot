from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Collection:
    id: str
    name: str
    url: str
    image: str
    description: str
    talking_points: list[str]


@dataclass
class Config:
    account_handle: str
    account_voice: str
    max_chars: int
    include_link: bool
    link_placement: str
    openai_model: str
    openai_temperature: float
    max_retries: int
    similarity_threshold: float
    history_limit: int
    angles: list[str]


@dataclass
class Credentials:
    openai_api_key: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_token_secret: str


def load_config(root: Path = ROOT_DIR) -> Config:
    with open(root / "config.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(
        account_handle=data["account"]["handle"],
        account_voice=data["account"]["voice"],
        max_chars=data["posting"]["max_chars"],
        include_link=data["posting"]["include_link"],
        link_placement=data["posting"]["link_placement"],
        openai_model=data["openai"]["model"],
        openai_temperature=data["openai"]["temperature"],
        max_retries=data["dedup"]["max_retries"],
        similarity_threshold=data["dedup"]["similarity_threshold"],
        history_limit=data["dedup"]["history_limit"],
        angles=data.get("angles", []),
    )


def load_collections(root: Path = ROOT_DIR) -> list[Collection]:
    with open(root / "collections.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return [
        Collection(
            id=item["id"],
            name=item["name"],
            url=item["url"],
            image=item["image"],
            description=item["description"],
            talking_points=item["talking_points"],
        )
        for item in data["collections"]
    ]


def load_system_prompt(root: Path = ROOT_DIR) -> str:
    return (root / "prompts" / "system.txt").read_text(encoding="utf-8").strip()


def load_history(root: Path = ROOT_DIR) -> dict[str, Any]:
    path = root / "data" / "history.json"
    if not path.exists():
        return {"entries": [], "last_collection_index": -1}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_history(history: dict[str, Any], root: Path = ROOT_DIR) -> None:
    path = root / "data" / "history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_credentials(root: Path = ROOT_DIR) -> Credentials:
    load_dotenv(root / ".env")

    def require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Missing environment variable: {name}")
        return value

    return Credentials(
        openai_api_key=require("OPENAI_API_KEY"),
        x_api_key=require("X_API_KEY"),
        x_api_secret=require("X_API_SECRET"),
        x_access_token=require("X_ACCESS_TOKEN"),
        x_access_token_secret=require("X_ACCESS_TOKEN_SECRET"),
    )


def pick_collection(
    collections: list[Collection], history: dict[str, Any]
) -> tuple[Collection, int]:
    last_index = history.get("last_collection_index", -1)
    next_index = (last_index + 1) % len(collections)
    return collections[next_index], next_index
