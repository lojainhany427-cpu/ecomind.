"""Flask API + static UI. Run: python -m ecomind.server"""
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from .config import load_config
from .db import GraphStore, DatabaseUnavailable
from .engine import Engine, InvalidRequest
from .llm import AnthropicNarrator
from .queries import QueryError

STATIC = Path(__file__).parent / "static"


def create_app(store=None, llm=None):
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    state = {"store": store, "llm": llm}

    def get_engine():
        if state["store"] is None:
            cfg = load_config()
            state["store"] = GraphStore(cfg)
            if cfg.autoseed:
                state["store"].ensure_seeded()
            if cfg.llm_key and state["llm"] is None:
                state["llm"] = AnthropicNarrator(cfg.llm_key, cfg.llm_model)
        return Engine(state["store"], state["llm"])

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/api/health")
    def health():
        try:
            get_engine()
            return jsonify(status="ok", database="connected")
        except DatabaseUnavailable as e:
            return jsonify(status="degraded", database="unavailable", detail=str(e)), 503

    @app.post("/api/investigate")
    def investigate():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Request body must be a JSON object"), 400
        try:
            return jsonify(get_engine().investigate(data.get("question"), data.get("weights")))
        except (InvalidRequest, QueryError) as e:
            return jsonify(error=str(e)), 400
        except DatabaseUnavailable as e:
            return jsonify(error=str(e)), 503

    return app


app = create_app()  # used by gunicorn: gunicorn ecomind.server:app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
