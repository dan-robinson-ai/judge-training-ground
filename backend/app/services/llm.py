"""Utility functions for LLM calls using litellm with structured output support."""

from typing import TypeVar

import litellm
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


async def call_llm(
    messages: list[dict[str, str]],
    response_model: type[T],
    model: str = "gpt-4o",
    temperature: float = 0.7,
) -> T:
    """
    Call an LLM and return a structured response validated against a Pydantic model.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        response_model: Pydantic model class to validate and parse the response
        model: LiteLLM model name (default: gpt-4o)
        temperature: Sampling temperature (default: 0.7)

    Returns:
        Parsed and validated instance of response_model

    Raises:
        ValueError: If the LLM response cannot be parsed into the response model
    """
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format=response_model,
    )

    content = response.choices[0].message.content

    try:
        return response_model.model_validate_json(content)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}")
