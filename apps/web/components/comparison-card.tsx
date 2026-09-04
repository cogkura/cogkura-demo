import type { ComparisonResult } from "@/lib/types";

import { ComparisonContextPanel } from "./comparison-context";
import { ComparisonMetricsPanel } from "./comparison-metrics";

type Props = {
  result: ComparisonResult;
};

export function ComparisonCard({ result }: Props) {
  return (
    <article className="flex h-full min-w-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header>
        <h3 className="text-lg font-semibold text-slate-900">{result.label}</h3>
        <p className="mt-1 text-sm text-slate-600">
          {result.mode === "cogkura"
            ? `${result.metrics.context_units} chunks`
            : `${result.metrics.context_units} units`}{" "}
          · ~{result.metrics.context_tokens} tokens ·{" "}
          {Math.round(result.metrics.context_prepare_ms)} ms prepare
        </p>
      </header>

      <ComparisonMetricsPanel
        relevance={result.relevance}
        contextUnits={result.metrics.context_units}
      />

      <div className="mt-4 flex-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Model answer
        </p>
        {result.error ? (
          <p className="mt-2 text-sm text-red-700">{result.error}</p>
        ) : result.answer ? (
          <p className="mt-2 text-sm text-slate-800">{result.answer}</p>
        ) : (
          <p className="mt-2 text-sm text-slate-500">
            Inspect-only — context prepared without a model call.
          </p>
        )}
      </div>

      <div className="mt-4">
        <ComparisonContextPanel
          context={result.context}
          mode={result.mode}
          relevance={result.relevance}
          diagnostics={result.diagnostics}
          defaultCollapsed={result.mode === "full_history"}
        />
      </div>
    </article>
  );
}
