import { useState, useEffect, useMemo } from "react"
import ComplaintCard from "../components/ComplaintCard"

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "in-progress", label: "In Progress" },
  { value: "resolved", label: "Resolved" },
]

const CATEGORY_OPTIONS = [
  { value: "", label: "All Categories" },
  { value: "road", label: "Road" },
  { value: "water", label: "Water" },
  { value: "sanitation", label: "Sanitation" },
  { value: "lighting", label: "Lighting" },
  { value: "public_safety", label: "Public Safety" },
  { value: "other", label: "Other" },
]

function buildUrl(statusFilter, categoryFilter) {
  const params = new URLSearchParams()
  if (statusFilter) params.set("status", statusFilter)
  if (categoryFilter) params.set("category", categoryFilter)
  const qs = params.toString()
  return `http://localhost:8000/complaints${qs ? "?" + qs : ""}`
}

export default function Dashboard() {
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")

  async function fetchComplaints() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(buildUrl(statusFilter, categoryFilter))
      if (!res.ok) throw new Error("Failed to fetch complaints.")
      const json = await res.json()
      setComplaints(json.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchComplaints()
  }, [statusFilter, categoryFilter])

  const sortedComplaints = useMemo(() => {
    return [...complaints].sort((a, b) => {
      const aResolved = a.status === "resolved"
      const bResolved = b.status === "resolved"

      // Keep active items first, and push resolved items to the end.
      if (aResolved !== bResolved) return aResolved ? 1 : -1

      const aPriority = Number(a.priority_score ?? 0)
      const bPriority = Number(b.priority_score ?? 0)
      return bPriority - aPriority
    })
  }, [complaints])

  const total = complaints.length
  const pending = complaints.filter((c) => c.status === "pending").length
  const inProgress = complaints.filter((c) => c.status === "in-progress").length
  const resolved = complaints.filter((c) => c.status === "resolved").length

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC]">
      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-8">
          <span className="inline-block text-[#4F46E5] text-xs font-semibold tracking-widest uppercase mb-3">
            Officer Portal
          </span>
          <h1 className="text-3xl font-black tracking-tight text-[#0F172A] mb-2">
            Priority Dashboard
          </h1>
          <p className="text-[#64748B] text-sm leading-relaxed">
            Complaints are sorted by AI-assigned priority score. Address the highest scores first.
          </p>
        </div>

        {/* Stat pills */}
        {!loading && !error && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            {[
              { label: "Total", value: total, color: "text-[#0F172A]" },
              { label: "Pending", value: pending, color: "text-[#64748B]" },
              { label: "In Progress", value: inProgress, color: "text-[#4F46E5]" },
              { label: "Resolved", value: resolved, color: "text-green-600" },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className="bg-white border border-[#E2E8F0] rounded-xl px-4 py-3 shadow-sm"
              >
                <p className="text-[#94A3B8] text-xs uppercase tracking-widest font-mono mb-1">
                  {label}
                </p>
                <p className={`text-2xl font-black font-mono ${color}`}>{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm text-[#0F172A] focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors cursor-pointer shadow-sm"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm text-[#0F172A] focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors cursor-pointer shadow-sm"
          >
            {CATEGORY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          <button
            onClick={fetchComplaints}
            className="ml-auto px-4 py-2 text-xs font-semibold rounded-lg bg-white text-[#64748B] hover:text-[#4F46E5] hover:border-[#4F46E5] transition-colors border border-[#E2E8F0] shadow-sm cursor-pointer"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-2 border-[#E2E8F0] border-t-[#4F46E5] rounded-full animate-spin" />
            <p className="text-[#94A3B8] text-sm font-mono">Fetching complaints…</p>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="p-5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm text-center">
            ⚠ {error}
            <button
              onClick={fetchComplaints}
              className="block mx-auto mt-3 text-xs underline opacity-70 hover:opacity-100 cursor-pointer"
            >
              Try again
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && sortedComplaints.length === 0 && (
          <div className="text-center py-24">
            <p className="text-4xl mb-3">📭</p>
            <p className="text-[#64748B] text-sm">No complaints match the current filters.</p>
          </div>
        )}

        {/* Complaint list */}
        {!loading && !error && sortedComplaints.length > 0 && (
          <div className="space-y-4">
            {sortedComplaints.map((complaint) => (
              <ComplaintCard
                key={complaint.id}
                complaint={complaint}
                onStatusUpdate={fetchComplaints}
              />
            ))}
          </div>
        )}

      </div>
    </div>
  )
}