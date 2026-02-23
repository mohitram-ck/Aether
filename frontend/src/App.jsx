import { useState, useEffect } from "react"
import axios from "axios"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const api = axios.create({ baseURL: "http://127.0.0.1:8000" })

function getToken() { return localStorage.getItem("token") }
function saveToken(t) { localStorage.setItem("token", t) }
function clearToken() { localStorage.removeItem("token") }
function authHeaders() { return { headers: { Authorization: `Bearer ${getToken()}` } } }

export default function App() {
  const [token, setToken] = useState(getToken())
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [mode, setMode] = useState("login")
  const [msg, setMsg] = useState("")
  const [transactions, setTransactions] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [queueLen, setQueueLen] = useState(0)
  const [amount, setAmount] = useState("")
  const [merchant, setMerchant] = useState("")
  const [location, setLocation] = useState("")
  const [currency, setCurrency] = useState("USD")

  useEffect(() => {
    if (!token) return
    async function loadAll() {
      try {
        const [t, a, q] = await Promise.all([
          api.get("/transactions/", authHeaders()),
          api.get("/analytics/forecast", authHeaders()),
          api.get("/transactions/stream/length", authHeaders())
        ])
        setTransactions(t.data)
        setAnalytics(a.data)
        setQueueLen(q.data.transactions_in_queue)
      } catch { /* empty */ }
    }
    loadAll()
  }, [token])

  async function handleAuth() {
    setMsg("")
    try {
      if (mode === "register") {
        await api.post("/auth/register", { email, password, role: "user" })
        setMsg("Registered! Now login.")
        setMode("login")
        return
      }
      const res = await api.post("/auth/login", { email, password })
      saveToken(res.data.access_token)
      setToken(res.data.access_token)
    } catch (e) {
      setMsg(e.response?.data?.detail || "Error")
    }
  }

  async function handleLogout() {
    try { await api.post("/auth/logout", {}, authHeaders()) } catch { /* empty */ }
    clearToken()
    setToken(null)
  }

  async function loadTransactions() {
    try {
      const res = await api.get("/transactions/", authHeaders())
      setTransactions(res.data)
    } catch { /* empty */ }
  }

  async function loadAnalytics() {
    try {
      const res = await api.get("/analytics/forecast", authHeaders())
      setAnalytics(res.data)
    } catch { /* empty */ }
  }

  async function loadQueue() {
    try {
      const res = await api.get("/transactions/stream/length", authHeaders())
      setQueueLen(res.data.transactions_in_queue)
    } catch { /* empty */ }
  }

  async function submitTransaction() {
    try {
      await api.post("/transactions/", {
        amount: parseFloat(amount),
        currency,
        merchant,
        location
      }, authHeaders())
      setAmount("")
      setMerchant("")
      setLocation("")
      loadTransactions()
      loadAnalytics()
      loadQueue()
    } catch (e) {
      alert(e.response?.data?.detail || "Failed")
    }
  }

  const chartData = analytics?.forecast_next_10_minutes?.map((v, i) => ({
    name: `+${i + 1}m`,
    txns: v
  })) || []

  if (!token) {
    return (
      <div style={{ minHeight: "100vh", background: "#0f0f1a", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ background: "#1e1e2e", padding: 40, borderRadius: 12, width: 340, display: "flex", flexDirection: "column", gap: 12 }}>
          <h1 style={{ color: "#7c3aed", margin: 0 }}>⚡ Aether</h1>
          <p style={{ color: "#aaa", margin: 0, fontSize: 13 }}>High-Frequency Transaction Engine</p>
          <h3 style={{ color: "#fff", margin: "8px 0 0" }}>{mode === "login" ? "Login" : "Register"}</h3>
          {msg && <p style={{ color: "#f59e0b", fontSize: 13 }}>{msg}</p>}
          <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={inp} />
          <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} style={inp} />
          <button onClick={handleAuth} style={btn}>{mode === "login" ? "Login" : "Register"}</button>
          <p style={{ color: "#aaa", fontSize: 13, textAlign: "center" }}>
            {mode === "login" ? "No account? " : "Have account? "}
            <span style={{ color: "#7c3aed", cursor: "pointer" }} onClick={() => setMode(mode === "login" ? "register" : "login")}>
              {mode === "login" ? "Register" : "Login"}
            </span>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: "100vh", background: "#0f0f1a", color: "#fff", fontFamily: "sans-serif" }}>
      <div style={{ background: "#1e1e2e", padding: "16px 32px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #333" }}>
        <h2 style={{ color: "#7c3aed", margin: 0 }}>⚡ Aether</h2>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ background: "#7c3aed22", color: "#7c3aed", padding: "4px 12px", borderRadius: 20, fontSize: 13 }}>Queue: {queueLen}</span>
          <button onClick={handleLogout} style={{ background: "transparent", color: "#ff4d4d", border: "1px solid #ff4d4d", borderRadius: 8, padding: "6px 14px", cursor: "pointer" }}>Logout</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, padding: 32 }}>
        <div style={card}>
          <h3 style={{ margin: "0 0 16px", color: "#fff" }}>Submit Transaction</h3>
          <input placeholder="Amount" type="number" value={amount} onChange={e => setAmount(e.target.value)} style={inp} />
          <input placeholder="Merchant" value={merchant} onChange={e => setMerchant(e.target.value)} style={{ ...inp, marginTop: 10 }} />
          <input placeholder="Location" value={location} onChange={e => setLocation(e.target.value)} style={{ ...inp, marginTop: 10 }} />
          <select value={currency} onChange={e => setCurrency(e.target.value)} style={{ ...inp, marginTop: 10 }}>
            <option>USD</option>
            <option>EUR</option>
            <option>GBP</option>
            <option>INR</option>
          </select>
          <button onClick={submitTransaction} style={{ ...btn, marginTop: 14 }}>Submit</button>
        </div>

        <div style={card}>
          <h3 style={{ margin: "0 0 16px", color: "#fff" }}>Fraud Analysis</h3>
          {!analytics && <p style={{ color: "#666" }}>Loading...</p>}
          {analytics?.status === "insufficient_data" && <p style={{ color: "#666" }}>Submit more transactions to see analysis</p>}
          {analytics?.status === "ok" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Row label="Fraud Risk" value={analytics.fraud_risk_detected ? "⚠️ DETECTED" : "✅ CLEAR"} color={analytics.fraud_risk_detected ? "#ff4d4d" : "#4caf50"} />
              <Row label="Data Points" value={analytics.data_points_analyzed} />
              <Row label="Velocity Anomaly" value={analytics.velocity_anomaly?.is_anomaly ? "⚠️ Yes" : "✅ No"} />
              <Row label="Amount Anomaly" value={analytics.amount_anomaly?.is_anomaly ? "⚠️ Yes" : "✅ No"} />
            </div>
          )}
        </div>
      </div>

      {chartData.length > 0 && (
        <div style={{ ...card, margin: "0 32px 24px" }}>
          <h3 style={{ margin: "0 0 16px", color: "#fff" }}>Load Forecast — Next 10 Minutes</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip contentStyle={{ background: "#1e1e2e", border: "1px solid #444" }} />
              <Line type="monotone" dataKey="txns" stroke="#7c3aed" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div style={{ ...card, margin: "0 32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ margin: 0, color: "#fff" }}>Transaction History</h3>
          <button onClick={loadTransactions} style={{ background: "#2a2a3e", color: "#fff", border: "1px solid #444", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: 13 }}>Refresh</button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr>
              {["Merchant", "Amount", "Currency", "Location", "Status", "Flagged", "Time"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "8px 12px", color: "#888", borderBottom: "1px solid #333" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transactions.map(t => (
              <tr key={t.id}>
                <td style={td}>{t.merchant}</td>
                <td style={td}>{t.amount}</td>
                <td style={td}>{t.currency}</td>
                <td style={td}>{t.location || "—"}</td>
                <td style={td}><span style={{ color: t.status === "processed" ? "#4caf50" : "#f59e0b" }}>{t.status}</span></td>
                <td style={td}>{t.is_flagged ? "⚠️ Yes" : "✅ No"}</td>
                <td style={td}>{new Date(t.created_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {transactions.length === 0 && <p style={{ color: "#666", marginTop: 16, fontSize: 13 }}>No transactions yet</p>}
      </div>
    </div>
  )
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #2a2a3e", fontSize: 14, color: "#ccc" }}>
      <span>{label}</span>
      <span style={{ color: color || "#fff", fontWeight: "bold" }}>{value}</span>
    </div>
  )
}

const inp = { padding: "10px 12px", borderRadius: 8, border: "1px solid #333", background: "#2a2a3e", color: "#fff", fontSize: 14, width: "100%", boxSizing: "border-box" }
const btn = { padding: 11, background: "#7c3aed", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold", fontSize: 14, width: "100%" }
const card = { background: "#1e1e2e", borderRadius: 12, padding: 24, border: "1px solid #333" }
const td = { padding: "10px 12px", borderBottom: "1px solid #1a1a2e", color: "#ccc" }