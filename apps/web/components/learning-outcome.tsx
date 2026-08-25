import type { LearningChange } from "@/lib/types";

type Props = {
  learning: LearningChange | null;
};

export function LearningOutcomePanel({ learning }: Props) {
  if (!learning) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-violet-200 bg-violet-50 p-5 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-violet-900">
        Learning outcome
      </h2>
      <dl className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-800 sm:grid-cols-4">
        <div>
          <dt className="text-xs uppercase text-violet-700">Outcome</dt>
          <dd className="font-medium">{learning.outcome}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-violet-700">Helpful</dt>
          <dd className="font-medium">{learning.helpful}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-violet-700">Unhelpful</dt>
          <dd className="font-medium">{learning.unhelpful}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-violet-700">Reinforced</dt>
          <dd className="font-medium">{learning.memories_reinforced}</dd>
        </div>
      </dl>
    </section>
  );
}
