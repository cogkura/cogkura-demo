"use client";

import { useState } from "react";

import { sendEvent } from "@/lib/api";
import type {
  EventResponse,
  LearningChange,
  MemoryValueChange,
  Product,
  ReturnReasonOption,
} from "@/lib/types";

type Props = {
  turnId: string | null;
  products: Product[];
  recommendedProductIds: string[];
  returnReasons: ReturnReasonOption[];
  disabled?: boolean;
  onOutcome: (payload: {
    event: EventResponse;
    learning: LearningChange | null;
    memoryChanges: MemoryValueChange[];
    orderId: string | null;
  }) => void;
};

export function ProductOutcomesPanel({
  turnId,
  products,
  recommendedProductIds,
  returnReasons,
  disabled = false,
  onOutcome,
}: Props) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastOrderId, setLastOrderId] = useState<string | null>(null);
  const [selectedReasonId, setSelectedReasonId] = useState(
    returnReasons[0]?.id ?? "hood-too-restrictive",
  );

  const candidateIds =
    recommendedProductIds.length > 0
      ? recommendedProductIds
      : products.map((product) => product.id);
  const candidates = products.filter((product) =>
    candidateIds.includes(product.id),
  );

  async function handlePurchase(productId: string) {
    if (!turnId || pending) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const response = await sendEvent({
        event_type: "purchase",
        product_id: productId,
        turn_id: turnId,
        client_event_id: crypto.randomUUID(),
      });
      const orderId = response.order?.id ?? null;
      setLastOrderId(orderId);
      onOutcome({
        event: response,
        learning: response.learning ?? null,
        memoryChanges: response.memory_changes,
        orderId,
      });
    } catch (purchaseError) {
      setError(
        purchaseError instanceof Error
          ? purchaseError.message
          : "Purchase failed",
      );
    } finally {
      setPending(false);
    }
  }

  async function handleReturn() {
    if (!lastOrderId || pending) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const response = await sendEvent({
        event_type: "product_return",
        order_id: lastOrderId,
        reason_id: selectedReasonId,
        client_event_id: crypto.randomUUID(),
      });
      setLastOrderId(null);
      onOutcome({
        event: response,
        learning: response.learning ?? null,
        memoryChanges: response.memory_changes,
        orderId: null,
      });
    } catch (returnError) {
      setError(
        returnError instanceof Error ? returnError.message : "Return failed",
      );
    } finally {
      setPending(false);
    }
  }

  if (!turnId) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Simulate customer outcome
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Run a chat turn first to record the recommendation context for
          purchase/return learning.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Simulate customer outcome
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Purchases apply HELPFUL learning to memories from turn{" "}
        <code className="font-mono text-xs">{turnId}</code>.
      </p>

      <div className="mt-4 space-y-3">
        {candidates.map((product) => (
          <button
            key={product.id}
            type="button"
            disabled={disabled || pending}
            onClick={() => void handlePurchase(product.id)}
            className="flex w-full items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="font-medium text-slate-900">{product.name}</span>
            <span className="text-slate-500">Purchase</span>
          </button>
        ))}
      </div>

      {lastOrderId ? (
        <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-900">Return order</p>
          <label className="mt-3 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Reason
            <select
              value={selectedReasonId}
              onChange={(event) => setSelectedReasonId(event.target.value)}
              disabled={disabled || pending}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
            >
              {returnReasons.map((reason) => (
                <option key={reason.id} value={reason.id}>
                  {reason.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={disabled || pending}
            onClick={() => void handleReturn()}
            className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {pending ? "Processing..." : "Simulate return"}
          </button>
        </div>
      ) : null}

      {error ? (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}
    </section>
  );
}
