"""IBM watsonx.ai / Granite 3.0 inference client with JSON guardrails and retry policy."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Default Granite model for extraction and reasoning
GRANITE_MODEL_ID = "ibm/granite-3-8b-instruct"


def clean_json_response(raw_text: str) -> dict[str, Any] | list[Any]:
    """Strip markdown fences and leading/trailing conversational text before parsing Granite output.
    
    Prevents formatting artifacts from triggering pipeline fallbacks.
    """
    text = raw_text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()
    
    # If there is still leading prose, locate the first { or [ to the last matching } or ]
    start_brace = text.find("{")
    start_bracket = text.find("[")
    
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        start = start_brace
        end = text.rfind("}")
    elif start_bracket != -1:
        start = start_bracket
        end = text.rfind("]")
    else:
        start = -1
        end = -1
        
    if start != -1 and end != -1 and end >= start:
        text = text[start : end + 1].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Granite response not parseable as JSON after cleaning: {exc} | Raw snippet: {raw_text[:200]}"
        ) from exc


class GraniteBudgetGuard:
    """Guard against runaway retry loops or free-tier quota exhaustion during demos."""

    def __init__(self, max_calls_per_session: int = 200) -> None:
        self.max_calls = max_calls_per_session
        self.call_count = 0

    def check_and_increment(self) -> None:
        if self.call_count >= self.max_calls:
            raise RuntimeError("Granite call budget exhausted — check for retry loops")
        self.call_count += 1

    def reset(self) -> None:
        self.call_count = 0

    @property
    def remaining(self) -> int:
        return max(0, self.max_calls - self.call_count)


budget_guard = GraniteBudgetGuard()


class WatsonxClient:
    """Interface for invoking IBM Granite 3.0 via watsonx.ai SDK."""

    def __init__(self) -> None:
        self.api_key = (
            settings.watsonx_api_key
            or os.getenv("WATSONX_APIKEY", "")
            or os.getenv("DOCOPS_WATSONX_API_KEY", "")
        )
        self.project_id = (
            settings.watsonx_project_id
            or os.getenv("WATSONX_PROJECT_ID", "")
            or os.getenv("DOCOPS_WATSONX_PROJECT_ID", "")
        )
        self.url = settings.watsonx_url or os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self._model = None
        self._initialized = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.project_id)

    def _get_model(self):
        if not self._initialized:
            self._initialized = True
            if self.is_configured:
                try:
                    from ibm_watsonx_ai.foundation_models import Model
                    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

                    parameters = {
                        GenParams.DECODING_METHOD: "greedy",
                        GenParams.MAX_NEW_TOKENS: 1024,
                        GenParams.MIN_NEW_TOKENS: 1,
                        GenParams.TEMPERATURE: 0.0,
                        GenParams.REPETITION_PENALTY: 1.0,
                    }
                    credentials = {
                        "url": self.url,
                        "apikey": self.api_key,
                    }
                    self._model = Model(
                        model_id=GRANITE_MODEL_ID,
                        params=parameters,
                        credentials=credentials,
                        project_id=self.project_id,
                    )
                    logger.info("watsonx.ai Granite 3.0 model initialized successfully")
                except Exception as exc:
                    logger.warning("Failed to initialize watsonx.ai SDK: %s. Using deterministic fallback.", exc)
                    self._model = None
        return self._model

    def generate_json(self, prompt: str, retries: int = 1) -> dict[str, Any] | list[Any]:
        """Invoke Granite 3.0 and parse structured JSON with retry-once policy."""
        budget_guard.check_and_increment()
        model = self._get_model()
        if not model:
            raise RuntimeError("watsonx.ai Granite model is not configured or unavailable")

        attempt = 0
        last_error = None
        while attempt <= retries:
            try:
                response = model.generate_text(prompt=prompt)
                return clean_json_response(response)
            except Exception as exc:
                last_error = exc
                logger.warning("Granite generate_json failed on attempt %d: %s", attempt + 1, exc)
                attempt += 1

        raise RuntimeError(f"Granite JSON generation failed after {retries + 1} attempts: {last_error}")

    def generate_text(self, prompt: str, max_tokens: int = 256, retries: int = 1) -> str:
        """Invoke Granite 3.0 for natural-language text generation."""
        budget_guard.check_and_increment()
        model = self._get_model()
        if not model:
            raise RuntimeError("watsonx.ai Granite model is not configured or unavailable")

        attempt = 0
        last_error = None
        while attempt <= retries:
            try:
                response = model.generate_text(prompt=prompt)
                return response.strip()
            except Exception as exc:
                last_error = exc
                logger.warning("Granite generate_text failed on attempt %d: %s", attempt + 1, exc)
                attempt += 1

        raise RuntimeError(f"Granite text generation failed after {retries + 1} attempts: {last_error}")


# Global singleton instance
watsonx_client = WatsonxClient()

__all__ = [
    "GRANITE_MODEL_ID",
    "GraniteBudgetGuard",
    "WatsonxClient",
    "budget_guard",
    "clean_json_response",
    "watsonx_client",
]
