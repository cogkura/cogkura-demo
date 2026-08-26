import type {
  ComparisonContext,
  ComparisonResult,
  ContextStrategyDiagnostics,
  RelevanceMetrics,
} from "@/lib/types";

type Props = {
  context: ComparisonContext;
  mode: ComparisonResult["mode"];
  relevance: RelevanceMetrics;
  diagnostics: ContextStrategyDiagnostics | null;
  defaultCollapsed?: boolean;
};

const VISIBLE_EVENT_IDS = 6;

function displayUnitId(id: string): string {
  if (id.length > 16 && /^[a-f0-9]+$/i.test(id)) {
    return `${id.slice(0, 8)}…`;
  }
  return id;
}

function EventIds({ ids }: { ids: string[] }) {
  const visible = ids.slice(0, VISIBLE_EVENT_IDS);
  const extra = ids.length - visible.length;
  return (
    <p className="mt-2 break-words text-xs text-slate-500">
      Events: {visible.join(", ")}
      {extra > 0 ? ` +${extra} more` : ""}
    </p>
  );
}

function classificationLabel(classification: string): string {
  switch (classification) {
    case "relevant":
      return "Labelled relevant";
    case "stale":
      return "Stale";
    case "relevant_and_stale":
      return "Labelled relevant and stale";
    default:
      return "Unclassified";
  }
}

function DiagnosticsPanel({ diagnostics }: { diagnostics: ContextStrategyDiagnostics }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600">
      <p className="font-semibold text-slate-800">Packing diagnostics</p>
      <dl className="mt-2 grid gap-1 sm:grid-cols-2">
        {diagnostics.budget_tokens !== null ? (
          <div>
            <dt className="inline text-slate-500">Budget: </dt>
            <dd className="inline">{diagnostics.budget_tokens} tokens</dd>
          </div>
        ) : null}
        {diagnostics.used_tokens !== null ? (
          <div>
            <dt className="inline text-slate-500">Used: </dt>
            <dd className="inline">{diagnostics.used_tokens} tokens</dd>
          </div>
        ) : null}
        {diagnostics.remaining_tokens !== null ? (
          <div>
            <dt className="inline text-slate-500">Remaining: </dt>
            <dd className="inline">{diagnostics.remaining_tokens} tokens</dd>
          </div>
        ) : null}
        {diagnostics.selected_units !== null ? (
          <div>
            <dt className="inline text-slate-500">Selected: </dt>
            <dd className="inline">{diagnostics.selected_units} units</dd>
          </div>
        ) : null}
        {diagnostics.unit_cap !== null ? (
          <div>
            <dt className="inline text-slate-500">Event safety cap: </dt>
            <dd className="inline">{diagnostics.unit_cap}</dd>
          </div>
        ) : null}
        {diagnostics.budget_constrained !== null ? (
          <div>
            <dt className="inline text-slate-500">Budget constrained: </dt>
            <dd className="inline">{diagnostics.budget_constrained ? "yes" : "no"}</dd>
          </div>
        ) : null}
        {diagnostics.unit_cap_reached !== null ? (
          <div>
            <dt className="inline text-slate-500">Event cap reached: </dt>
            <dd className="inline">{diagnostics.unit_cap_reached ? "yes" : "no"}</dd>
          </div>
        ) : null}
        {diagnostics.prompt_budget_tokens !== null ? (
          <div>
            <dt className="inline text-slate-500">Prompt budget: </dt>
            <dd className="inline">{diagnostics.prompt_budget_tokens} tokens</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}

export function ComparisonContextPanel({
  context,
  mode,
  relevance,
  diagnostics,
  defaultCollapsed = false,
}: Props) {
  const evaluationByUnit = new Map(
    relevance.unit_evaluations.map((item) => [item.unit_id, item]),
  );

  return (
    <details
      className="min-w-0 rounded-xl border border-slate-200 bg-slate-50"
      open={!defaultCollapsed}
    >
      <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-800">
        Context inspector · {context.units.length} units · ~
        {context.estimated_tokens} tokens
      </summary>
      <div className="space-y-3 border-t border-slate-200 px-4 py-4">
        {diagnostics ? <DiagnosticsPanel diagnostics={diagnostics} /> : null}
        {context.units.length === 0 ? (
          <p className="text-sm text-slate-600">No context units selected.</p>
        ) : (
          context.units.map((unit) => {
            const evaluation = evaluationByUnit.get(unit.id);
            return (
              <article
                key={unit.id}
                className="min-w-0 overflow-hidden rounded-lg border border-slate-200 bg-white p-3"
              >
                <p className="whitespace-pre-wrap break-words text-sm text-slate-800">
                  {unit.text}
                </p>
                <div className="mt-2 flex min-w-0 items-center gap-2 text-xs text-slate-500">
                  {unit.kind ? (
                    <span className="shrink-0 uppercase tracking-wide">
                      {unit.kind.replaceAll("_", " ")}
                    </span>
                  ) : null}
                  <span
                    className="min-w-0 truncate font-mono text-slate-600"
                    title={unit.id}
                  >
                    {displayUnitId(unit.id)}
                  </span>
                  {mode === "search" && unit.score !== null ? (
                    <span className="shrink-0">BM25 {unit.score.toFixed(3)}</span>
                  ) : null}
                  {unit.activation != null ? (
                    <span className="shrink-0">
                      activation {unit.activation.toFixed(3)}
                    </span>
                  ) : null}
                </div>
                {evaluation ? (
                  <p className="mt-2 text-xs text-slate-600">
                    {classificationLabel(evaluation.classification)}
                    {evaluation.expected_concepts.length > 0
                      ? ` · expected: ${evaluation.expected_concepts
                          .map((id) => relevance.concept_labels[id] ?? id)
                          .join(", ")}`
                      : ""}
                    {evaluation.excluded_concepts.length > 0
                      ? ` · stale: ${evaluation.excluded_concepts
                          .map((id) => relevance.concept_labels[id] ?? id)
                          .join(", ")}`
                      : ""}
                    {evaluation.provenance_status === "unresolved"
                      ? " · provenance unresolved"
                      : ""}
                  </p>
                ) : null}
                {unit.retrieval_reason ? (
                  <p className="mt-1 text-xs text-slate-500">{unit.retrieval_reason}</p>
                ) : null}
                {unit.source_event_ids.length > 0 ? (
                  <EventIds ids={unit.source_event_ids} />
                ) : null}
              </article>
            );
          })
        )}
      </div>
    </details>
  );
}
