"use client";

import { useId, useState } from "react";

import type { ChatResponse } from "@/lib/types";

type Turn = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  suggestedPrompt: string;
  sizeUpdateMessage?: string | null;
  modelAvailable: boolean;
  disabled?: boolean;
  onSubmit: (message: string) => Promise<ChatResponse>;
  onTurnComplete?: (response: ChatResponse) => void;
};

export function Chat({
  suggestedPrompt,
  sizeUpdateMessage,
  modelAvailable,
  disabled = false,
  onSubmit,
  onTurnComplete,
}: Props) {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [inspectDetail, setInspectDetail] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const inputId = useId();

  async function submitMessage(message: string) {
    const trimmed = message.trim();
    if (!trimmed || pending) {
      return;
    }
    setPending(true);
    setError(null);
    setInspectDetail(null);
    setTurns((current) => [...current, { role: "user", content: trimmed }]);
    setInput("");
    try {
      const response = await onSubmit(trimmed);
      onTurnComplete?.(response);
      if (response.status === "completed") {
        setTurns((current) => [
          ...current,
          { role: "assistant", content: response.message.content },
        ]);
      } else {
        setInspectDetail(response.detail);
      }
    } catch (submitError) {
      const detail =
        submitError instanceof Error ? submitError.message : "Request failed";
      setError(detail);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex h-full min-h-[28rem] flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-900">Conversation</h2>
        <div className="flex flex-wrap gap-2">
          {sizeUpdateMessage ? (
            <button
              type="button"
              disabled={disabled || pending}
              onClick={() => void submitMessage(sizeUpdateMessage)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Update size
            </button>
          ) : null}
          <button
            type="button"
            disabled={disabled || pending}
            onClick={() => void submitMessage(suggestedPrompt)}
            className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            Run example
          </button>
        </div>
      </div>

      <div className="mt-4 flex-1 space-y-4 overflow-y-auto rounded-xl bg-slate-50 p-4">
        {turns.length === 0 ? (
          <p className="text-sm text-slate-600">
            Ask for a waterproof hiking jacket recommendation, or run the example
            prompt.
          </p>
        ) : (
          turns.map((turn, index) => (
            <div
              key={`${turn.role}-${index}`}
              className={
                turn.role === "user"
                  ? "ml-8 rounded-xl bg-white p-4 text-sm text-slate-800 shadow-sm"
                  : "mr-8 rounded-xl bg-slate-900 p-4 text-sm text-white"
              }
            >
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide opacity-70">
                {turn.role === "user" ? "Customer" : "Assistant"}
              </p>
              <p>{turn.content}</p>
            </div>
          ))
        )}
      </div>

      {!modelAvailable ? (
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Set <code className="font-mono">OPENAI_API_KEY</code> to run the AI response.
          Memory inspection still works without it.
        </p>
      ) : null}

      {inspectDetail ? (
        <p className="mt-4 rounded-lg border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-700">
          {inspectDetail}
        </p>
      ) : null}

      {error ? (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <form
        className="mt-4 flex gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          void submitMessage(input);
        }}
      >
        <label htmlFor={inputId} className="sr-only">
          Message
        </label>
        <input
          id={inputId}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          disabled={disabled || pending}
          placeholder="Ask the assistant..."
          className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-slate-900 focus:ring-2 disabled:bg-slate-100"
        />
        <button
          type="submit"
          disabled={disabled || pending}
          className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {pending ? "Sending..." : "Send"}
        </button>
      </form>
    </section>
  );
}
