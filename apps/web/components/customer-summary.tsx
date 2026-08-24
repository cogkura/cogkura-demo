import type { CustomerSummary, HistorySummary } from "@/lib/types";

type Props = {
  customer: CustomerSummary;
  history: HistorySummary;
};

export function CustomerSummaryPanel({ customer, history }: Props) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
        Customer
      </p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">
        {customer.name}
      </h2>
      <dl className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Customer since</dt>
          <dd className="font-medium">{customer.customer_since}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Orders</dt>
          <dd className="font-medium">{customer.order_count}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Returns</dt>
          <dd className="font-medium">{customer.return_count}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Historical events</dt>
          <dd className="font-medium">{history.events}</dd>
        </div>
      </dl>
    </section>
  );
}
