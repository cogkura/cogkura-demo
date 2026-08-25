"""Live purchase and return event handling."""

from __future__ import annotations

import time
from dataclasses import dataclass

from cogkura import LearningOutcome

from cogkura_demo.catalogue import Catalogue
from cogkura_demo.interaction_mapper import DemoInteractionMapper
from cogkura_demo.learning import build_learning_feedback, map_learning_result
from cogkura_demo.memory import DemoMemory, map_processing_summary
from cogkura_demo.models import (
    DemoOrderResponse,
    EventRequest,
    EventResponse,
    LiveEventSummary,
    MemoryValueChangeResponse,
    PurchaseEventRequest,
    ReturnEventRequest,
)
from cogkura_demo.mutations import compare_semantic_snapshots, find_product
from cogkura_demo.scenarios import HistoryEvent, validate_live_event
from cogkura_demo.session import DemoOrder, ProcessedClientEvent


@dataclass(frozen=True, slots=True)
class EventHandleResult:
    response: EventResponse


class EventService:
    def __init__(
        self,
        *,
        demo_memory: DemoMemory,
        catalogue: Catalogue,
        interaction_mapper: DemoInteractionMapper,
    ) -> None:
        self._demo_memory = demo_memory
        self._catalogue = catalogue
        self._interaction_mapper = interaction_mapper

    async def handle_event(self, request: EventRequest) -> EventHandleResult:
        session = self._demo_memory.session
        existing = session.processed_client_events.get(request.client_event_id)
        if existing is not None:
            return EventHandleResult(
                response=EventResponse.model_validate(
                    {**existing.response_payload, "status": "duplicate"}
                )
            )

        if isinstance(request, PurchaseEventRequest):
            response = await self._handle_purchase(request)
        else:
            response = await self._handle_return(request)

        session.processed_client_events[request.client_event_id] = ProcessedClientEvent(
            client_event_id=request.client_event_id,
            response_payload=response.model_dump(),
        )
        return EventHandleResult(response=response)

    async def _handle_purchase(self, request: PurchaseEventRequest) -> EventResponse:
        session = self._demo_memory.session
        turn = session.turn_records.get(request.turn_id)
        if turn is None:
            msg = f"Unknown turn_id: {request.turn_id}"
            raise ValueError(msg)
        product = find_product(self._catalogue, request.product_id)
        if product is None:
            msg = f"Unknown product_id: {request.product_id}"
            raise ValueError(msg)

        occurred_at = session.clock.advance()
        event_id = session.next_live_event_id("purchase")
        event = HistoryEvent(
            id=event_id,
            type="purchase",
            customer_id="alex",
            occurred_at=occurred_at,
            content=f"Alex purchased {product.name}.",
            product_id=product.id,
            session_id=f"sess-{event_id}",
        )
        validate_live_event(event, current_time=session.clock.current)
        before = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
        process_start = time.perf_counter()
        result = await self._demo_memory.observe_and_process(event, as_of=occurred_at)
        process_ms = (time.perf_counter() - process_start) * 1000.0
        after = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
        changes = compare_semantic_snapshots(before, after)

        feedback_id = f"learn-{request.client_event_id}"
        learning_result = await self._demo_memory.learn(
            build_learning_feedback(
                turn.context,
                feedback_id=feedback_id,
                outcome=LearningOutcome.HELPFUL,
                occurred_at=occurred_at,
            )
        )
        learning = map_learning_result(learning_result, outcome=LearningOutcome.HELPFUL)

        order_id = session.next_order_id()
        order = DemoOrder(
            id=order_id,
            product_id=product.id,
            turn_id=request.turn_id,
            purchased_at=occurred_at,
        )
        session.live_orders[order_id] = order
        session.live_events.append(event)
        session.live_purchase_count += 1
        session.memory_changes = changes
        session.last_learning = learning.model_dump()
        session.last_mutation = {
            "type": "purchase",
            "product_id": product.id,
            "process_ms": process_ms,
        }

        return EventResponse(
            event=LiveEventSummary(
                type="purchase",
                content=event.content,
                product_id=product.id,
            ),
            order=DemoOrderResponse(
                id=order.id,
                product_id=order.product_id,
                turn_id=order.turn_id,
                purchased_at=order.purchased_at.isoformat(),
            ),
            learning=learning,
            memory_changes=[_map_change(change) for change in changes],
            processing=map_processing_summary(result),
        )

    async def _handle_return(self, request: ReturnEventRequest) -> EventResponse:
        session = self._demo_memory.session
        order = session.live_orders.get(request.order_id)
        if order is None:
            msg = f"Unknown order_id: {request.order_id}"
            raise ValueError(msg)
        if order.returned_at is not None:
            msg = f"Order already returned: {request.order_id}"
            raise ValueError(msg)

        reason = self._interaction_mapper.get_return_reason(request.reason_id)
        if reason is None:
            msg = f"Unknown reason_id: {request.reason_id}"
            raise ValueError(msg)

        turn = session.turn_records.get(order.turn_id)
        if turn is None:
            msg = f"Unknown turn for order: {order.turn_id}"
            raise ValueError(msg)

        product = find_product(self._catalogue, order.product_id)
        product_name = product.name if product else order.product_id

        occurred_at = session.clock.advance()
        event_id = session.next_live_event_id("return")
        event = HistoryEvent(
            id=event_id,
            type="product_return",
            customer_id="alex",
            occurred_at=occurred_at,
            content=f"Alex returned {product_name} because {reason.reason.lower()}",
            product_id=order.product_id,
            reason=reason.reason,
            semantic_facts=reason.semantic_facts,
            session_id=f"sess-{event_id}",
        )
        validate_live_event(event, current_time=session.clock.current)
        before = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
        result = await self._demo_memory.observe_and_process(event, as_of=occurred_at)
        after = await self._demo_memory.semantic_snapshot(valid_at=occurred_at)
        changes = compare_semantic_snapshots(before, after)

        feedback_id = f"learn-{request.client_event_id}"
        learning_result = await self._demo_memory.learn(
            build_learning_feedback(
                turn.context,
                feedback_id=feedback_id,
                outcome=LearningOutcome.UNHELPFUL,
                occurred_at=occurred_at,
            )
        )
        learning = map_learning_result(learning_result, outcome=LearningOutcome.UNHELPFUL)

        order.returned_at = occurred_at
        session.live_events.append(event)
        session.live_return_count += 1
        session.memory_changes = changes
        session.last_learning = learning.model_dump()
        session.last_mutation = {"type": "return", "product_id": order.product_id}

        return EventResponse(
            event=LiveEventSummary(
                type="product_return",
                content=event.content,
                product_id=order.product_id,
                reason=reason.reason,
            ),
            learning=learning,
            memory_changes=[_map_change(change) for change in changes],
            processing=map_processing_summary(result),
        )


def _map_change(change) -> MemoryValueChangeResponse:  # type: ignore[no-untyped-def]
    return MemoryValueChangeResponse(
        predicate=change.predicate,
        before=change.before,
        after=change.after,
        kind=change.kind,
    )
