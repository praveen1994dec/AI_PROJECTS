import { Link, useNavigate } from "react-router-dom";
export default function Navbar() { const navigate = useNavigate(); const email = localStorage.getItem("email") || "Detective";
  return <nav className="border-b border-slate-800 bg-slate-950/90 px-6 py-4"><div className="mx-auto flex max-w-7xl items-center justify-between">
    <Link to="/" className="text-lg font-bold text-cyan-300">AI Cloud Cost Detective</Link><div className="flex items-center gap-5 text-sm">
      <Link to="/" className="text-slate-300 hover:text-white">Dashboard</Link><Link to="/history" className="text-slate-300 hover:text-white">History</Link>
      <span className="text-slate-500">{email}</span><button className="rounded-lg border border-slate-700 px-3 py-1.5 hover:bg-slate-800" onClick={() => { localStorage.clear(); navigate("/login"); }}>Logout</button>
    </div></div></nav>; }
