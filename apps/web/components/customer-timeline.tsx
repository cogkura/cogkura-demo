import type { TimelineEvent } from "@/lib/types";

type Props = {
  events: TimelineEvent[];
  totalEvents: number;
};

export function CustomerTimeline({ events, totalEvents }: Props) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-900">Customer timeline</h2>
        <p className="text-sm text-slate-500">{totalEvents} events total</p>
      </div>
      <ol className="mt-6 space-y-5 border-l border-slate-200 pl-5">
        {events.map((event) => (
          <li key={event.id} className="relative">
            <span
              className={`absolute -left-[1.35rem] top-1.5 h-2.5 w-2.5 rounded-full ${
                event.is_live ? "bg-emerald-500" : "bg-slate-400"
              }`}
            />
            <p className="text-sm font-semibold text-slate-900">
              {event.label}
              {event.is_live ? (
                <span className="ml-2 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                  Live
                </span>
              ) : null}
            </p>
            <p className="mt-1 text-sm text-slate-700">{event.detail}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
