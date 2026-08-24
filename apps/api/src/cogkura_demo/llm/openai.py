"""OpenAI Responses API client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI

from cogkura_demo.catalogue import Product


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    request_id: str
    input_tokens: int | None
    output_tokens: int | None


class LLMClient(Protocol):
    async def respond(
        self,
        *,
        system_prompt: str,
        customer_memory: str,
        user_message: str,
        products: list[Product],
        assessment_flags: list[str],
    ) -> LLMResponse: ...


def _format_products(products: list[Product]) -> str:
    return json.dumps(
        [
            {
                "id": product.id,
                "name": product.name,
                "price_gbp": product.price_gbp,
                "waterproof": product.waterproof,
                "weight_grams": product.weight_grams,
                "colours": product.colours,
                "sizes": product.sizes,
                "fit": product.fit,
                "description": product.description,
            }
            for product in products
        ],
        indent=2,
    )


def build_system_prompt() -> str:
    return (
        "You are the shopping and customer-support assistant for Northstar Outfitters.\n\n"
        "Use the supplied customer memory when it is relevant.\n"
        "Do not claim to know customer information that is not present in memory.\n"
        "Use current product catalogue data for recommendations.\n"
        "If customer memory conflicts with current product data, product data is authoritative "
        "for current availability and specifications.\n\n"
        "If memory assessment flags include MISSING_KNOWLEDGE, do not fabricate the missing "
        "customer preference.\n\n"
        "Be concise and helpful."
    )


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model = model

    async def respond(
        self,
        *,
        system_prompt: str,
        customer_memory: str,
        user_message: str,
        products: list[Product],
        assessment_flags: list[str],
    ) -> LLMResponse:
        memory_block = customer_memory or "(No relevant customer memory selected.)"
        product_block = _format_products(products)
        assessment_block = ", ".join(assessment_flags) if assessment_flags else "none"
        input_text = (
            "SYSTEM INSTRUCTIONS\n"
            f"{system_prompt}\n\n"
            "CUSTOMER MEMORY\n"
            f"{memory_block}\n\n"
            "MEMORY ASSESSMENT FLAGS\n"
            f"{assessment_block}\n\n"
            "CURRENT CUSTOMER MESSAGE\n"
            f"{user_message}\n\n"
            "PRODUCT DATA\n"
            f"{product_block}"
        )
        response = await self._client.responses.create(
            model=self._model,
            input=input_text,
        )
        content = response.output_text
        usage = response.usage
        input_tokens = usage.input_tokens if usage is not None else None
        output_tokens = usage.output_tokens if usage is not None else None
        request_id = response.id
        return LLMResponse(
            content=content,
            request_id=request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
