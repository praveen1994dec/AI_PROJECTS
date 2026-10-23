import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import Login from "./pages/Login"; import Signup from "./pages/Signup"; import Dashboard from "./pages/Dashboard";
import History from "./pages/History"; import Report from "./pages/Report"; import Navbar from "./components/Navbar";
function Protected({ children }: { children: React.ReactNode }) { return localStorage.getItem("token") ? <>{children}</> : <Navigate to="/login" replace />; }
export default function App() {
  return <Routes><Route path="/login" element={<Login />} /><Route path="/signup" element={<Signup />} />
    <Route element={<Protected><><Navbar /><Outlet /></></Protected>}><Route path="/" element={<Dashboard />} /><Route path="/history" element={<History />} /><Route path="/report/:id" element={<Report />} /></Route>
    <Route path="*" element={<Navigate to="/" replace />} /></Routes>;
}
