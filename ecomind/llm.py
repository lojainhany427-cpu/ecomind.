"""Optional LLM narration via the Anthropic Messages API (stdlib only).
The LLM only rewrites facts we already retrieved from the graph; it never writes Cypher.
NOTE: written to the public API shape but NOT exercised in the build sandbox (no network/key)."""
import json
import urllib.request


class AnthropicNarrator:
    def __init__(self, key: str, model: str):
        self._key, self._model = key, model

    def narrate(self, template_text: str) -> str:
        body = json.dumps({
            "model": self._model, "max_tokens": 700,
            "system": ("Rewrite the analysis for a school student in clear, friendly prose. Use ONLY the facts "
                       "given. Do not add numbers, sources or claims. Keep the synthetic-data warning and any "
                       "missing-evidence warnings."),
            "messages": [{"role": "user", "content": template_text}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "content-type": "application/json", "x-api-key": self._key, "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
