const money = (value: unknown) => `$${Number(value || 0).toFixed(2)}`;

export default function TopResourcesChart({ resources }: { resources: any[] }) {
  const data = resources.slice(0, 10);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Top cost-driving resources</h2>
          <p className="mt-1 text-xs text-slate-500">Ranked by monthly cost</p>
        </div>
        <span className="text-xs text-slate-500">{data.length} resources</span>
      </div>

      {!data.length ? (
        <p className="text-sm text-slate-500">No resource cost data available.</p>
      ) : (
        <div className="divide-y divide-slate-800">
          {data.map((resource, index) => (
            <div
              key={resource.resource_id || resource.name || index}
              className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
            >
              <span className="w-6 text-sm font-semibold text-slate-500">
                #{index + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-100">
                  {resource.name || resource.resource_id || `Resource ${index + 1}`}
                </p>
                <p className="mt-1 truncate text-xs text-slate-400">
                  {resource.resource_type || "AWS resource"}
                  {resource.resource_id && resource.name ? ` · ${resource.resource_id}` : ""}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-cyan-300">{money(resource.cost)}</p>
                <span
                  className={`text-[11px] ${
                    resource.cost_basis === "exact"
                      ? "text-emerald-300"
                      : "text-amber-300"
                  }`}
                >
                  {resource.cost_basis === "exact" ? "Exact" : "Estimated"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
