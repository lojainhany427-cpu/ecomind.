"""Configuration from environment variables (and an optional local .env file).
Secrets are never hard-coded and never returned by the API."""
import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    username: str | None
    password: str | None
    ssl: bool
    autoseed: bool
    graph: str
    llm_key: str | None
    llm_model: str


def load_config() -> Config:
    _load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    try:
        port = int(os.getenv("FALKORDB_PORT", "6379"))
    except ValueError:
        raise ValueError("FALKORDB_PORT must be an integer")
    return Config(
        host=os.getenv("FALKORDB_HOST", "localhost"),
        port=port,
        username=os.getenv("FALKORDB_USERNAME") or None,
        password=os.getenv("FALKORDB_PASSWORD") or None,
        ssl=_flag("FALKORDB_SSL"),
        autoseed=_flag("ECOMIND_AUTOSEED"),
        graph=os.getenv("FALKORDB_GRAPH", "ecomind"),
        llm_key=os.getenv("ANTHROPIC_API_KEY") or None,
        llm_model=os.getenv("ECOMIND_LLM_MODEL", "claude-sonnet-4-6"),
    )
