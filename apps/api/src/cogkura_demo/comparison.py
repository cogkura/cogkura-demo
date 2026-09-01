"""Comparison orchestration service."""

from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import uuid4

from cogkura_demo.catalogue import Catalogue, Product, waterproof_jacket_candidates
from cogkura_demo.context_strategies.base import (
    MODE_LABELS,
    CustomerContextStrategy,
    PreparedCustomerContext,
)
from cogkura_demo.context_strategies.bm25 import Bm25SearchStrategy
from cogkura_demo.context_strategies.cogkura import CogKuraStrategy
from cogkura_demo.context_strategies.full_history import FullHistoryStrategy
from cogkura_demo.evaluation import ComparisonEvaluator
from cogkura_demo.llm.openai import LLMClient, build_system_prompt
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import TokenCounter
from cogkura_demo.models import (
    ComparisonContextResponse,
    ComparisonContextUnitResponse,
    ComparisonMetrics,
    ComparisonRequest,
    ComparisonResponse,
    ComparisonResultResponse,
    ComparisonSnapshotResponse,
    ContextStrategyDiagnosticsResponse,
    ProductResponse,
)


@dataclass(frozen=True, slots=True)
class ComparisonRunResult:
    response: ComparisonResponse


class ComparisonService:
    def __init__(
        self,
        *,
        demo_memory: DemoMemory,
        catalogue: Catalogue,
        token_counter: TokenCounter,
        evaluator: ComparisonEvaluator,
        llm_client: LLMClient | None,
        model_available: bool,
        search_budget_tokens: int,
        search_max_events: int,
    ) -> None:
        self._demo_memory = demo_memory
        self._catalogue = catalogue
        self._token_counter = token_counter
        self._evaluator = evaluator
        self._llm_client = llm_client
        self._model_available = model_available
        self._strategies: list[CustomerContextStrategy] = [
            FullHistoryStrategy(token_counter=token_counter),
            Bm25SearchStrategy(
                token_counter=token_counter,
                catalogue=catalogue,
                budget_tokens=search_budget_tokens,
                max_events=search_max_events,
            ),
            CogKuraStrategy(demo_memory=demo_memory),
        ]

    async def compare(self, request: ComparisonRequest) -> ComparisonRunResult:
        session = self._demo_memory.session
        bundle = session.seed_bundle
        snapshot = session.snapshot(snapshot_id=f"comparison-{uuid4().hex[:8]}")
        products = waterproof_jacket_candidates(self._catalogue)
        product_responses = [_map_product(product) for product in products]
        goal = bundle.scenario.goal

        prepared: list[PreparedCustomerContext] = []
        for strategy in self._strategies:
            prepared.append(
                await strategy.prepare(
                    message=request.message,
                    goal=goal,
                    snapshot=snapshot,
                )
            )

        results: list[ComparisonResultResponse] = []
        for context in prepared:
            relevance = self._evaluator.evaluate(context, snapshot.history)
            answer: str | None = None
            error: str | None = None
            metrics = ComparisonMetrics(
                context_tokens=context.estimated_tokens,
                context_units=len(context.units),
                context_prepare_ms=context.prepare_ms,
            )
            if request.generate_answers and self._model_available and self._llm_client is not None:
                model_start = time.perf_counter()
                try:
                    llm_response = await self._llm_client.respond(
                        system_prompt=build_system_prompt(),
                        customer_context=context.rendered,
                        user_message=request.message,
                        products=products,
                        assessment_flags=[],
                    )
                    answer = llm_response.content
                    metrics = metrics.model_copy(
                        update={
                            "model_input_tokens": llm_response.input_tokens,
                            "model_output_tokens": llm_response.output_tokens,
                            "model_latency_ms": round(
                                (time.perf_counter() - model_start) * 1000.0,
                                1,
                            ),
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    error = str(exc)
            results.append(
                ComparisonResultResponse(
                    mode=context.mode.value,
                    label=MODE_LABELS[context.mode],
                    answer=answer,
                    context=_map_context(context),
                    relevance=relevance,
                    metrics=metrics,
                    diagnostics=_map_diagnostics(context),
                    error=error,
                )
            )

        return ComparisonRunResult(
            response=ComparisonResponse(
                snapshot=ComparisonSnapshotResponse(
                    id=snapshot.snapshot_id,
                    as_of=snapshot.as_of.isoformat(),
                    history_events=len(snapshot.history),
                    history_version=snapshot.history_version,
                ),
                message=request.message,
                products=product_responses,
                results=results,
            )
        )


def _map_context(context: PreparedCustomerContext) -> ComparisonContextResponse:
    return ComparisonContextResponse(
        rendered=context.rendered,
        estimated_tokens=context.estimated_tokens,
        units=[
            ComparisonContextUnitResponse(
                id=unit.id,
                text=unit.text,
                source_event_ids=list(unit.source_event_ids),
                score=unit.score,
                kind=unit.kind,
                activation=unit.activation,
                retrieval_reason=unit.retrieval_reason,
                association_path=unit.association_path,
                relevance_tier=unit.relevance_tier,
                structured_association_fit=unit.structured_association_fit,
            )
            for unit in context.units
        ],
    )


def _map_diagnostics(
    context: PreparedCustomerContext,
) -> ContextStrategyDiagnosticsResponse | None:
    diagnostics = context.diagnostics
    if all(
        value is None
        for value in (
            diagnostics.budget_tokens,
            diagnostics.used_tokens,
            diagnostics.remaining_tokens,
            diagnostics.selected_units,
            diagnostics.candidate_units,
            diagnostics.unit_cap,
            diagnostics.unit_cap_reached,
            diagnostics.budget_constrained,
            diagnostics.corpus_events,
            diagnostics.prompt_budget_tokens,
        )
    ):
        return None
    return ContextStrategyDiagnosticsResponse(
        budget_tokens=diagnostics.budget_tokens,
        used_tokens=diagnostics.used_tokens,
        remaining_tokens=diagnostics.remaining_tokens,
        selected_units=diagnostics.selected_units,
        candidate_units=diagnostics.candidate_units,
        unit_cap=diagnostics.unit_cap,
        unit_cap_reached=diagnostics.unit_cap_reached,
        budget_constrained=diagnostics.budget_constrained,
        corpus_events=diagnostics.corpus_events,
        prompt_budget_tokens=diagnostics.prompt_budget_tokens,
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
