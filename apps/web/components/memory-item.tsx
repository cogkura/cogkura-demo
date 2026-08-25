import type { MemoryItem } from "@/lib/types";

type Props = {
  item: MemoryItem;
  showDetails?: boolean;
};

export function MemoryItemCard({ item, showDetails = false }: Props) {
  return (
    <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-medium text-slate-900">{item.statement}</p>
      <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">
        {item.memory_kind.replaceAll("_", " ")}
      </p>
      {showDetails ? (
        <dl className="mt-3 grid gap-2 text-xs text-slate-600">
          {item.score !== null ? (
            <div>
              <dt className="inline font-medium">Score: </dt>
              <dd className="inline">{item.score.toFixed(3)}</dd>
            </div>
          ) : null}
          {item.activation !== null ? (
            <div>
              <dt className="inline font-medium">Activation: </dt>
              <dd className="inline">{item.activation.toFixed(3)}</dd>
            </div>
          ) : null}
          {item.retrieval_reason ? (
            <div>
              <dt className="font-medium">Retrieval</dt>
              <dd>{item.retrieval_reason}</dd>
            </div>
          ) : null}
          {item.selection_reason ? (
            <div>
              <dt className="font-medium">Selection</dt>
              <dd>{item.selection_reason}</dd>
            </div>
          ) : null}
          {item.learned_utility !== null && item.learned_utility !== undefined ? (
            <div>
              <dt className="inline font-medium">Learned utility: </dt>
              <dd className="inline">{item.learned_utility.toFixed(3)}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
    </article>
  );
}
