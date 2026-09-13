import { useSettingsStore } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { Bot, Grid3X3, TrendingUp, Zap, Plus, DollarSign } from 'lucide-react'
import { api } from '../api/client'

export default function Strategies() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const [bots, setBots] = useState(null)
  const [breakouts, setBreakouts] = useState([])
  const [loading, setLoading] = useState(true)
  const [dcaForm, setDcaForm] = useState({ symbol: 'BTC-USD', total_investment: 1000, num_orders: 5, price_deviation_pct: 1.5, take_profit_pct: 5, stop_loss_pct: 3 })
  const [gridForm, setGridForm] = useState({ symbol: 'BTC-USD', lower_price: 100000, upper_price: 120000, num_grids: 10, total_investment: 1000 })
  const [showDCA, setShowDCA] = useState(false)
  const [showGrid, setShowGrid] = useState(false)

  const safeFixed = (v, d=2) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toFixed(d)
  }

  const fetchData = async () => {
    try {
      const [bRes, brRes] = await Promise.all([
        api.getAllStrategies().catch(() => fetch('/api/strategies/all').then(r => r.json())),
        api.scanBreakouts().catch(() => fetch('/api/strategies/breakout/scan').then(r => r.json()))
      ])
      setBots(bRes)
      setBreakouts(brRes.breakouts || brRes.all_signals || [])
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const createDCA = async () => {
    try {
      const data = await api.createDCABot(dcaForm).catch(() => fetch('/api/strategies/dca', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dcaForm) }).then(r=>r.json()))
      setShowDCA(false); fetchData(); alert('DCA Bot created for real trading!')
    } catch (e) { alert(e.message) }
  }

  const createGrid = async () => {
    try {
      await api.createGridBot(gridForm).catch(() => fetch('/api/strategies/grid', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(gridForm) }).then(r=>r.json()))
      setShowGrid(false); fetchData(); alert('Grid Bot created for real trading!')
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center">Loading real strategy bots...</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 font-poppins space-y-6">
      <div>
        <h1 className="text-3xl font-black flex items-center gap-3"><Bot className="text-zinc-500" /> Trading Bots - Real Strategies</h1>
        <p className="text-zinc-500 mt-1">DCA, Grid, Breakout - real trading bots for actual trades, no fake simulation</p>
      </div>

      {/* Bot Types */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-black/5 dark:border-white/5">
          <div className="flex items-center justify-between">
            <DollarSign className="text-emerald-600" size={20} />
            <span className="px-2 py-0.5 rounded-full bg-emerald-500 text-black text-[10px] font-black">REAL</span>
          </div>
          <h3 className="font-bold mt-3">DCA Bot</h3>
          <p className="text-xs text-zinc-500 mt-1">Dollar Cost Averaging - buy dips with real orders below market</p>
          <button onClick={() => setShowDCA(true)} className="mt-4 w-full py-2 rounded-xl bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 flex items-center justify-center gap-2"><Plus size={14} /> Create DCA Bot</button>
        </div>
        <div className="p-5 rounded-2xl bg-gradient-to-br from-violet-500/10 to-violet-600/5 border border-black/5 dark:border-white/5">
          <div className="flex items-center justify-between">
            <Grid3X3 className="text-zinc-500" size={20} />
            <span className="px-2 py-0.5 rounded-full bg-black dark:bg-white text-white text-[10px] font-black">REAL</span>
          </div>
          <h3 className="font-bold mt-3">Grid Bot</h3>
          <p className="text-xs text-zinc-500 mt-1">Profits from ranging markets - real grid levels with live prices</p>
          <button onClick={() => setShowGrid(true)} className="mt-4 w-full py-2 rounded-xl bg-black dark:bg-white text-white font-bold text-sm hover:bg-violet-400 flex items-center justify-center gap-2"><Plus size={14} /> Create Grid Bot</button>
        </div>
        <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-500/10 to-orange-600/5 border border-amber-500/20">
          <div className="flex items-center justify-between">
            <TrendingUp className="text-zinc-500" size={20} />
            <span className="px-2 py-0.5 rounded-full bg-amber-500 text-black text-[10px] font-black">LIVE SCAN</span>
          </div>
          <h3 className="font-bold mt-3">Breakout Scanner</h3>
          <p className="text-xs text-zinc-500 mt-1">Volume confirmed breakouts - real market opportunities</p>
          <button onClick={fetchData} className="mt-4 w-full py-2 rounded-xl bg-amber-500 text-black font-bold text-sm hover:bg-amber-400 flex items-center justify-center gap-2"><Zap size={14} /> Scan Breakouts</button>
        </div>
      </div>

      {/* Active Bots */}
      <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h3 className="font-bold mb-4">Active Bots - Real Trading ({bots?.count ?? 0})</h3>
        {!bots || (bots.count ?? 0) === 0 ? (
          <div className="text-center py-6 text-zinc-500">No active bots - create DCA or Grid bot for real trading</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(bots.dca_bots || {}).map(([sym, bot]) => (
              <div key={sym} className="p-4 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                <div className="flex items-center justify-between">
                  <span className="font-bold">{sym} DCA</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-emerald-600">{bot.config?.num_orders ?? bot.num_orders ?? 5} orders</span>
                </div>
                <div className="mt-3 space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-zinc-500">Total</span><span>${safeFixed(bot.config?.total_investment ?? bot.total_investment,0)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Live Price</span><span>${safeFixed(bot.live_price ?? bot.current_price,2)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">TP</span><span className="text-emerald-600">{safeFixed(bot.config?.take_profit_pct ?? bot.take_profit_pct,1)}%</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">SL</span><span className="text-red-500">{safeFixed(bot.config?.stop_loss_pct ?? bot.stop_loss_pct,1)}%</span></div>
                </div>
                <div className="mt-3">
                  <div className="text-[10px] text-zinc-500 uppercase">DCA Levels</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(bot.levels || bot.dca_levels || []).slice(0, 5).map((l, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded-full ui-card border border-black/5 dark:border-white/5">${safeFixed(l.price ?? l,0)}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            {Object.entries(bots.grid_bots || {}).map(([sym, bot]) => (
              <div key={sym} className="p-4 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                <div className="flex items-center justify-between">
                  <span className="font-bold">{sym} GRID</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500">{bot.config?.num_grids ?? bot.num_grids ?? 10} grids</span>
                </div>
                <div className="mt-3 space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-zinc-500">Range</span><span>${safeFixed(bot.config?.lower_price ?? bot.lower_price,0)} - ${safeFixed(bot.config?.upper_price ?? bot.upper_price,0)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Total</span><span>${safeFixed(bot.config?.total_investment ?? bot.total_investment,0)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Profit/Grid</span><span className="text-emerald-600">${safeFixed(bot.profit_per_grid ?? bot.profit_per_grid_pct,2)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Live</span><span>${safeFixed(bot.live_price ?? bot.current_price,2)}</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Breakouts */}
      <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h3 className="font-bold mb-4 flex items-center gap-2"><Zap size={16} className="text-zinc-500" /> Breakout Signals - Real Market (Volume Confirmed)</h3>
        {breakouts.length === 0 ? (
          <div className="text-center py-6 text-zinc-500">No breakouts detected - market is ranging</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {breakouts.map((b, i) => (
              <div key={i} className={`p-4 rounded-xl border ${b.signal?.includes('BUY') ? 'bg-emerald-500/5 border-black/5 dark:border-white/5' : b.signal?.includes('SELL') ? 'bg-red-500/5 border-red-500/10' : 'bg-transparent border-black/5 dark:border-white/5/50'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">{b.symbol || 'Unknown'}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${b.signal?.includes('BUY') ? 'bg-emerald-500 text-black' : b.signal?.includes('SELL') ? 'bg-red-500 text-white' : 'ui-card text-zinc-500'}`}>{b.signal || 'HOLD'}</span>
                </div>
                <div className="mt-2 text-xs space-y-1">
                  <div className="flex justify-between"><span className="text-zinc-500">Entry</span><span>${safeFixed(b.entry_price,2)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Breakout Level</span><span>${safeFixed(b.breakout_level,2)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Volume Confirmed</span><span className={b.volume_confirmed ? 'text-emerald-600' : 'text-zinc-500'}>{b.volume_confirmed ? 'Yes ✓' : 'No'}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">SL</span><span className="text-red-500">${safeFixed(b.stop_loss,2)}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">TP</span><span className="text-emerald-600">${safeFixed(b.take_profit,2)}</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showDCA && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4">
          <div className="p-6 rounded-2xl ui-card border border-black/5 dark:border-white/5 w-full max-w-md">
            <h3 className="font-bold text-lg mb-4">Create DCA Bot - Real Accumulation</h3>
            <div className="space-y-3">
              <select value={dcaForm.symbol} onChange={e => setDcaForm({ ...dcaForm, symbol: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <input type="number" placeholder="Total Investment $" value={dcaForm.total_investment} onChange={e => setDcaForm({ ...dcaForm, total_investment: parseFloat(e.target.value)||1000 })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="Orders" value={dcaForm.num_orders} onChange={e => setDcaForm({ ...dcaForm, num_orders: parseInt(e.target.value)||5 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <input type="number" step="0.1" placeholder="Deviation %" value={dcaForm.price_deviation_pct} onChange={e => setDcaForm({ ...dcaForm, price_deviation_pct: parseFloat(e.target.value)||1.5 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" step="0.1" placeholder="TP %" value={dcaForm.take_profit_pct} onChange={e => setDcaForm({ ...dcaForm, take_profit_pct: parseFloat(e.target.value)||5 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <input type="number" step="0.1" placeholder="SL %" value={dcaForm.stop_loss_pct} onChange={e => setDcaForm({ ...dcaForm, stop_loss_pct: parseFloat(e.target.value)||3 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowDCA(false)} className="flex-1 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">Cancel</button>
                <button onClick={createDCA} className="flex-1 py-2 rounded-xl bg-emerald-500 text-black font-bold">Create Real DCA Bot</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showGrid && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4">
          <div className="p-6 rounded-2xl ui-card border border-black/5 dark:border-white/5 w-full max-w-md">
            <h3 className="font-bold text-lg mb-4">Create Grid Bot - Ranging Market Profits</h3>
            <div className="space-y-3">
              <select value={gridForm.symbol} onChange={e => setGridForm({ ...gridForm, symbol: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="Lower Price" value={gridForm.lower_price} onChange={e => setGridForm({ ...gridForm, lower_price: parseFloat(e.target.value)||0 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <input type="number" placeholder="Upper Price" value={gridForm.upper_price} onChange={e => setGridForm({ ...gridForm, upper_price: parseFloat(e.target.value)||0 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="Num Grids" value={gridForm.num_grids} onChange={e => setGridForm({ ...gridForm, num_grids: parseInt(e.target.value)||10 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <input type="number" placeholder="Total Investment" value={gridForm.total_investment} onChange={e => setGridForm({ ...gridForm, total_investment: parseFloat(e.target.value)||1000 })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowGrid(false)} className="flex-1 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">Cancel</button>
                <button onClick={createGrid} className="flex-1 py-2 rounded-xl bg-black dark:bg-white text-white font-bold">Create Real Grid Bot</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
