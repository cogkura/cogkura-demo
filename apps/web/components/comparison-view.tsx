"use client";

import { useState } from "react";

import { compareStrategies } from "@/lib/api";
import type { ComparisonResponse } from "@/lib/types";

import { ComparisonCard } from "./comparison-card";
import { ComparisonForm } from "./comparison-form";
import { ComparisonSummary } from "./comparison-summary";

type Props = {
  suggestedPrompt: string;
  modelAvailable: boolean;
  disabled?: boolean;
};

export function ComparisonView({
  suggestedPrompt,
  modelAvailable,
  disabled = false,
}: Props) {
  const [response, setResponse] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState<"preparing" | "generating" | null>(
    null,
  );

  async function handleSubmit(message: string, generateAnswers: boolean) {
    setLoading(true);
    setLoadingPhase("preparing");
    setError(null);
    try {
      if (generateAnswers && modelAvailable) {
        setLoadingPhase("generating");
      }
      const result = await compareStrategies({ message, generate_answers: generateAnswers });
      setResponse(result);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Comparison failed",
      );
    } finally {
      setLoading(false);
      setLoadingPhase(null);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">
          Same customer. Same question. Same model. Different memory strategy.
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Compare read-only context preparation across full history, lexical search,
          and CogKura working memory. No purchases, returns, or learning run here.
          Labelled coverage measures application-defined source evidence; unclassified
          units may still be useful.
        </p>
      </section>

      <ComparisonForm
        suggestedPrompt={suggestedPrompt}
        modelAvailable={modelAvailable}
        disabled={disabled}
        loading={loading}
        loadingPhase={loadingPhase}
        onSubmit={handleSubmit}
      />

      {error ? <p className="text-sm text-red-700">{error}</p> : null}

      {response ? (
        <>
          <ComparisonSummary results={response.results} />
          <div className="grid min-w-0 gap-6 xl:grid-cols-3">
            {response.results.map((result) => (
              <ComparisonCard key={result.mode} result={result} />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
