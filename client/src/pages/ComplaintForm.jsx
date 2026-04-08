import { useState } from "react"

const CATEGORIES = [
  { value: "road", label: "Road & Infrastructure" },
  { value: "water", label: "Water Supply" },
  { value: "sanitation", label: "Sanitation & Sewage" },
  { value: "lighting", label: "Street Lighting" },
  { value: "public_safety", label: "Public Safety" },
  { value: "other", label: "Other" },
]

// Light-background severity styles — dark text on tinted surface
const SEVERITY_STYLES = {
  Critical: {
    banner: "bg-red-50 border-red-200 text-red-700",
    label:  "text-red-600",
    dot:    "bg-red-500",
  },
  High: {
    banner: "bg-orange-50 border-orange-200 text-orange-700",
    label:  "text-orange-600",
    dot:    "bg-orange-500",
  },
  Medium: {
    banner: "bg-amber-50 border-amber-200 text-amber-700",
    label:  "text-amber-600",
    dot:    "bg-amber-500",
  },
  Low: {
    banner: "bg-green-50 border-green-200 text-green-700",
    label:  "text-green-600",
    dot:    "bg-green-500",
  },
}

export default function ComplaintForm() {
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("")
  const [locationText, setLocationText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/complaints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description,
          category,
          location_text: locationText,
        }),
      })

      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.detail || "Something went wrong. Please try again.")
      }

      setResult(json.data)
      setDescription("")
      setCategory("")
      setLocationText("")
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const severity = result?.severity_label
  const sev = severity ? (SEVERITY_STYLES[severity] || SEVERITY_STYLES.Low) : null

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex items-start justify-center px-4 py-12">
      <div className="w-full max-w-xl">

        {/* Header */}
        <div className="mb-8">
          <span className="inline-block text-[#4F46E5] text-xs font-semibold tracking-widest uppercase mb-3">
            Citizen Portal
          </span>
          <h1 className="text-3xl font-black tracking-tight text-[#0F172A] mb-2">
            File a Complaint
          </h1>
          <p className="text-[#64748B] text-sm leading-relaxed">
            Describe your civic issue in detail. Our AI system will assess its
            severity and prioritise it for resolution.
          </p>
        </div>

        {/* Success Banner */}
        {result && sev && (
          <div className={`mb-6 p-5 rounded-xl border ${sev.banner} transition-all`}>
            <div className="flex items-center gap-2 mb-3">
              <div className={`w-2 h-2 rounded-full ${sev.dot}`} />
              <span className="font-semibold text-sm">Your complaint has been noted. Our team will look into it shortly.</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs font-medium opacity-60 uppercase tracking-wide mb-1">Severity</p>
                <p className={`text-xl font-black ${sev.label}`}>{result.severity_label}</p>
              </div>
              <div>
                <p className="text-xs font-medium opacity-60 uppercase tracking-wide mb-1">Priority Score</p>
                <p className="text-xl font-black text-[#0F172A]">
                  {result.priority_score?.toFixed(2)}
                  <span className="text-sm font-normal text-[#64748B]"> / 100</span>
                </p>
              </div>
            </div>
            <p className="text-xs opacity-50 mt-3 font-mono">
              ID: {result.id?.slice(0, 8)}…
            </p>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
            ⚠ {error}
          </div>
        )}

        {/* Form Card */}
        <div className="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm p-6 space-y-5">

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] uppercase tracking-widest mb-2">
              Complaint Description <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={6}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the civic issue in detail — location, duration, impact on residents…"
              className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-3 text-[#0F172A] placeholder-[#CBD5E1] text-sm resize-none focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors"
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] uppercase tracking-widest mb-2">
              Category <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-3 text-sm text-[#0F172A] focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors appearance-none cursor-pointer"
              style={{ color: category ? "#0F172A" : "#CBD5E1" }}
            >
              <option value="" disabled>Select a category…</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] uppercase tracking-widest mb-2">
              Location <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={locationText}
              onChange={(e) => setLocationText(e.target.value)}
              placeholder="e.g. MG Road, near Metro Station, Delhi"
              className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-3 text-[#0F172A] placeholder-[#CBD5E1] text-sm focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            onClick={handleSubmit}
            className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-[#E2E8F0] disabled:text-[#94A3B8] text-white font-bold py-3.5 rounded-lg text-sm transition-all duration-200 tracking-wide cursor-pointer"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Submitting…
              </span>
            ) : (
              "Submit Complaint →"
            )}
          </button>

        </div>

        {/* Footer note */}
        <p className="text-center text-[#94A3B8] text-xs mt-6">
          Complaints are processed instantly by CitySync AI and routed to officers by priority.
        </p>

      </div>
    </div>
  )
}