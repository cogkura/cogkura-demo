"""Shopping assistant agent orchestration."""

from __future__ import annotations

import time
from dataclasses import dataclass

from cogkura import MemoryContext

from cogkura_demo.catalogue import Catalogue, Product, waterproof_jacket_candidates
from cogkura_demo.interaction_mapper import DemoInteractionMapper
from cogkura_demo.llm.openai import LLMClient, build_system_prompt
from cogkura_demo.memory import DemoMemory, map_memory_context, map_processing_summary
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
    LiveEventSummary,
    MemoryMutationResponse,
    MemoryValueChangeResponse,
    ProductResponse,
)
from cogkura_demo.mutations import compare_semantic_snapshots, match_products_in_text
from cogkura_demo.scenarios import validate_live_event
from cogkura_demo.session import AgentTurnRecord


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
        interaction_mapper: DemoInteractionMapper,
    ) -> None:
        self._demo_memory = demo_memory
        self._catalogue = catalogue
        self._token_counter = token_counter
        self._llm_client = llm_client
        self._model_available = model_available
        self._interaction_mapper = interaction_mapper

    async def handle_message(self, message: str) -> AgentTurnResult:
        session = self._demo_memory.session
        bundle = session.seed_bundle
        goal = bundle.scenario.goal
        turn_id = session.next_turn_id()
        total_start = time.perf_counter()

        mutation: MemoryMutationResponse | None = None
        memory_process_ms: float | None = None
        if self._interaction_mapper.matches_statement(message):
            occurred_at = session.clock.advance()
            mutation_event = self._interaction_mapper.map_statement(
                message,
                occurred_at=occurred_at,
                event_id=session.next_live_event_id("statement"),
            )
            if mutation_event is not None:
                validate_live_event(mutation_event, current_time=session.clock.current)
                before = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
                process_start = time.perf_counter()
                result = await self._demo_memory.observe_and_process(
                    mutation_event,
                    as_of=occurred_at,
                )
                memory_process_ms = (time.perf_counter() - process_start) * 1000.0
                after = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
                changes = compare_semantic_snapshots(before, after)
                session.live_events.append(mutation_event)
                session.memory_changes = changes
                mutation = MemoryMutationResponse(
                    event=LiveEventSummary(
                        type=mutation_event.type,
                        content=mutation_event.content,
                    ),
                    memory_changes=[
                        MemoryValueChangeResponse(
                            predicate=change.predicate,
                            before=change.before,
                            after=change.after,
                            kind=change.kind,
                        )
                        for change in changes
                    ],
                    processing=map_processing_summary(result),
                )

        memory_start = time.perf_counter()
        context = await self._demo_memory.prepare_customer_context(
            message,
            goal=goal,
            as_of=session.clock.current,
        )
        memory_prepare_ms = (time.perf_counter() - memory_start) * 1000.0
        memory_response = map_memory_context(context)

        product_start = time.perf_counter()
        products = waterproof_jacket_candidates(self._catalogue)
        product_search_ms = (time.perf_counter() - product_start) * 1000.0
        product_responses = [_map_product(product) for product in products]

        full_history_tokens = estimate_full_history_tokens(session.history, self._token_counter)
        metrics_base = DemoMetrics(
            history_events=len(session.history),
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
            memory_process_ms=round(memory_process_ms, 1) if memory_process_ms else None,
        )

        recommended_product_ids: list[str] = []

        if not self._model_available or self._llm_client is None:
            total_ms = (time.perf_counter() - total_start) * 1000.0
            metrics = metrics_base.model_copy(update={"total_latency_ms": round(total_ms, 1)})
            session.turn_records[turn_id] = AgentTurnRecord(
                turn_id=turn_id,
                occurred_at=session.clock.current,
                context=context,
                response_id=None,
                recommended_product_ids=tuple(recommended_product_ids),
                message=message,
            )
            return AgentTurnResult(
                response=ChatInspectResponse(
                    turn_id=turn_id,
                    memory=memory_response,
                    products=product_responses,
                    metrics=metrics,
                    mutation=mutation,
                    recommended_product_ids=recommended_product_ids,
                ),
                context=context,
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
        recommended_product_ids = match_products_in_text(llm_response.content, self._catalogue)
        await self._demo_memory.record_context_use(
            context,
            request_id=llm_response.request_id,
            referenced_at=session.clock.current,
        )

        total_ms = (time.perf_counter() - total_start) * 1000.0
        metrics = metrics_base.model_copy(
            update={
                "model_input_tokens": llm_response.input_tokens,
                "model_output_tokens": llm_response.output_tokens,
                "model_latency_ms": round(model_latency_ms, 1),
                "total_latency_ms": round(total_ms, 1),
            }
        )
        session.turn_records[turn_id] = AgentTurnRecord(
            turn_id=turn_id,
            occurred_at=session.clock.current,
            context=context,
            response_id=llm_response.request_id,
            recommended_product_ids=tuple(recommended_product_ids),
            message=message,
        )
        return AgentTurnResult(
            response=ChatCompletedResponse(
                turn_id=turn_id,
                message=ChatMessage(content=llm_response.content),
                memory=memory_response,
                products=product_responses,
                metrics=metrics,
                mutation=mutation,
                recommended_product_ids=recommended_product_ids,
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
