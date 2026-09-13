import { useEffect, useState } from 'react'
import { Bell, Plus, Trash2, CheckCircle, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ symbol: 'BTC-USD', type: 'PRICE_ABOVE', target_price: 115000 })

  const safeFixed = (v, d=2) => {
    if (v == null) return 'N/A'
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return 'N/A'
    return n.toFixed(d)
  }

  const fetchData = async () => {
    try {
      const data = await api.getAlerts().catch(() => fetch('/api/alerts').then(r => r.json()))
      setAlerts(data.alerts || [])
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i) }, [])

  const createAlert = async () => {
    try {
      const payload = { symbol: form.symbol, type: form.type, target_price: form.target_price ? parseFloat(form.target_price) : null }
      const data = await api.createAlert(payload).catch(() => fetch('/api/alerts/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(r=>r.json()))
      setShowCreate(false); fetchData()
    } catch (e) { alert(e.message) }
  }

  const deleteAlert = async (id) => {
    try {
      await api.cancelAlert(id).catch(() => fetch(`/api/alerts/${id}`, { method: 'DELETE' }))
      fetchData()
    } catch (e) { console.error(e) }
  }

  const checkAlerts = async () => {
    try {
      const data = await api.checkAlerts().catch(() => fetch('/api/alerts/check').then(r=>r.json()))
      if (data.triggered?.length > 0) alert(`${data.triggered.length} alerts triggered!`)
      fetchData()
    } catch (e) { console.error(e) }
  }

  if (loading) return <div className="p-6 text-center">Loading real alerts...</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3"><Bell className="text-amber-400" /> Alerts - Real Market Monitoring</h1>
          <p className="text-crypto-muted mt-1">Price alerts, signal alerts - real Binance monitoring for actual trades</p>
        </div>
        <div className="flex gap-2">
          <button onClick={checkAlerts} className="px-4 py-2 rounded-xl bg-crypto-card border border-crypto-border hover:border-crypto-borderLight">Check Now</button>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 rounded-xl bg-amber-500 text-black font-bold flex items-center gap-2"><Plus size={16} /> Create Alert</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Total Alerts</div>
          <div className="text-2xl font-black">{alerts.length}</div>
        </div>
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Active</div>
          <div className="text-2xl font-black text-emerald-400">{alerts.filter(a => a.status === 'ACTIVE').length}</div>
        </div>
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Triggered</div>
          <div className="text-2xl font-black text-amber-400">{alerts.filter(a => a.status === 'TRIGGERED').length}</div>
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
        <h3 className="font-bold mb-4">All Alerts - Real Market</h3>
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-crypto-muted">No alerts - create one for real market monitoring</div>
        ) : (
          <div className="space-y-3">
            {alerts.slice().reverse().map(alert => (
              <div key={alert.id} className={`p-4 rounded-xl border flex items-center justify-between ${alert.status === 'TRIGGERED' ? 'bg-amber-500/5 border-amber-500/20' : alert.status === 'ACTIVE' ? 'bg-crypto-bg border-crypto-border/50' : 'bg-crypto-bg/50 border-crypto-border/20 opacity-60'}`}>
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${alert.status === 'TRIGGERED' ? 'bg-amber-500/10 text-amber-400' : alert.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-crypto-card text-crypto-muted'}`}>
                    {alert.status === 'TRIGGERED' ? <AlertTriangle size={18} /> : alert.status === 'ACTIVE' ? <Bell size={18} /> : <CheckCircle size={18} />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold">{alert.symbol || 'Unknown'}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${alert.type?.includes('ABOVE') ? 'bg-emerald-500/10 text-emerald-400' : alert.type?.includes('BELOW') ? 'bg-red-500/10 text-red-400' : 'bg-violet-500/10 text-violet-400'}`}>{alert.type || 'UNKNOWN'}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${alert.status === 'ACTIVE' ? 'bg-emerald-500 text-black' : alert.status === 'TRIGGERED' ? 'bg-amber-500 text-black' : 'bg-crypto-card text-crypto-muted'}`}>{alert.status || 'UNKNOWN'}</span>
                    </div>
                    <div className="text-xs text-crypto-muted mt-1">
                      {alert.message || 'No message'} • 
                      Target: {alert.target_price != null ? `$${safeFixed(alert.target_price,2)}` : 'N/A'} • 
                      Current: {alert.current_price != null ? `$${safeFixed(alert.current_price,2)}` : 'N/A'}
                    </div>
                    <div className="text-[10px] text-crypto-muted mt-0.5">Created: {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Unknown'} {alert.triggered_at ? `• Triggered: ${new Date(alert.triggered_at).toLocaleString()}` : ''}</div>
                  </div>
                </div>
                <button onClick={() => deleteAlert(alert.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-crypto-muted hover:text-red-400"><Trash2 size={16} /></button>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4">
          <div className="p-6 rounded-2xl bg-crypto-card border border-crypto-border w-full max-w-md">
            <h3 className="font-bold text-lg mb-4">Create Real Alert - Live Monitoring</h3>
            <div className="space-y-4">
              <select value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                <option value="PRICE_ABOVE">Price Above</option>
                <option value="PRICE_BELOW">Price Below</option>
                <option value="SIGNAL_BUY">Signal Buy</option>
                <option value="SIGNAL_SELL">Signal Sell</option>
                <option value="VOLUME_SPIKE">Volume Spike</option>
                <option value="RISK_HIGH">High Risk</option>
              </select>
              <input type="number" placeholder="Target Price (optional for signal alerts)" value={form.target_price} onChange={e => setForm({ ...form, target_price: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border" />
              <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs">
                <div className="font-bold text-amber-400">Real Market Alert</div>
                <div className="text-crypto-muted mt-1">Monitors live Binance price - triggers when condition met for real trading</div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowCreate(false)} className="flex-1 py-2 rounded-xl bg-crypto-bg border border-crypto-border">Cancel</button>
                <button onClick={createAlert} className="flex-1 py-2 rounded-xl bg-amber-500 text-black font-bold">Create Real Alert</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
