"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDemoState, resetDemo, sendChatMessage } from "@/lib/api";
import type {
  DemoMetrics,
  DemoStateResponse,
  MemoryContext,
} from "@/lib/types";

import { Chat } from "@/components/chat";
import { ContextMetrics } from "@/components/context-metrics";
import { CustomerSummaryPanel } from "@/components/customer-summary";
import { CustomerTimeline } from "@/components/customer-timeline";
import { MemoryContextPanel } from "@/components/memory-context";

export default function HomePage() {
  const [demo, setDemo] = useState<DemoStateResponse | null>(null);
  const [memory, setMemory] = useState<MemoryContext | null>(null);
  const [metrics, setMetrics] = useState<DemoMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [chatKey, setChatKey] = useState(0);
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

  async function handleSubmit(message: string) {
    const generation = requestGeneration.current;
    const response = await sendChatMessage(message);
    if (generation !== requestGeneration.current) {
      return response;
    }
    setMemory(response.memory);
    setMetrics(response.metrics);
    return response;
  }

  async function handleReset() {
    setResetting(true);
    requestGeneration.current += 1;
    try {
      await resetDemo();
      setMemory(null);
      setMetrics(null);
      setChatKey((value) => value + 1);
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
              CogKura Demo
            </p>
            <h1 className="mt-1 text-3xl font-semibold text-slate-900">
              Northstar Outfitters AI Assistant
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              {demo.customer.name} · customer for 18 months ·{" "}
              {demo.history.events} historical events
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

        <div className="mb-6">
          <CustomerSummaryPanel
            customer={demo.customer}
            history={demo.history}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Chat
            key={chatKey}
            suggestedPrompt={demo.scenario.suggested_prompt}
            modelAvailable={demo.model_available}
            disabled={resetting}
            onSubmit={handleSubmit}
          />
          <MemoryContextPanel memory={memory} />
        </div>

        <div className="mt-6">
          <ContextMetrics metrics={metrics} />
        </div>

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
