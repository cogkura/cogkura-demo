"use client";

import { useId, useState } from "react";

type Props = {
  suggestedPrompt: string;
  modelAvailable: boolean;
  disabled?: boolean;
  loading?: boolean;
  loadingPhase?: "preparing" | "generating" | null;
  onSubmit: (message: string, generateAnswers: boolean) => Promise<void>;
};

export function ComparisonForm({
  suggestedPrompt,
  modelAvailable,
  disabled = false,
  loading = false,
  loadingPhase = null,
  onSubmit,
}: Props) {
  const [message, setMessage] = useState(suggestedPrompt);
  const [generateAnswers, setGenerateAnswers] = useState(modelAvailable);
  const inputId = useId();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || loading || disabled) {
      return;
    }
    await onSubmit(trimmed, generateAnswers);
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <label htmlFor={inputId} className="text-sm font-medium text-slate-800">
        Customer question
      </label>
      <textarea
        id={inputId}
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        rows={4}
        disabled={disabled || loading}
        className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900"
      />
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={generateAnswers}
            disabled={!modelAvailable || disabled || loading}
            onChange={(event) => setGenerateAnswers(event.target.checked)}
          />
          Generate model answers
        </label>
        <button
          type="submit"
          disabled={disabled || loading}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading
            ? loadingPhase === "generating"
              ? "Generating comparison..."
              : "Preparing customer contexts..."
            : "Run comparison"}
        </button>
      </div>
      {modelAvailable && generateAnswers ? (
        <p className="mt-3 text-xs text-slate-500">
          This runs three sequential model requests with identical prompts except
          for customer context.
        </p>
      ) : null}
    </form>
  );
}
