import type { RelevanceMetrics } from "@/lib/types";

type Props = {
  relevance: RelevanceMetrics;
  contextUnits: number;
};

function labelledUnitCount(relevance: RelevanceMetrics): number {
  return relevance.unit_evaluations.filter(
    (item) => item.classification !== "unclassified",
  ).length;
}

export function ComparisonMetricsPanel({ relevance, contextUnits }: Props) {
  const coveragePercent = Math.round(relevance.relevant_concept_coverage * 100);
  const labelledUnits = labelledUnitCount(relevance);
  const missingLabels = relevance.concepts_missing.map(
    (id) => relevance.concept_labels[id] ?? id,
  );

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Labelled coverage
      </p>
      <p className="mt-2 text-sm font-medium text-slate-900">
        {contextUnits} in context · {labelledUnits} labelled units ·{" "}
        {relevance.unclassified_units} unclassified
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Labelled coverage measures application-defined source evidence for
        customer concepts. Unclassified units may still be useful; the demo does
        not use an LLM judge.
      </p>
      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Labelled concept coverage</dt>
          <dd className="font-medium text-slate-900">
            {relevance.expected_concepts_found}/{relevance.expected_concepts_total}{" "}
            ({coveragePercent}%)
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Stale labelled concepts</dt>
          <dd className="font-medium text-slate-900">
            {relevance.excluded_concepts_present}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Relevant units</dt>
          <dd className="font-medium text-slate-900">{relevance.relevant_units}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Stale units</dt>
          <dd className="font-medium text-slate-900">{relevance.stale_units}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">Unclassified units</dt>
          <dd className="font-medium text-slate-900">
            {relevance.unclassified_units} of {contextUnits} still in context
          </dd>
        </div>
      </dl>
      {missingLabels.length > 0 ? (
        <p className="mt-3 text-xs text-amber-800">
          Labelled concepts not evidenced: {missingLabels.join(", ")}
        </p>
      ) : null}
    </div>
  );
}
