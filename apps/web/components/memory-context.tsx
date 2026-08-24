"use client";

import { useState } from "react";

import type { MemoryContext } from "@/lib/types";

import { MemoryItemCard } from "./memory-item";

type Props = {
  memory: MemoryContext | null;
};

export function MemoryContextPanel({ memory }: Props) {
  const [showDetails, setShowDetails] = useState(false);

  if (!memory) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Memory used for this response
        </h2>
        <p className="mt-3 text-sm text-slate-600">
          Ask a question to see which customer memories CogKura selects for the
          model.
        </p>
      </section>
    );
  }

  const flags = memory.assessment.flags;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Memory used for this response
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            {memory.items.length} memories · ~{memory.estimated_tokens} tokens
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowDetails((value) => !value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          {showDetails ? "Hide details" : "Why these memories?"}
        </button>
      </div>

      <div className="mt-4 rounded-xl bg-slate-100 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Memory assessment
        </p>
        <p className="mt-1 text-sm text-slate-800">
          {flags.length > 0 ? flags.join(", ") : "No missing-knowledge flags"}
        </p>
      </div>

      <div className="mt-4 space-y-3">
        {memory.items.map((item, index) => (
          <MemoryItemCard
            key={`${item.statement}-${index}`}
            item={item}
            showDetails={showDetails}
          />
        ))}
      </div>
    </section>
  );
}
