import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const money = (value: unknown) => `$${Number(value || 0).toFixed(2)}`;

export default function AnomalyChart({
  series,
  anomalies,
}: {
  series: any[];
  anomalies: any[];
}) {
  const data = series
    .slice(-10)
    .map((item) => ({ date: item.date, amount: Number(item.amount || 0) }));
  const total = data.reduce((sum, item) => sum + item.amount, 0);
  const average = data.length ? total / data.length : 0;
  const peak = data.reduce(
    (highest, item) => (item.amount > highest.amount ? item : highest),
    { date: "", amount: 0 },
  );
  const last = data[data.length - 1]?.amount || 0;
  const first = data[0]?.amount || 0;
  const trend =
    last > first * 1.1 ? "rising" : last < first * 0.9 ? "falling" : "stable";

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Cost trend & anomalies</h2>
          <p className="mt-1 text-xs text-slate-500">
            Daily spend for the last 10 days
          </p>
        </div>
        <span
          className={`rounded-full px-2 py-1 text-xs ${
            anomalies.length
              ? "bg-amber-950 text-amber-300"
              : "bg-emerald-950 text-emerald-300"
          }`}
        >
          {anomalies.length
            ? `${anomalies.length} spike${anomalies.length === 1 ? "" : "s"}`
            : "No unusual spend"}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <Metric label="Daily average" value={money(average)} />
        <Metric label="Peak day" value={peak.date ? money(peak.amount) : "—"} />
        <Metric label="Trend" value={data.length > 1 ? trend : "Building"} />
      </div>

      {data.length ? (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
            <YAxis tickFormatter={(value) => `$${value}`} stroke="#64748b" />
            <Tooltip
              formatter={(value: number) => [money(value), "Daily spend"]}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Area
              type="monotone"
              dataKey="amount"
              stroke="#22d3ee"
              fill="#164e63"
              fillOpacity={0.55}
            />
            {anomalies.slice(-10).map((anomaly, index) => {
              const point = data.find((item) => item.date === anomaly.date);
              return point ? (
                <ReferenceDot
                  key={`${anomaly.date}-${index}`}
                  x={point.date}
                  y={point.amount}
                  r={6}
                  fill={anomaly.severity === "high" ? "#f87171" : "#fbbf24"}
                  stroke="#0f172a"
                  strokeWidth={2}
                />
              ) : null;
            })}
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div className="my-8 rounded-lg border border-dashed border-slate-700 p-6 text-center text-sm text-slate-400">
          Cost trend will appear after Cost Explorer returns daily usage data.
        </div>
      )}

      <div className="mt-2 space-y-2">
        {anomalies.slice(-5).map((anomaly, index) => (
          <div
            key={`${anomaly.date}-${index}`}
            className="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="font-medium text-slate-200">
                {anomaly.date} · {anomaly.service || "All services"}
              </span>
              <span
                className={
                  anomaly.severity === "high"
                    ? "text-red-300"
                    : anomaly.severity === "medium"
                      ? "text-amber-300"
                      : "text-yellow-300"
                }
              >
                {anomaly.severity || "medium"} ·{" "}
                {Number(anomaly.pct_change || 0).toFixed(1)}% vs baseline
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              {money(anomaly.amount)} spent. Review recent deployments, traffic,
              and newly created resources for this day.
            </p>
          </div>
        ))}
        {!anomalies.length && (
          <p className="text-xs text-emerald-300">
            No days exceeded the configured 20% deviation threshold.
          </p>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-800/60 px-3 py-2">
      <p className="text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-slate-200">{value}</p>
    </div>
  );
}
