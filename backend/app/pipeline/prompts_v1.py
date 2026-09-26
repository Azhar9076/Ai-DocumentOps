"""Prompt v1: Baseline Zero-Shot Prompting Templates for IBM Granite 3.0."""

CLASSIFIER_PROMPT_V1 = """You are a document classifier.
Classify the following text into one of: INVOICE, FORM, CONTRACT, UNKNOWN.
Return JSON with key "doc_type".

Document:
Gdocument_text}
"""

GRANITE_V_VERSIONS = {
    "prompt_v1": {"field_accuracy": 64.2, "routing_accuracy": 71.0, "label": "Prompt v1 (Zero-Shot Baseline)"},
    "prompt_v2": {"field_accuracy": 96.4, "routing_accuracy": 94.4, "label": "Prompt v2 (Few-Shot + Self-Correction)"},
}
