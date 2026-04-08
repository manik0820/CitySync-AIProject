import { Link, useLocation } from "react-router-dom"

export default function Navbar() {
  const { pathname } = useLocation()
  const token = localStorage.getItem("token")

  const links = [
  { to: "/submit", label: "File Complaint" },
  ...(token
    ? [{ to: "/dashboard", label: "Officer Dashboard" }]
    : [{ to: "/login", label: "Officer Login" }]
  ),
]

  return (
    <nav style={{
      backgroundColor: "#0F172A",
      borderBottom: "3px solid #4F46E5",
      padding: "0 2rem",
      height: "64px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      {/* Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{
          width: "32px", height: "32px",
          backgroundColor: "#4F46E5",
          borderRadius: "8px",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontWeight: "800", color: "white", fontSize: "14px",
        }}>
          CS
        </div>
        <span style={{
          color: "white",
          fontWeight: "700",
          fontSize: "18px",
          letterSpacing: "-0.3px",
        }}>
          CitySync
        </span>
      </div>

      {/* Links + Logout */}
      <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
        {links.map(({ to, label }) => {
          const active = pathname === to
          return (
            <Link key={to} to={to} style={{
              textDecoration: "none",
              padding: "8px 16px",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: active ? "600" : "400",
              color: active ? "white" : "#94A3B8",
              backgroundColor: active ? "#4F46E5" : "transparent",
              transition: "all 0.15s ease",
            }}
              onMouseEnter={e => { if (!active) e.target.style.color = "white" }}
              onMouseLeave={e => { if (!active) e.target.style.color = "#94A3B8" }}
            >
              {label}
            </Link>
          )
        })}

        {token && (
          <button
            onClick={() => {
              localStorage.removeItem("token")
              localStorage.removeItem("officer")
              window.location.href = "/login"
            }}
            style={{
              marginLeft: "8px",
              padding: "8px 16px",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: "500",
              color: "#94A3B8",
              background: "transparent",
              border: "none",
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        )}
      </div>
    </nav>
  )
}