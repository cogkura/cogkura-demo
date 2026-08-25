import type { ComparisonContext, ComparisonResult } from "@/lib/types";

type Props = {
  context: ComparisonContext;
  mode: ComparisonResult["mode"];
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

export function ComparisonContextPanel({
  context,
  mode,
  defaultCollapsed = false,
}: Props) {
  const collapsed = defaultCollapsed;

  return (
    <details
      className="min-w-0 rounded-xl border border-slate-200 bg-slate-50"
      open={!collapsed}
    >
      <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-800">
        Context inspector · {context.units.length} units · ~
        {context.estimated_tokens} tokens
      </summary>
      <div className="space-y-3 border-t border-slate-200 px-4 py-4">
        {context.units.length === 0 ? (
          <p className="text-sm text-slate-600">No context units selected.</p>
        ) : (
          context.units.map((unit) => (
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
              </div>
              {unit.source_event_ids.length > 0 ? (
                <EventIds ids={unit.source_event_ids} />
              ) : null}
            </article>
          ))
        )}
      </div>
    </details>
  );
}
