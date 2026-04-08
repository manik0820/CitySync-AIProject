import { useState } from "react"

const SEVERITY_STYLES = {
  Critical: {
    badge: "bg-red-100 text-red-700 border border-red-200",
    border: "border-l-red-500",
    score: "text-red-600",
  },
  High: {
    badge: "bg-orange-100 text-orange-700 border border-orange-200",
    border: "border-l-orange-500",
    score: "text-orange-600",
  },
  Medium: {
    badge: "bg-amber-100 text-amber-700 border border-amber-200",
    border: "border-l-amber-500",
    score: "text-amber-600",
  },
  Low: {
    badge: "bg-green-100 text-green-700 border border-green-200",
    border: "border-l-green-500",
    score: "text-green-600",
  },
}

const STATUS_STYLES = {
  pending: "bg-slate-100 text-slate-600 border border-slate-200",
  "in-progress": "bg-indigo-100 text-indigo-700 border border-indigo-200",
  resolved: "bg-green-100 text-green-700 border border-green-200",
}

const STATUS_LABELS = {
  pending: "Pending",
  "in-progress": "In Progress",
  resolved: "Resolved",
}

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function truncate(text, max = 110) {
  if (!text) return ""
  return text.length > max ? text.slice(0, max).trim() + "…" : text
}

export default function ComplaintCard({ complaint, onStatusUpdate }) {
  const [loading, setLoading] = useState(null)

  const severity = complaint.severity_label || "Low"
  const styles = SEVERITY_STYLES[severity] || SEVERITY_STYLES.Low
  const isResolved = complaint.status === "resolved"

  async function handleStatusUpdate(newStatus) {
    setLoading(newStatus)
    try {
      const res = await fetch(
        `http://localhost:8000/complaints/${complaint.id}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        }
      )
      if (!res.ok) throw new Error("Update failed")
      await onStatusUpdate()
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div
      className={`
        bg-white border border-[#E2E8F0] border-l-4 ${styles.border}
        rounded-xl p-5 shadow-sm transition-all duration-300
        ${isResolved ? "opacity-50" : "hover:shadow-md hover:border-[#CBD5E1]"}
      `}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-baseline gap-1">
          <span className={`text-3xl font-black font-mono ${styles.score}`}>
            {complaint.priority_score?.toFixed(1) ?? "—"}
          </span>
          <span className="text-[#94A3B8] text-xs font-mono">/ 100</span>
        </div>

        <div className="flex flex-wrap gap-2 justify-end">
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${styles.badge}`}>
            {severity}
          </span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLES[complaint.status] || STATUS_STYLES.pending}`}>
            {STATUS_LABELS[complaint.status] || complaint.status}
          </span>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#F1F5F9] text-[#64748B] uppercase tracking-wide border border-[#E2E8F0]">
            {complaint.category}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-[#0F172A] text-sm leading-relaxed mb-3">
        {truncate(complaint.description)}
      </p>

      {/* Meta row */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#94A3B8] mb-4">
        <span>📍 {complaint.location_text}</span>
        <span>🕐 {formatDate(complaint.created_at)}</span>
        <span>⚡ Urgency: {(complaint.urgency_score * 100).toFixed(0)}%</span>
        <span className="font-mono">ID: {complaint.id?.slice(0, 8)}…</span>
      </div>

      {/* Actions */}
      {!isResolved && (
        <div className="flex gap-2 flex-wrap">
          {complaint.status !== "in-progress" && (
            <button
              onClick={() => handleStatusUpdate("in-progress")}
              disabled={!!loading}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading === "in-progress" ? "Updating…" : "Mark In Progress"}
            </button>
          )}
          <button
            onClick={() => handleStatusUpdate("resolved")}
            disabled={!!loading}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {loading === "resolved" ? "Updating…" : "Mark Resolved"}
          </button>
        </div>
      )}

      {isResolved && (
        <p className="text-xs text-[#94A3B8] italic">This complaint has been resolved.</p>
      )}
    </div>
  )
}