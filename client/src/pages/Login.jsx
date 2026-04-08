import { useState } from "react"
import { useNavigate } from "react-router-dom"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  async function handleLogin(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.detail || "Login failed. Please try again.")
      }

      // Store token and officer info
      localStorage.setItem("token", json.token)
      localStorage.setItem("officer", JSON.stringify(json.officer))

      navigate("/dashboard")
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#4F46E5] mb-4">
            <span className="text-white font-black text-lg">CS</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-[#0F172A] mb-1">
            Officer Login
          </h1>
          <p className="text-[#64748B] text-sm">
            Sign in to access the priority dashboard.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
            ⚠ {error}
          </div>
        )}

        {/* Form Card */}
        <div className="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">

          <div>
            <label className="block text-xs font-semibold text-[#0F172A] uppercase tracking-widest mb-2">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="officer@citysync.in"
              className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-3 text-[#0F172A] placeholder-[#CBD5E1] text-sm focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#0F172A] uppercase tracking-widest mb-2">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-3 text-[#0F172A] placeholder-[#CBD5E1] text-sm focus:outline-none focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/10 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            onClick={handleLogin}
            className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-[#E2E8F0] disabled:text-[#94A3B8] text-white font-bold py-3.5 rounded-lg text-sm transition-all duration-200 tracking-wide cursor-pointer"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Signing in…
              </span>
            ) : (
              "Sign In →"
            )}
          </button>

        </div>

        <p className="text-center text-[#94A3B8] text-xs mt-6">
          Access restricted to authorised officers only.
        </p>

      </div>
    </div>
  )
}