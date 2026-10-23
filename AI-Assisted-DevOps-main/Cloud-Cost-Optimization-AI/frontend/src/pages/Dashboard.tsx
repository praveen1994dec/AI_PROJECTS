import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { request } from "../api";
import BudgetWidget from "../components/BudgetWidget";
import TopResourcesChart from "../components/TopResourcesChart";
import AnomalyChart from "../components/AnomalyChart";
import ProgressTracker from "../components/ProgressTracker";

const money = (value: unknown) => `$${Number(value || 0).toFixed(2)}`;
const demoRegions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-southeast-1"];

type Overview = {
  current?: any;
  previous?: any;
  forecast?: any;
  top?: any;
  anomalies?: any;
};

export default function Dashboard() {
  const [regions, setRegions] = useState<string[]>([]);
  const [region, setRegion] = useState("");
  const [overview, setOverview] = useState<Overview>({});
  const [budget, setBudget] = useState<any>({ configured: false });
  const [scan, setScan] = useState<{ progressId: string; reportId: string } | null>(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    request<string[]>("/api/regions")
      .then((available) => {
        setRegions(available);
        if (available[0]) setRegion(available[0]);
      })
      .catch((err) => {
        // Keep the dashboard usable for app configuration when AWS is not connected.
        setRegions(demoRegions);
        setRegion(demoRegions[0]);
        setError(`AWS data unavailable: showing common regions for setup. ${err.message}`);
      });
  }, []);

  useEffect(() => {
    if (!region) return;
    setOverview({});
    setError("");
    const load = <T,>(key: string, path: string, apply: (value: T) => void) => {
      setLoading((state) => ({ ...state, [key]: true }));
      request<T>(path)
        .then(apply)
        .catch((err) => setError((current) => current || err.message))
        .finally(() => setLoading((state) => ({ ...state, [key]: false })));
    };
    load("current", `/api/cost/current?region=${encodeURIComponent(region)}`, (value) => setOverview((state) => ({ ...state, current: value })));
    load("previous", `/api/cost/previous-month?region=${encodeURIComponent(region)}`, (value) => setOverview((state) => ({ ...state, previous: value })));
    load("forecast", `/api/cost/forecast?region=${encodeURIComponent(region)}`, (value) => setOverview((state) => ({ ...state, forecast: value })));
    load("top", `/api/cost/top-resources?region=${encodeURIComponent(region)}&limit=10`, (value) => setOverview((state) => ({ ...state, top: value })));
    load("anomalies", `/api/cost/anomalies?region=${encodeURIComponent(region)}`, (value) => setOverview((state) => ({ ...state, anomalies: value })));
    load("budget", `/api/budget?region=${encodeURIComponent(region)}`, setBudget);
  }, [region]);

  async function scanResources() {
    try {
      setError("");
      setScanning(true);
      const result = await request<any>("/api/analyze", {
        method: "POST",
        body: JSON.stringify({ region }),
      });
      setScan({ progressId: result.progress_id, reportId: String(result.analysis_id) });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setScanning(false);
    }
  }

  function refreshBudget() {
    request<any>(`/api/budget?region=${encodeURIComponent(region)}`)
      .then(setBudget)
      .catch((err) => setError((current) => current || err.message));
  }

  const resources = overview.top?.resources || overview.top || [];
  const anomalies = overview.anomalies?.anomalies || [];
  const overviewLoading = Object.values(loading).some(Boolean);

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Cost overview</h1>
          <p className="mt-1 text-slate-400">Fast, AI-free visibility into your AWS spend.</p>
        </div>
        <select value={region} onChange={(event) => setRegion(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-3">
          {!regions.length && <option value="">No regions available</option>}
          {regions.map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>
      {error && <p className="rounded-lg bg-red-950 p-3 text-sm text-red-300">{error}</p>}
      {overviewLoading && <p className="text-sm text-cyan-300">Loading available cost data…</p>}
      <div className="grid gap-4 md:grid-cols-3">
        {[["Current MTD", overview.current?.total, "current"], ["Previous month", overview.previous?.total, "previous"], ["15-day forecast", overview.forecast?.total, "forecast"]].map(([label, value, key]) => (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5" key={key as string}>
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-3xl font-bold">{value === undefined ? "—" : money(value)}</p>
          </div>
        ))}
      </div>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <BudgetWidget region={region} budget={budget} onSaved={refreshBudget} />
        <TopResourcesChart resources={resources} />
      </div>
      <AnomalyChart series={overview.current?.series || []} anomalies={anomalies} />
      <div className="rounded-2xl border border-cyan-900 bg-cyan-950/20 p-6">
        <h2 className="text-xl font-semibold">Ready to optimize?</h2>
        <p className="mt-1 text-sm text-slate-400">Run the deeper resource scan only when you need actionable recommendations.</p>
        <button disabled={!region || !!scan || scanning} onClick={scanResources} className="mt-4 cursor-pointer rounded-lg bg-cyan-500 px-5 py-3 font-bold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50">{scanning ? "Starting optimization scan…" : scan ? "Optimization scan started…" : "Analyze &amp; Optimize Resources"}</button>
      </div>
      {scan && <ProgressTracker analysisId={scan.progressId} onComplete={() => navigate(`/report/${scan.reportId}`)} />}
    </main>
  );
}
