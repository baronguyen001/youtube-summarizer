from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import UnionType
from typing import Any, Self, cast, get_args, get_origin

import yaml

PROVIDER_ENV = {
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}
PATH_FIELDS = {"db_path", "markdown_dir", "html_dir", "cookiefile"}


@dataclass(slots=True)
class SummarizeConfig:
    temperature: float = 0.3
    max_output_tokens: int = 1536
    gemini_thinking_budget: int = 0
    delay_between_videos_s: float = 0.0
    max_retries: int = 5


@dataclass(slots=True)
class RetryConfig:
    max_attempts: int = 4


@dataclass(slots=True)
class PromptConfig:
    preset: str = "auto"
    custom_template: str | None = None


@dataclass(slots=True)
class DeliveryConfig:
    targets: list[str] = field(default_factory=lambda: ["stdout"])
    markdown_dir: Path = Path("out")
    html_dir: Path = Path("out")


@dataclass(slots=True)
class YtDlpConfig:
    cookiefile: Path | None = None


@dataclass(slots=True)
class Config:
    provider: str = "gemini"
    model: str | None = None
    output_language: str = "en"
    caption_langs: list[str] = field(default_factory=lambda: ["en"])
    transcript_char_cap: int = 60000
    db_path: Path = Path("ytsum.db")
    openai_base_url: str | None = None
    summarize: SummarizeConfig = field(default_factory=SummarizeConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    yt_dlp: YtDlpConfig = field(default_factory=YtDlpConfig)

    @property
    def api_key_env(self) -> str:
        return PROVIDER_ENV.get(self.provider, "")

    @property
    def api_key(self) -> str:
        env_name = self.api_key_env
        return os.environ.get(env_name, "") if env_name else ""

    def with_overrides(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        lang: str | None = None,
        deliver: str | None = None,
    ) -> Self:
        cfg = self
        if provider:
            cfg = replace(cfg, provider=provider)
        if model:
            cfg = replace(cfg, model=model)
        if lang:
            cfg = replace(cfg, output_language=lang, caption_langs=[lang])
        if deliver:
            targets = [item.strip() for item in deliver.split(",") if item.strip()]
            cfg = replace(cfg, delivery=replace(cfg.delivery, targets=targets or ["stdout"]))
        return cfg


def load_config(path: str | Path | None = None) -> Config:
    cfg = Config()
    if not path:
        return cfg
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a mapping at the top level.")
    return cast(Config, _merge_dataclass(cfg, raw))


def _merge_dataclass(instance: Any, values: dict[str, Any]) -> Any:
    updates: dict[str, Any] = {}
    field_map = getattr(instance, "__dataclass_fields__", {})
    for name, value in values.items():
        if name not in field_map:
            continue
        current = getattr(instance, name)
        field_type = field_map[name].type
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            updates[name] = _merge_dataclass(current, value)
        elif name in PATH_FIELDS or isinstance(current, Path) or _is_path_type(field_type):
            updates[name] = Path(value) if value is not None else None
        else:
            updates[name] = value
    return replace(instance, **updates)


def _is_path_type(field_type: Any) -> bool:
    origin = get_origin(field_type)
    if origin in {UnionType, None}:
        return field_type is Path or Path in get_args(field_type)
    return Path in get_args(field_type)
