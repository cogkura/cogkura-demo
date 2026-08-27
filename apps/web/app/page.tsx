"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDemoState, resetDemo, sendChatMessage } from "@/lib/api";
import type {
  ChatResponse,
  DemoMetrics,
  DemoStateResponse,
  LearningChange,
  MemoryContext,
  MemoryValueChange,
  Product,
} from "@/lib/types";

import { Chat } from "@/components/chat";
import { ComparisonView } from "@/components/comparison-view";
import { ContextMetrics } from "@/components/context-metrics";
import { CustomerSummaryPanel } from "@/components/customer-summary";
import { CustomerTimeline } from "@/components/customer-timeline";
import { LearningOutcomePanel } from "@/components/learning-outcome";
import { MemoryChangesPanel } from "@/components/memory-changes";
import { MemoryContextPanel } from "@/components/memory-context";
import { ProductOutcomesPanel } from "@/components/product-outcomes";

const RETURN_REASONS = [
  { id: "hood-too-restrictive", label: "Hood feels too restrictive" },
  { id: "sleeves-too-short", label: "Sleeves are too short" },
  { id: "too-heavy", label: "Too heavy" },
  { id: "colour-wrong", label: "Colour wasn't right" },
  { id: "changed-mind", label: "Changed my mind" },
];

type ViewMode = "live" | "compare";

export default function HomePage() {
  const [view, setView] = useState<ViewMode>("live");
  const [demo, setDemo] = useState<DemoStateResponse | null>(null);
  const [memory, setMemory] = useState<MemoryContext | null>(null);
  const [metrics, setMetrics] = useState<DemoMetrics | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [turnId, setTurnId] = useState<string | null>(null);
  const [recommendedProductIds, setRecommendedProductIds] = useState<string[]>(
    [],
  );
  const [memoryChanges, setMemoryChanges] = useState<MemoryValueChange[]>([]);
  const [learning, setLearning] = useState<LearningChange | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [chatKey, setChatKey] = useState(0);
  const [compareKey, setCompareKey] = useState(0);
  const requestGeneration = useRef(0);

  const loadDemo = useCallback(async () => {
    const state = await fetchDemoState();
    setDemo(state);
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        await loadDemo();
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load demo state",
        );
      } finally {
        setLoading(false);
      }
    })();
  }, [loadDemo]);

  function applyChatResponse(response: ChatResponse) {
    setMemory(response.memory);
    setMetrics(response.metrics);
    setProducts(response.products);
    setTurnId(response.turn_id);
    setRecommendedProductIds(response.recommended_product_ids);
    if (response.mutation?.memory_changes.length) {
      setMemoryChanges(response.mutation.memory_changes);
    }
  }

  async function handleSubmit(message: string) {
    const generation = requestGeneration.current;
    const response = await sendChatMessage(message);
    if (generation !== requestGeneration.current) {
      return response;
    }
    applyChatResponse(response);
    await loadDemo();
    return response;
  }

  async function handleReset() {
    setResetting(true);
    requestGeneration.current += 1;
    try {
      await resetDemo();
      setMemory(null);
      setMetrics(null);
      setProducts([]);
      setTurnId(null);
      setRecommendedProductIds([]);
      setMemoryChanges([]);
      setLearning(null);
      setChatKey((value) => value + 1);
      setCompareKey((value) => value + 1);
      await loadDemo();
    } catch (resetError) {
      setError(
        resetError instanceof Error ? resetError.message : "Reset failed",
      );
    } finally {
      setResetting(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-100 px-4 py-10">
        <p className="text-center text-slate-600">Loading demo...</p>
      </main>
    );
  }

  if (error && !demo) {
    return (
      <main className="min-h-screen bg-slate-100 px-4 py-10">
        <p className="text-center text-red-700">{error}</p>
      </main>
    );
  }

  if (!demo) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
              CogKura Demo 0.3.2
            </p>
            <h1 className="mt-1 text-3xl font-semibold text-slate-900">
              Northstar Outfitters AI Assistant
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              {demo.customer.name} · {demo.customer.order_count} orders ·{" "}
              {demo.customer.return_count} returns · {demo.history.events} events
              {demo.current_time ? ` · session ${demo.current_time.slice(0, 10)}` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleReset()}
            disabled={resetting}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {resetting ? "Resetting..." : "Reset scenario"}
          </button>
        </header>

        <nav
          aria-label="Demo views"
          className="mb-6 inline-flex rounded-xl border border-slate-300 bg-white p-1"
        >
          <button
            type="button"
            onClick={() => setView("live")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              view === "live"
                ? "bg-slate-900 text-white"
                : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            Live Memory
          </button>
          <button
            type="button"
            onClick={() => setView("compare")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              view === "compare"
                ? "bg-slate-900 text-white"
                : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            Compare
          </button>
        </nav>

        <div className="mb-6">
          <CustomerSummaryPanel
            customer={demo.customer}
            history={demo.history}
          />
        </div>

        {view === "live" ? (
          <>
            <div className="grid gap-6 lg:grid-cols-2">
              <Chat
                key={chatKey}
                suggestedPrompt={demo.scenario.suggested_prompt}
                sizeUpdateMessage={demo.scenario.size_update_message}
                modelAvailable={demo.model_available}
                disabled={resetting}
                onSubmit={handleSubmit}
              />
              <MemoryContextPanel memory={memory} />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <ProductOutcomesPanel
                turnId={turnId}
                products={products}
                recommendedProductIds={recommendedProductIds}
                returnReasons={RETURN_REASONS}
                disabled={resetting}
                onOutcome={({ learning: outcome, memoryChanges: changes }) => {
                  setLearning(outcome);
                  if (changes.length > 0) {
                    setMemoryChanges(changes);
                  }
                  void loadDemo();
                }}
              />
              <div className="space-y-6">
                <MemoryChangesPanel changes={memoryChanges} />
                <LearningOutcomePanel learning={learning} />
              </div>
            </div>

            <div className="mt-6">
              <ContextMetrics metrics={metrics} />
            </div>
          </>
        ) : (
          <ComparisonView
            key={compareKey}
            suggestedPrompt={demo.scenario.suggested_prompt}
            modelAvailable={demo.model_available}
            disabled={resetting}
          />
        )}

        <div className="mt-6">
          <CustomerTimeline
            events={demo.timeline}
            totalEvents={demo.history.events}
          />
        </div>
      </div>
    </main>
  );
}
