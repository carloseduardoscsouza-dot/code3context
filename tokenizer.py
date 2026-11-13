"""
Token estimation and LLM API cost calculator.
"""

from typing import Dict, Any

# Prices per 1,000,000 input tokens (USD)
MODEL_PRICING = {
    "Claude 3.5 Sonnet": 3.00,
    "GPT-4o": 2.50,
    "Gemini 1.5 Pro": 1.25,
    "Gemini 1.5 Flash": 0.075,
    "DeepSeek V3": 0.14,
}


def estimate_tokens(text: str) -> int:
    """
    Returns exact token count if tiktoken is available,
    otherwise uses an accurate heuristic calibrated for source code & markdown.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # High accuracy code heuristic: code averages ~3.6 chars per token
        if not text:
            return 0
        return max(1, int(len(text) / 3.65))


def estimate_costs(token_count: int) -> Dict[str, float]:
    """Calculates estimated input cost across major LLMs."""
    costs = {}
    for model_name, price_per_million in MODEL_PRICING.items():
        costs[model_name] = (token_count / 1_000_000) * price_per_million
    return costs
