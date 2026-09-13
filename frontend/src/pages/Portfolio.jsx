import { useEffect, useState } from 'react'
import { Wallet, TrendingUp, TrendingDown, PieChart, BarChart3, X, Plus } from 'lucide-react'

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null)
  const [perf, setPerf] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showOpen, setShowOpen] = useState(false)
  const [form, setForm] = useState({ symbol: 'BTC-USD', side: 'LONG', quantity: 0.01, entry_price: '' })

  const fetchData = async () => {
    try {
      const [pRes, perfRes] = await Promise.all([
        fetch('/api/portfolio').then(r => r.json()),
        fetch('/api/portfolio/performance').then(r => r.json())
      ])
      setPortfolio(pRes)
      setPerf(perfRes)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i) }, [])

  const openPos = async () => {
    try {
      const res = await fetch('/api/portfolio/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, entry_price: form.entry_price ? parseFloat(form.entry_price) : null, quantity: parseFloat(form.quantity) })
      })
      const data = await res.json()
      if (res.ok) {
        setShowOpen(false)
        fetchData()
      } else {
        alert(data.detail || 'Failed')
      }
    } catch (e) { alert(e.message) }
  }

  const closePos = async (symbol) => {
    if (!confirm(`Close REAL position for ${symbol}?`)) return
    try {
      const res = await fetch(`/api/portfolio/close/${symbol}`, { method: 'POST' })
      const data = await res.json()
      if (res.ok) fetchData()
      else alert(data.detail)
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center">Loading real portfolio...</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3">
            <Wallet className="text-emerald-400" /> Real Portfolio
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-bold">LIVE BINANCE</span>
          </h1>
          <p className="text-crypto-muted mt-1">Real holdings tracking - live Binance prices - no fake simulation</p>
        </div>
        <button onClick={() => setShowOpen(true)} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold flex items-center gap-2 hover:bg-emerald-400">
          <Plus size={16} /> Open Position
        </button>
      </div>

      {/* Summary Cards */}
      {portfolio && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Total Value</div>
            <div className="text-2xl font-black mt-1">${portfolio.total_value?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            <div className={`text-sm mt-1 flex items-center gap-1 ${portfolio.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {portfolio.total_pnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} ${portfolio.total_pnl?.toFixed(2)} ({portfolio.total_pnl_pct?.toFixed(2)}%)
            </div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Cash</div>
            <div className="text-2xl font-black mt-1">${portfolio.cash?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            <div className="text-xs text-crypto-muted mt-1">{((portfolio.cash / portfolio.total_value) * 100).toFixed(1)}% of portfolio</div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Positions Value</div>
            <div className="text-2xl font-black mt-1">${portfolio.positions_value?.toFixed(2)}</div>
            <div className="text-xs text-crypto-muted mt-1">{portfolio.count} open positions</div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Real Trading</div>
            <div className="text-lg font-bold mt-1 text-emerald-400">No Fake Simulation</div>
            <div className="text-xs text-crypto-muted mt-1">Live Binance prices, real P&L</div>
          </div>
        </div>
      )}

      {/* Performance */}
      {perf && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Total Trades</div>
            <div className="text-xl font-bold">{perf.total_trades}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Win Rate</div>
            <div className="text-xl font-bold text-emerald-400">{perf.win_rate?.toFixed(1)}%</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Profit Factor</div>
            <div className="text-xl font-bold">{perf.profit_factor?.toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Best Trade</div>
            <div className="text-xl font-bold text-emerald-400">${perf.best_trade?.toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Worst Trade</div>
            <div className="text-xl font-bold text-red-400">${perf.worst_trade?.toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Profit</div>
            <div className={`text-xl font-bold ${perf.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${perf.total_pnl?.toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Allocation */}
      {portfolio?.allocation && (
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold flex items-center gap-2 mb-4"><PieChart size={16} /> Allocation - Real Holdings</h3>
          <div className="space-y-2">
            {Object.entries(portfolio.allocation).map(([sym, pct]) => (
              <div key={sym} className="flex items-center gap-3">
                <div className="w-20 text-sm font-medium">{sym}</div>
                <div className="flex-1 h-2 bg-crypto-bg rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-emerald-500 to-violet-500" style={{ width: `${pct}%` }}></div>
                </div>
                <div className="w-12 text-xs text-crypto-muted">{pct.toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Positions */}
      <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
        <h3 className="font-bold flex items-center gap-2 mb-4"><BarChart3 size={16} /> Open Positions - Live Binance Prices</h3>
        {portfolio?.positions?.length === 0 ? (
          <div className="text-center py-8 text-crypto-muted">No open positions - open one to track real trading</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-crypto-muted uppercase">
                <tr><th className="text-left py-2">Symbol</th><th>Side</th><th>Entry</th><th>Qty</th><th>SL</th><th>TP</th><th>Lev</th><th>Action</th></tr>
              </thead>
              <tbody>
                {portfolio?.positions?.map((p, i) => (
                  <tr key={i} className="border-t border-crypto-border/30">
                    <td className="py-3 font-bold">{p.symbol}</td>
                    <td><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${p.side === 'LONG' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{p.side}</span></td>
                    <td>${p.entry_price?.toLocaleString()}</td>
                    <td>{p.quantity}</td>
                    <td className="text-red-400">${p.stop_loss?.toLocaleString()}</td>
                    <td className="text-emerald-400">${p.take_profits?.tp1?.toLocaleString()}</td>
                    <td>{p.leverage}</td>
                    <td><button onClick={() => closePos(p.symbol)} className="px-3 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs">Close</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Closed */}
      {portfolio?.closed_positions?.length > 0 && (
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold mb-4">Closed Positions - Real P&L History</h3>
          <div className="space-y-2 max-h-[300px] overflow-auto">
            {portfolio.closed_positions.slice(-20).reverse().map((p, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
                <div className="flex items-center gap-3">
                  <span className="font-bold">{p.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${p.side === 'LONG' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{p.side}</span>
                  <span className="text-xs text-crypto-muted">{p.quantity} @ ${p.entry_price?.toFixed(2)}</span>
                </div>
                <div className={`font-bold ${p.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${p.pnl?.toFixed(2)} ({p.pnl_pct?.toFixed(2)}%)</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Open Modal */}
      {showOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur">
          <div className="p-6 rounded-2xl bg-crypto-card border border-crypto-border w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">Open Real Position</h3>
              <button onClick={() => setShowOpen(false)} className="p-2 rounded-lg hover:bg-crypto-bg"><X size={16} /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-crypto-muted">Symbol</label>
                <select value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                  {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD'].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-crypto-muted">Side</label>
                  <select value={form.side} onChange={e => setForm({ ...form, side: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                    <option value="LONG">LONG</option>
                    <option value="SHORT">SHORT</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-crypto-muted">Quantity</label>
                  <input type="number" step="0.0001" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border" />
                </div>
              </div>
              <div>
                <label className="text-xs text-crypto-muted">Entry Price (leave empty for live Binance price)</label>
                <input type="number" value={form.entry_price} onChange={e => setForm({ ...form, entry_price: e.target.value })} placeholder="Live price" className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-xs">
                <div className="font-bold text-emerald-400">Real Trading - No Fake</div>
                <div className="text-crypto-muted mt-1">This tracks real position with live Binance price, SL/TP from AI call. Use proper risk management.</div>
              </div>
              <button onClick={openPos} className="w-full py-3 rounded-xl bg-emerald-500 text-black font-bold hover:bg-emerald-400">Open Real Position</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
