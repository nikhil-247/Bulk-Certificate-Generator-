import { ReactNode } from "react";
import { Award, LayoutDashboard, Plus, Sparkles } from "lucide-react";
export function Layout({ children, page, onNavigate }: { children: ReactNode; page: string; onNavigate: (page: string) => void }) {
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-icon"><Award size={20}/></div><div><strong>CertFlow</strong><small>Bulk Certificate Studio</small></div></div><nav>
    <button className={page === "dashboard" ? "nav-item active" : "nav-item"} onClick={() => onNavigate("dashboard")}><LayoutDashboard size={18}/> Dashboard</button>
    <button className={page === "create" ? "nav-item active" : "nav-item"} onClick={() => onNavigate("create")}><Plus size={18}/> New generation</button>
  </nav><div className="sidebar-note"><Sparkles size={16}/><div><strong>Assignment-ready</strong><p>Async bulk generation with job-level progress and downloadable PDFs.</p></div></div></aside>
  <main className="main"><header className="topbar"><span>Certificate Operations</span><span className="status-pill"><span className="status-green"/> API connected</span></header>{children}</main></div>;
}