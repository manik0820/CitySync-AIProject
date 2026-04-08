import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Navbar from "./components/Navbar"
import ComplaintForm from "./pages/ComplaintForm"
import Dashboard from "./pages/Dashboard"
import Login from "./pages/Login"

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token")
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/submit" />} />
          <Route path="/submit" element={<ComplaintForm />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
        </Routes>
      </div>
    </BrowserRouter>
  )
}