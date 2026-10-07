export function StatusBadge({ status }: { status: string }) {
  const label = status.replace(/_/g, " ");
  const tone = status.includes("error") || status === "failed" ? "danger" : status === "completed" ? "success" : status === "processing" ? "info" : "neutral";
  return <span className={"badge badge-" + tone}><span className="dot" />{label}</span>;
}