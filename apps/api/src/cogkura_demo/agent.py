"""Shopping assistant agent orchestration."""

from __future__ import annotations

import time
from dataclasses import dataclass

from cogkura import MemoryContext

from cogkura_demo.catalogue import Catalogue, Product, waterproof_jacket_candidates
from cogkura_demo.llm.openai import LLMClient, build_system_prompt
from cogkura_demo.memory import DemoMemory, map_memory_context
from cogkura_demo.metrics import (
    TokenCounter,
    estimate_full_history_tokens,
    history_reduction_percent,
)
from cogkura_demo.models import (
    ChatCompletedResponse,
    ChatInspectResponse,
    ChatMessage,
    DemoMetrics,
    ProductResponse,
)


@dataclass(frozen=True, slots=True)
class AgentTurnResult:
    response: ChatCompletedResponse | ChatInspectResponse
    context: MemoryContext | None


class AgentService:
    def __init__(
        self,
        *,
        demo_memory: DemoMemory,
        catalogue: Catalogue,
        token_counter: TokenCounter,
        llm_client: LLMClient | None,
        model_available: bool,
    ) -> None:
        self._demo_memory = demo_memory
        self._catalogue = catalogue
        self._token_counter = token_counter
        self._llm_client = llm_client
        self._model_available = model_available

    async def handle_message(self, message: str) -> AgentTurnResult:
        bundle = self._demo_memory.bundle
        goal = bundle.scenario.goal
        total_start = time.perf_counter()

        memory_start = time.perf_counter()
        context = await self._demo_memory.prepare_customer_context(message, goal=goal)
        memory_prepare_ms = (time.perf_counter() - memory_start) * 1000.0
        memory_response = map_memory_context(context)

        product_start = time.perf_counter()
        products = waterproof_jacket_candidates(self._catalogue)
        product_search_ms = (time.perf_counter() - product_start) * 1000.0
        product_responses = [_map_product(product) for product in products]

        full_history_tokens = estimate_full_history_tokens(bundle.history, self._token_counter)
        metrics_base = DemoMetrics(
            history_events=len(bundle.history),
            estimated_full_history_tokens=full_history_tokens,
            memory_items=len(memory_response.items),
            memory_context_tokens=memory_response.estimated_tokens,
            history_context_reduction_percent=history_reduction_percent(
                full_history_tokens,
                memory_response.estimated_tokens,
            ),
            memory_prepare_ms=round(memory_prepare_ms, 1),
            product_search_ms=round(product_search_ms, 1),
            model_latency_ms=None,
            total_latency_ms=0.0,
        )

        if not self._model_available or self._llm_client is None:
            total_ms = (time.perf_counter() - total_start) * 1000.0
            metrics = metrics_base.model_copy(update={"total_latency_ms": round(total_ms, 1)})
            return AgentTurnResult(
                response=ChatInspectResponse(
                    memory=memory_response,
                    products=product_responses,
                    metrics=metrics,
                ),
                context=None,
            )

        model_start = time.perf_counter()
        llm_response = await self._llm_client.respond(
            system_prompt=build_system_prompt(),
            customer_memory=memory_response.rendered,
            user_message=message,
            products=products,
            assessment_flags=memory_response.assessment.flags,
        )
        model_latency_ms = (time.perf_counter() - model_start) * 1000.0
        await self._demo_memory.record_context_use(context, request_id=llm_response.request_id)

        total_ms = (time.perf_counter() - total_start) * 1000.0
        metrics = metrics_base.model_copy(
            update={
                "model_input_tokens": llm_response.input_tokens,
                "model_output_tokens": llm_response.output_tokens,
                "model_latency_ms": round(model_latency_ms, 1),
                "total_latency_ms": round(total_ms, 1),
            }
        )
        return AgentTurnResult(
            response=ChatCompletedResponse(
                message=ChatMessage(content=llm_response.content),
                memory=memory_response,
                products=product_responses,
                metrics=metrics,
            ),
            context=context,
        )


def _map_product(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        category=product.category,
        price_gbp=product.price_gbp,
        waterproof=product.waterproof,
        weight_grams=product.weight_grams,
        colours=product.colours,
        sizes=product.sizes,
        fit=product.fit,
        description=product.description,
    )
