import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { CreateJob } from "./pages/CreateJob";
import { JobDetail } from "./pages/JobDetail";
import { getJob, getJobs, Job, JobDetail as JobDetailType } from "./lib/api";
import "./styles.css";
function App() {
  const [page, setPage] = useState("dashboard");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [job, setJob] = useState<JobDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const loadJobs = useCallback(async () => { setLoading(true); try { setJobs(await getJobs()); } finally { setLoading(false); } }, []);
  useEffect(() => { loadJobs(); }, [loadJobs]);
  const openJob = async (id: string) => { setPage("detail"); setLoading(true); try { setJob(await getJob(id)); } finally { setLoading(false); } };
  const refreshJob = useCallback(async () => { if (!job) return; try { setJob(await getJob(job.id)); } catch {} }, [job]);
  const created = (id: string) => { setPage("detail"); openJob(id); loadJobs(); };
  const navigate = (next: string) => { setPage(next); if (next === "dashboard") loadJobs(); };
  return <Layout page={page === "detail" ? "dashboard" : page} onNavigate={navigate}>
    {page === "dashboard" && <Dashboard jobs={jobs} loading={loading} onRefresh={loadJobs} onNew={() => setPage("create")} onOpen={openJob}/>}
    {page === "create" && <CreateJob onBack={() => setPage("dashboard")} onCreated={created}/>}
    {page === "detail" && <JobDetail job={job} loading={loading} onBack={() => setPage("dashboard")} onRefresh={refreshJob}/>}
  </Layout>
}
createRoot(document.getElementById("root")!).render(<StrictMode><App/></StrictMode>);