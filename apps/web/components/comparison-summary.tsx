import type { ComparisonResult } from "@/lib/types";

type Props = {
  results: ComparisonResult[];
};

export function ComparisonSummary({ results }: Props) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <caption className="px-4 py-3 text-left text-xs text-slate-500">
          Units are memories or events in context. Labelled coverage scores a
          small gold set of evidence events, not whether a unit was used.
        </caption>
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-semibold">Strategy</th>
            <th className="px-4 py-3 font-semibold">Context tokens</th>
            <th className="px-4 py-3 font-semibold">Units in context</th>
            <th className="px-4 py-3 font-semibold">Labelled coverage</th>
            <th className="px-4 py-3 font-semibold">Unclassified</th>
            <th className="px-4 py-3 font-semibold">Stale units</th>
            <th className="px-4 py-3 font-semibold">Model input</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.mode} className="border-b border-slate-100 last:border-0">
              <th scope="row" className="px-4 py-3 font-medium text-slate-900">
                {result.label}
              </th>
              <td className="px-4 py-3 text-slate-700">
                ~{result.metrics.context_tokens.toLocaleString("en-GB")}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {result.metrics.context_units}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {result.relevance.expected_concepts_found}/
                {result.relevance.expected_concepts_total}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {result.relevance.unclassified_units}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {result.relevance.stale_units}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {result.metrics.model_input_tokens?.toLocaleString("en-GB") ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
