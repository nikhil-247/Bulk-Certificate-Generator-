import { ChangeEvent, useMemo, useState } from "react";
import { ArrowLeft, Download, FileUp, Plus, Trash2, Upload } from "lucide-react";
import { Recipient, createJob } from "../lib/api";
const emptyRecipient = (): Recipient => ({ name: "", email: "", designation: "", organization: "" });
export function CreateJob({ onBack, onCreated }: { onBack: () => void; onCreated: (id: string) => void }) {
  const [certificate, setCertificate] = useState({ title: "Certificate of Completion", event_name: "", issuer_name: "", issue_date: new Date().toISOString().slice(0, 10) });
  const [recipients, setRecipients] = useState<Recipient[]>([emptyRecipient()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const validCount = useMemo(() => recipients.filter(r => r.name.trim() && r.email.includes("@")).length, [recipients]);
  const updateRecipient = (i: number, field: keyof Recipient, value: string) => setRecipients(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));
  const parseCsvLine = (line: string): string[] => { const cells: string[] = []; let current = ""; let quoted = false; for (let i = 0; i < line.length; i += 1) { const char = line[i]; if (char === '"') { if (quoted && line[i + 1] === '"') { current += '"'; i += 1; } else { quoted = !quoted; } } else if (char === "," && !quoted) { cells.push(current.trim()); current = ""; } else { current += char; } } cells.push(current.trim()); return cells; };
  const parseCsv = (text: string) => {
    const rows = text.split(/\r?\n/).filter(line => line.trim()); if (!rows.length) return;
    const headers = parseCsvLine(rows[0]).map(x => x.toLowerCase());
    const get = (parts: string[], keys: string[]) => { const index = headers.findIndex(h => keys.includes(h)); return index >= 0 ? (parts[index] || "").trim() : ""; };
    const parsed = rows.slice(1).map(parseCsvLine).map(parts => ({ name: get(parts, ["name", "full_name", "recipient_name"]), email: get(parts, ["email", "recipient_email"]), designation: get(parts, ["designation", "role"]), organization: get(parts, ["organization", "company"]) })).filter(r => r.name && r.email);
    if (!headers.some(h => ["name", "full_name", "recipient_name"].includes(h)) || !headers.some(h => ["email", "recipient_email"].includes(h))) return setError("CSV must contain name and email columns.");
    if (!parsed.length) return setError("No valid recipient rows were found in the CSV.");
    if (parsed.length > 5000) return setError("A single job can contain at most 5,000 recipients.");
    setError(""); setRecipients(parsed);
  };
  const downloadSampleCsv = () => { const content = ["name,email,designation,organization",'Aarav Sharma,aarav@example.com,Software Intern,Example Labs','Priya Singh,priya@example.com,Data Analyst,"Example, Inc."'].join("\n"); const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" })); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "certificate-recipients-example.csv"; anchor.click(); URL.revokeObjectURL(url); };
  const handleCsv = async (e: ChangeEvent<HTMLInputElement>) => { const file = e.target.files?.[0]; if (file) parseCsv(await file.text()); };
  const submit = async () => {
    setError(""); if (!certificate.event_name.trim() || !certificate.issuer_name.trim()) return setError("Event name and issuer are required.");
    const cleaned = recipients.filter(r => r.name.trim() || r.email.trim()).map(r => ({ ...r, name: r.name.trim(), email: r.email.trim().toLowerCase() }));
    if (!cleaned.length || cleaned.some(r => r.name.length < 2 || !r.email.includes("@"))) return setError("Every recipient must have a valid name and email.");
    if (new Set(cleaned.map(r => r.email)).size !== cleaned.length) return setError("Duplicate recipient emails are not allowed.");
    try { setSubmitting(true); const job = await createJob({ certificate, recipients: cleaned }); onCreated(job.id); } catch (e) { setError(e instanceof Error ? e.message : "Unable to create job"); } finally { setSubmitting(false); }
  };
  return <section className="page narrow"><button className="back" onClick={onBack}><ArrowLeft size={17}/> Back to dashboard</button><div className="section-heading"><p className="eyebrow">NEW GENERATION JOB</p><h1>Build a certificate run</h1><p className="lede">Set the fixed template metadata once, then submit all recipients in one request.</p></div>
    <div className="form-grid"><div className="card"><h2>Certificate details</h2><p className="muted">One predefined PDF design is used as required.</p><div className="form-cols"><label>Certificate title<input value={certificate.title} onChange={e => setCertificate({...certificate,title:e.target.value})}/></label><label>Issue date<input type="date" value={certificate.issue_date} onChange={e => setCertificate({...certificate,issue_date:e.target.value})}/></label><label>Event / course<input value={certificate.event_name} onChange={e => setCertificate({...certificate,event_name:e.target.value})} placeholder="FastAPI Backend Workshop"/></label><label>Issuer name<input value={certificate.issuer_name} onChange={e => setCertificate({...certificate,issuer_name:e.target.value})} placeholder="Aereo Engineering Team"/></label></div></div>
    <div className="card"><div className="card-head"><div><h2>Recipients</h2><p className="muted">{validCount} valid recipient{validCount === 1 ? "" : "s"} ready to process.</p></div><label className="upload-btn"><Upload size={16}/> Import CSV<input type="file" accept=".csv,text/csv" onChange={handleCsv}/></label></div>
      <div className="recipient-head"><span>Name</span><span>Email</span><span>Designation</span><span>Organization</span><span/></div>
      {recipients.map((r,i) => <div className="recipient-row" key={i}><input value={r.name} onChange={e=>updateRecipient(i,"name",e.target.value)} placeholder="Aarav Sharma"/><input value={r.email} onChange={e=>updateRecipient(i,"email",e.target.value)} placeholder="aarav@example.com"/><input value={r.designation || ""} onChange={e=>updateRecipient(i,"designation",e.target.value)} placeholder="Software Intern"/><input value={r.organization || ""} onChange={e=>updateRecipient(i,"organization",e.target.value)} placeholder="Example Labs"/><button className="icon-btn danger-icon" onClick={()=>setRecipients(prev=>prev.length===1?prev:prev.filter((_,idx)=>idx!==i))}><Trash2 size={16}/></button></div>)}
      <button className="add-row" onClick={()=>setRecipients([...recipients,emptyRecipient()])}><Plus size={16}/> Add recipient</button><div className="csv-tip"><FileUp size={17}/><div><strong>CSV supported</strong><p>Headers: name, email, designation, organization. Quoted CSV fields are supported.</p><button className="text-button" type="button" onClick={downloadSampleCsv}><Download size={14}/> Download sample</button></div></div>
    </div></div>
    {error && <div className="error-box">{error}</div>}<div className="submit-row"><span>One API request → one tracked generation job → individual certificate files.</span><button className="primary" disabled={submitting} onClick={submit}>{submitting ? "Creating job..." : "Generate certificates"}</button></div>
  </section>
}