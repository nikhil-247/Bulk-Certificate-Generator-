export type Recipient = { name: string; email: string; designation?: string; organization?: string; };
export type Job = { id: string; certificate_title: string; event_name: string; issuer_name: string; issue_date: string; total_count: number; success_count: number; failed_count: number; status: string; created_at: string; started_at?: string | null; completed_at?: string | null; };
export type Certificate = Recipient & { id: string; status: string; certificate_code: string; error_message?: string | null; created_at: string; completed_at?: string | null; download_url?: string | null; };
export type JobDetail = Job & { certificates: Certificate[]; progress_percent: number };
const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json", ...(init?.headers || {}) }, ...init });
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: "Request failed" })); throw new Error(body.detail || "Request failed"); }
  return response.json();
}
export const getJobs = () => request<Job[]>("/jobs");
export const getJob = (id: string) => request<JobDetail>(`/jobs/${id}`);
export const createJob = (payload: unknown) => request<Job>("/jobs", { method: "POST", body: JSON.stringify(payload) });
export const downloadUrl = (certificateId: string) => `${API}/certificates/${certificateId}/download`;
export const bulkDownloadUrl = (jobId: string) => `${API}/jobs/${jobId}/download-all`;