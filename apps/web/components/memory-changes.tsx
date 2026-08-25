import type { MemoryValueChange } from "@/lib/types";

type Props = {
  changes: MemoryValueChange[];
};

export function MemoryChangesPanel({ changes }: Props) {
  if (changes.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-emerald-900">
        Memory changes
      </h2>
      <ul className="mt-3 space-y-2">
        {changes.map((change) => (
          <li
            key={change.predicate}
            className="rounded-lg bg-white px-4 py-3 text-sm text-slate-800"
          >
            <span className="font-medium">{change.predicate}</span>
            {": "}
            {change.before ?? "—"} → {change.after ?? "—"}
          </li>
        ))}
      </ul>
    </section>
  );
}
