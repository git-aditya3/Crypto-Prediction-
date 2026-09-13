import { useEffect, useState } from 'react'
import { Wallet, TrendingUp, TrendingDown, PieChart, BarChart3, X, Plus } from 'lucide-react'
import { api } from '../api/client'

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null)
  const [perf, setPerf] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showOpen, setShowOpen] = useState(false)
  const [form, setForm] = useState({ symbol: 'BTC-USD', side: 'LONG', quantity: 0.01, entry_price: '' })

  const fetchData = async () => {
    try {
      const [pRes, perfRes] = await Promise.all([
        api.getPortfolio().catch(() => null),
        api.getPortfolioPerformance().catch(() => null)
      ])
      // Fallback to fetch if api fails
      if (!pRes) {
        const r = await fetch('/api/portfolio')
        if (r.ok) {
          const data = await r.json()
          setPortfolio(data)
        }
      } else {
        setPortfolio(pRes)
      }
      if (perfRes) setPerf(perfRes)
      else {
        const r = await fetch('/api/portfolio/performance')
        if (r.ok) setPerf(await r.json())
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i) }, [])

  const openPos = async () => {
    try {
      const qty = parseFloat(form.quantity)
      if (!qty || qty <= 0) {
        alert('Quantity must be > 0')
        return
      }
      const payload = { 
        symbol: form.symbol, 
        side: form.side, 
        quantity: qty,
        entry_price: form.entry_price ? parseFloat(form.entry_price) : null
      }
      // Try api client first
      try {
        const data = await api.openPosition(payload)
        setShowOpen(false)
        fetchData()
      } catch (apiErr) {
        const res = await fetch('/api/portfolio/open', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const data = await res.json()
        if (res.ok) {
          setShowOpen(false)
          fetchData()
        } else {
          alert(data.detail || data.message || 'Failed to open position')
        }
      }
    } catch (e) { alert(e.message) }
  }

  const closePos = async (symbol) => {
    if (!confirm(`Close REAL position for ${symbol}? This will use actual CoinDCX market price.`)) return
    try {
      try {
        await api.closePosition(symbol)
        fetchData()
      } catch {
        const res = await fetch(`/api/portfolio/close/${symbol}`, { method: 'POST' })
        const data = await res.json()
        if (res.ok) fetchData()
        else alert(data.detail || 'Failed to close')
      }
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center">Loading real portfolio - CoinDCX actual money...</div>

  const totalValue = portfolio?.total_value || 0
  const cash = portfolio?.cash || 0
  const positionsValue = portfolio?.positions_value || 0
  const totalPnl = portfolio?.total_pnl || 0
  const totalPnlPct = portfolio?.total_pnl_pct || 0
  const openPositions = portfolio?.positions || []
  const allocation = portfolio?.allocation || {}
  // Closed positions are not in Portfolio dataclass, get from perf or portfolio.closed_positions if backend provides
  const closedPositions = portfolio?.closed_positions || perf?.closed_positions || []

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3">
            <Wallet className="text-emerald-400" /> Real Portfolio - CoinDCX
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-bold">COINDCX REAL MONEY</span>
            <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-bold">ACTUAL INR</span>
          </h1>
          <p className="text-crypto-muted mt-1">Real holdings tracking - CoinDCX actual INR and crypto - no paper simulation - real P&L</p>
        </div>
        <button onClick={() => setShowOpen(true)} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold flex items-center gap-2 hover:bg-emerald-400">
          <Plus size={16} /> Open Real Position
        </button>
      </div>

      {/* Summary Cards */}
      {portfolio && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Total Value - Real Money</div>
            <div className="text-2xl font-black mt-1">${totalValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            <div className={`text-sm mt-1 flex items-center gap-1 ${totalPnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {totalPnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} ${totalPnl.toFixed(2)} ({totalPnlPct.toFixed(2)}%)
            </div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Cash - Real INR</div>
            <div className="text-2xl font-black mt-1">${cash.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            <div className="text-xs text-crypto-muted mt-1">{totalValue > 0 ? ((cash / totalValue) * 100).toFixed(1) : 0}% of portfolio</div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">Positions Value - Real</div>
            <div className="text-2xl font-black mt-1">${positionsValue.toFixed(2)}</div>
            <div className="text-xs text-crypto-muted mt-1">{openPositions.length} open positions - actual trades</div>
          </div>
          <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
            <div className="text-xs text-crypto-muted uppercase tracking-widest">CoinDCX Real Money</div>
            <div className="text-lg font-bold mt-1 text-emerald-400">No Paper Simulation</div>
            <div className="text-xs text-crypto-muted mt-1">Actual INR from CoinDCX account - real P&L</div>
          </div>
        </div>
      )}

      {/* Performance */}
      {perf && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Total Trades - Real</div>
            <div className="text-xl font-bold">{perf.total_trades ?? perf.closed_trades ?? 0}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Win Rate - Real</div>
            <div className="text-xl font-bold text-emerald-400">{(perf.win_rate ?? 0).toFixed(1)}%</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Profit Factor - Real</div>
            <div className="text-xl font-bold">{(perf.profit_factor ?? 0).toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Best Trade - Real</div>
            <div className="text-xl font-bold text-emerald-400">${(perf.best_trade ?? 0).toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Worst Trade - Real</div>
            <div className="text-xl font-bold text-red-400">${(perf.worst_trade ?? 0).toFixed(2)}</div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
            <div className="text-[10px] text-crypto-muted uppercase">Profit - Real INR</div>
            <div className={`text-xl font-bold ${(perf.total_pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${(perf.total_pnl ?? 0).toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Allocation */}
      {allocation && Object.keys(allocation).length > 0 && (
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold flex items-center gap-2 mb-4"><PieChart size={16} /> Allocation - Real Holdings - CoinDCX Actual</h3>
          <div className="space-y-2">
            {Object.entries(allocation).map(([sym, pct]) => (
              <div key={sym} className="flex items-center gap-3">
                <div className="w-20 text-sm font-medium">{sym}</div>
                <div className="flex-1 h-2 bg-crypto-bg rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-emerald-500 to-violet-500" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}></div>
                </div>
                <div className="w-12 text-xs text-crypto-muted">{(pct ?? 0).toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Positions */}
      <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
        <h3 className="font-bold flex items-center gap-2 mb-4"><BarChart3 size={16} /> Open Positions - CoinDCX Real Money - Actual INR Trades</h3>
        {openPositions.length === 0 ? (
          <div className="text-center py-8 text-crypto-muted">No open positions - open one via Auto Trading or manually - real CoinDCX trades</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-crypto-muted uppercase">
                <tr><th className="text-left py-2">Symbol</th><th>Side</th><th>Entry</th><th>Qty</th><th>SL</th><th>TP</th><th>Lev</th><th>Action</th></tr>
              </thead>
              <tbody>
                {openPositions.map((p, i) => (
                  <tr key={i} className="border-t border-crypto-border/30">
                    <td className="py-3 font-bold">{p.symbol || 'Unknown'}</td>
                    <td><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${p.side === 'LONG' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{p.side || 'LONG'}</span></td>
                    <td>${(p.entry_price ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td>{(p.quantity ?? 0).toFixed(6)}</td>
                    <td className="text-red-400">${(p.stop_loss ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td className="text-emerald-400">${(p.take_profits?.tp1 ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                    <td>{p.leverage || '1x'}</td>
                    <td><button onClick={() => closePos(p.symbol)} className="px-3 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs">Close Real</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Closed */}
      {closedPositions.length > 0 && (
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold mb-4">Closed Positions - Real P&L History - CoinDCX Actual Money</h3>
          <div className="space-y-2 max-h-[300px] overflow-auto">
            {closedPositions.slice(-20).reverse().map((p, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
                <div className="flex items-center gap-3">
                  <span className="font-bold">{p.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${p.side === 'LONG' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{p.side}</span>
                  <span className="text-xs text-crypto-muted">{(p.quantity ?? 0).toFixed(6)} @ ${(p.entry_price ?? 0).toFixed(2)}</span>
                </div>
                <div className={`font-bold ${(p.pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${(p.pnl ?? 0).toFixed(2)} ({(p.pnl_pct ?? 0).toFixed(2)}%)</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Open Modal */}
      {showOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4">
          <div className="p-6 rounded-2xl bg-crypto-card border border-crypto-border w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">Open Real Position - CoinDCX Actual INR</h3>
              <button onClick={() => setShowOpen(false)} className="p-2 rounded-lg hover:bg-crypto-bg"><X size={16} /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-crypto-muted">Symbol - CoinDCX Market (BTCINR etc)</label>
                <select value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                  {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD'].map(s => <option key={s} value={s}>{s} → {s.replace('USD','INR').replace('-','')}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-crypto-muted">Side</label>
                  <select value={form.side} onChange={e => setForm({ ...form, side: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border">
                    <option value="LONG">LONG - Buy Real</option>
                    <option value="SHORT">SHORT - Sell Real</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-crypto-muted">Quantity</label>
                  <input type="number" step="0.000001" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border" />
                </div>
              </div>
              <div>
                <label className="text-xs text-crypto-muted">Entry Price (leave empty for live CoinDCX price)</label>
                <input type="number" value={form.entry_price} onChange={e => setForm({ ...form, entry_price: e.target.value })} placeholder="Live CoinDCX price" className="w-full mt-1 px-3 py-2 rounded-xl bg-crypto-bg border border-crypto-border" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-xs">
                <div className="font-bold text-emerald-400">CoinDCX Real Money - No Paper Simulation</div>
                <div className="text-crypto-muted mt-1">This uses ACTUAL INR from your CoinDCX account - real trades, real P&L as you requested. Uses live CoinDCX price BTCINR etc. Risk guards protect capital. No paper simulation.</div>
              </div>
              <button onClick={openPos} className="w-full py-3 rounded-xl bg-emerald-500 text-black font-bold hover:bg-emerald-400">Open Real Position - Actual INR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
