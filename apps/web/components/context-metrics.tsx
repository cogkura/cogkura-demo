import type { DemoMetrics } from "@/lib/types";

type Props = {
  metrics: DemoMetrics | null;
};

export function ContextMetrics({ metrics }: Props) {
  if (!metrics) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Context comparison</h2>
        <p className="mt-3 text-sm text-slate-600">
          Run the example to compare full customer history with CogKura working
          memory.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Context comparison</h2>
      <div className="mt-6 grid gap-6 md:grid-cols-[1fr_auto_1fr] md:items-center">
        <div className="rounded-xl bg-slate-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Customer history
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">
            {metrics.history_events} events
          </p>
          <p className="mt-1 text-sm text-slate-600">
            ~{metrics.estimated_full_history_tokens.toLocaleString()} estimated tokens
          </p>
        </div>
        <div className="text-center text-sm font-medium text-slate-500">CogKura</div>
        <div className="rounded-xl bg-emerald-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Working memory
          </p>
          <p className="mt-2 text-2xl font-semibold text-emerald-900">
            {metrics.memory_items} memories
          </p>
          <p className="mt-1 text-sm text-emerald-800">
            ~{metrics.memory_context_tokens.toLocaleString()} estimated tokens
          </p>
        </div>
      </div>
      <p className="mt-5 text-center text-lg font-semibold text-slate-900">
        {metrics.history_context_reduction_percent}% less customer-history context
      </p>

      <div className="mt-6 rounded-xl border border-slate-200 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Model request
        </p>
        <dl className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-3">
          <div>
            <dt className="text-slate-500">Input</dt>
            <dd className="font-medium">
              {metrics.model_input_tokens?.toLocaleString() ?? "—"} tokens
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Output</dt>
            <dd className="font-medium">
              {metrics.model_output_tokens?.toLocaleString() ?? "—"} tokens
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Latency</dt>
            <dd className="font-medium">
              {metrics.model_latency_ms !== null
                ? `${Math.round(metrics.model_latency_ms)} ms`
                : "—"}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
