import { useSettingsStore } from '../store/useSettingsStore'
import { THEMES } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { Bot, Grid3X3, TrendingUp, Zap, Plus, DollarSign, Activity, BarChart3, Layers, Repeat, Coins, Shield } from 'lucide-react'
import { api } from '../api/client'

export default function Strategies() {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isDark = !isLight
  const [bots, setBots] = useState(null)
  const [breakouts, setBreakouts] = useState([])
  const [institutional, setInstitutional] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dcaForm, setDcaForm] = useState({ symbol: 'BTC-USD', total_investment: 1000, num_orders: 5, price_deviation_pct: 1.5, take_profit_pct: 5, stop_loss_pct: 3 })
  const [gridForm, setGridForm] = useState({ symbol: 'BTC-USD', lower_price: 100000, upper_price: 120000, num_grids: 10, total_investment: 1000 })
  const [mmForm, setMmForm] = useState({ symbol: 'BTC-USD', total_investment: 10000, spread_bps: 20, max_inventory: 1.0 })
  const [execForm, setExecForm] = useState({ symbol: 'BTC-USD', side: 'BUY', total_quantity: 0.1, strategy: 'TWAP', duration_minutes: 60, num_slices: 12 })
  const [statForm, setStatForm] = useState({ symbol_a: 'BTC-USD', symbol_b: 'ETH-USD', entry_z: 2.0 })
  const [showDCA, setShowDCA] = useState(false)
  const [showGrid, setShowGrid] = useState(false)
  const [showMM, setShowMM] = useState(false)
  const [showExec, setShowExec] = useState(false)
  const [showStat, setShowStat] = useState(false)

  const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }

  const fetchData = async () => {
    try {
      const [bRes, brRes, instRes] = await Promise.all([
        fetch('/api/strategies/all').then(r => r.json()).catch(() => null),
        fetch('/api/strategies/breakout/scan').then(r => r.json()).catch(() => null),
        fetch('/api/strategies/institutional/scan').then(r => r.json()).catch(() => null)
      ])
      setBots(bRes)
      setBreakouts(brRes?.breakouts || brRes?.all_signals || [])
      setInstitutional(instRes?.results || null)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const createDCA = async () => {
    try {
      await fetch('/api/strategies/dca', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dcaForm) }).then(r=>r.json())
      setShowDCA(false); fetchData(); alert('DCA Bot created for real trading!')
    } catch (e) { alert(e.message) }
  }
  const createGrid = async () => {
    try {
      await fetch('/api/strategies/grid', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(gridForm) }).then(r=>r.json())
      setShowGrid(false); fetchData(); alert('Grid Bot created!')
    } catch (e) { alert(e.message) }
  }
  const createMM = async () => {
    try {
      await fetch('/api/strategies/market_making', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mmForm) }).then(r=>r.json())
      setShowMM(false); fetchData(); alert('Market Making Bot created - Avellaneda-Stoikov!')
    } catch (e) { alert(e.message) }
  }
  const createExec = async () => {
    try {
      await fetch('/api/strategies/execution', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(execForm) }).then(r=>r.json())
      setShowExec(false); fetchData(); alert(`${execForm.strategy} execution created!`)
    } catch (e) { alert(e.message) }
  }
  const createStat = async () => {
    try {
      await fetch('/api/strategies/stat_arb', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(statForm) }).then(r=>r.json())
      setShowStat(false); fetchData(); alert(`Stat Arb ${statForm.symbol_a}/${statForm.symbol_b} created!`)
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center text-zinc-500">Loading strategies...</div>

  return (
    <div className={`min-h-screen font-poppins ${isDark ? 'theme-bg' : 'theme-bg'}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-6">
        <div>
          <h1 className={`text-2xl font-bold flex items-center gap-3 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Bot size={20} /> Trading Bots • Institutional</h1>
          <p className="text-[12px] text-zinc-500 mt-1">Real trading bots + Institutional: Market Making Avellaneda-Stoikov, TWAP/VWAP, Stat Arb Pairs, OrderBook Imbalance OFI, Funding Arb, Risk VaR/Kelly</p>
        </div>

        {/* Institutional Header */}
        <div className="ui-card p-4 border border-emerald-500/20">
          <div className="flex items-center gap-2 mb-2"><Shield size={16} className="text-emerald-500" /><span className={`font-bold text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Institutional Research Integrated</span><span className="ui-pill-live text-[9px]">INSTITUTIONAL</span></div>
          <div className={`text-[11px] leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            Strategies from institutional research: <span className="font-bold">Market Making</span> (Avellaneda-Stoikov optimal bid/ask with inventory risk γ, order book liquidity κ, volatility), <span className="font-bold">TWAP/VWAP</span> (slippage minimization, volume profile, time slicing), <span className="font-bold">Stat Arb</span> (Engle-Granger cointegration, OLS hedge ratio, z-score mean reversion, half-life), <span className="font-bold">OrderBook Imbalance</span> (bid/ask pressure, OFI order flow imbalance, weighted imbalance), <span className="font-bold">Funding Arb</span> (spot-futures basis, funding rate collection), <span className="font-bold">Risk Model</span> (VaR 95%, CVaR, Kelly Criterion, drawdown control, correlation risk).
          </div>
        </div>

        {/* Bot Types Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="ui-card p-4">
            <DollarSign className="text-emerald-600" size={18} />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>DCA Bot</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Buy dips below market</p>
            <button onClick={() => setShowDCA(true)} className="mt-3 w-full py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] text-[11px] font-bold flex items-center justify-center gap-1"><Plus size={12} /> Create</button>
          </div>
          <div className="ui-card p-4">
            <Grid3X3 size={18} className={isDark ? 'text-[var(--text)]' : 'text-black'} />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Grid Bot</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Ranging market profits</p>
            <button onClick={() => setShowGrid(true)} className="mt-3 w-full py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] text-[11px] font-bold flex items-center justify-center gap-1"><Plus size={12} /> Create</button>
          </div>
          <div className="ui-card p-4 border border-emerald-500/20">
            <Layers size={18} className="text-emerald-500" />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Market Making</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Avellaneda-Stoikov + OFI</p>
            <button onClick={() => setShowMM(true)} className="mt-3 w-full py-2 rounded-xl bg-emerald-500 text-black text-[11px] font-bold flex items-center justify-center gap-1"><Plus size={12} /> Create MM</button>
          </div>
          <div className="ui-card p-4">
            <BarChart3 size={18} className={isDark ? 'text-[var(--text)]' : 'text-black'} />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>TWAP/VWAP</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Execution algos</p>
            <button onClick={() => setShowExec(true)} className="mt-3 w-full py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] text-[11px] font-bold flex items-center justify-center gap-1"><Plus size={12} /> Execute</button>
          </div>
          <div className="ui-card p-4">
            <Repeat size={18} className={isDark ? 'text-[var(--text)]' : 'text-black'} />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Stat Arb</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Pairs cointegration</p>
            <button onClick={() => setShowStat(true)} className="mt-3 w-full py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] text-[11px] font-bold flex items-center justify-center gap-1"><Plus size={12} /> Pair</button>
          </div>
          <div className="ui-card p-4">
            <Activity size={18} className="text-amber-600" />
            <h3 className={`font-bold mt-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>OFI Scanner</h3>
            <p className="text-[11px] text-zinc-500 mt-1">Order flow imbalance</p>
            <button onClick={fetchData} className="mt-3 w-full py-2 rounded-xl bg-amber-500 text-black text-[11px] font-bold flex items-center justify-center gap-1"><Zap size={12} /> Scan</button>
          </div>
        </div>

        {/* Active Bots */}
        <div className="ui-card p-5">
          <h3 className={`font-bold mb-4 text-[14px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Active Bots • Real Trading ({bots?.count ?? 0}) • Institutional Included</h3>
          {!bots || (bots.count ?? 0) === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-[12px]">No active bots - create DCA, Grid, Market Making, TWAP/VWAP, Stat Arb for real trading</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(bots.dca_bots || {}).map(([sym, bot]) => (
                <div key={sym} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{sym} DCA</span><span className="ui-pill text-[10px]">{bot.config?.num_orders ?? 5} orders</span></div>
                  <div className="mt-2 space-y-1"><div className="flex justify-between"><span className="text-zinc-500">Total</span><span>${safeFixed(bot.config?.total_investment,0)}</span></div></div>
                </div>
              ))}
              {Object.entries(bots.grid_bots || {}).map(([sym, bot]) => (
                <div key={sym} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{sym} GRID</span><span className="ui-pill text-[10px]">{bot.config?.num_grids ?? 10} grids</span></div>
                  <div className="mt-2 space-y-1"><div className="flex justify-between"><span className="text-zinc-500">Range</span><span>${safeFixed(bot.config?.lower_price,0)}-${safeFixed(bot.config?.upper_price,0)}</span></div></div>
                </div>
              ))}
              {Object.entries(bots.mm_bots || {}).map(([sym, bot]) => (
                <div key={sym} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-emerald-500/20' : 'bg-emerald-50 border-emerald-500/20'}`}>
                  <div className="flex justify-between"><span className="font-bold">{sym} MM</span><span className="ui-pill-live text-[9px]">AVELLANEDA</span></div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between"><span className="text-zinc-500">Bid</span><span className="text-emerald-600">${safeFixed(bot.latest_quote?.bid_price,2)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Ask</span><span className="text-red-500">${safeFixed(bot.latest_quote?.ask_price,2)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Spread</span><span>${safeFixed(bot.latest_quote?.spread,2)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Inventory</span><span>{safeFixed(bot.inventory,3)}</span></div>
                  </div>
                </div>
              ))}
              {Object.entries(bots.stat_arb_bots || {}).map(([pair, bot]) => (
                <div key={pair} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{pair}</span><span className={`ui-pill text-[9px] ${bot.latest_signal?.signal?.includes('LONG') ? 'ui-pill-buy' : bot.latest_signal?.signal?.includes('SHORT') ? 'ui-pill-sell' : ''}`}>{bot.latest_signal?.signal || 'HOLD'}</span></div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between"><span className="text-zinc-500">Z-Score</span><span>{safeFixed(bot.latest_signal?.z_score,2)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Hedge Ratio</span><span>{safeFixed(bot.latest_signal?.hedge_ratio,3)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Half-life</span><span>{safeFixed(bot.latest_signal?.half_life,1)}d</span></div>
                  </div>
                </div>
              ))}
              {Object.entries(bots.ofi_bots || {}).map(([sym, bot]) => (
                <div key={sym} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{sym} OFI</span><span className={`ui-pill text-[9px] ${bot.latest_signal?.signal?.includes('BUY') ? 'ui-pill-buy' : bot.latest_signal?.signal?.includes('SELL') ? 'ui-pill-sell' : ''}`}>{bot.latest_signal?.signal || 'HOLD'}</span></div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between"><span className="text-zinc-500">Imbalance</span><span>{safeFixed(bot.latest_signal?.imbalance,3)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">OFI</span><span>{safeFixed(bot.latest_signal?.ofi,3)}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Mid</span><span>${safeFixed(bot.latest_signal?.mid_price,2)}</span></div>
                  </div>
                </div>
              ))}
              {Object.entries(bots.funding_bots || {}).map(([sym, bot]) => (
                <div key={sym} className={`p-3 rounded-xl border text-[12px] ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{sym} Funding</span><span className="ui-pill text-[9px]">{bot.latest_signal?.signal || 'HOLD'}</span></div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between"><span className="text-zinc-500">Funding</span><span>{safeFixed((bot.latest_signal?.funding_rate||0)*100,4)}%</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Annualized</span><span>{safeFixed((bot.latest_signal?.annualized_rate||0)*100,2)}%</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Basis</span><span>{safeFixed((bot.latest_signal?.basis||0)*100,3)}%</span></div>
                    <div className="flex justify-between"><span className="text-zinc-500">Est Profit</span><span className="text-emerald-600">${safeFixed(bot.latest_signal?.estimated_profit,2)}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Institutional Scan Results */}
        {institutional && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="ui-card p-4">
              <h4 className={`font-bold text-[12px] mb-3 flex items-center gap-1.5 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Activity size={12} /> OrderBook Imbalance</h4>
              <div className="space-y-2">
                {(institutional.orderbook_imbalance || []).slice(0,3).map((s,i)=>(
                  <div key={i} className={`p-2 rounded-lg border text-[11px] flex justify-between ${isDark ? 'theme-bg border-white/5' : 'bg-white border-black/5'}`}>
                    <span className="font-bold">{s.symbol}</span><span className={s.signal?.includes('BUY') ? 'text-emerald-600' : s.signal?.includes('SELL') ? 'text-red-500' : 'text-zinc-500'}>{s.signal} I:{safeFixed(s.imbalance,2)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="ui-card p-4">
              <h4 className={`font-bold text-[12px] mb-3 flex items-center gap-1.5 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Coins size={12} /> Funding Arb</h4>
              <div className="space-y-2">
                {(institutional.funding_arb || []).slice(0,3).map((s,i)=>(
                  <div key={i} className={`p-2 rounded-lg border text-[11px] flex justify-between ${isDark ? 'theme-bg border-white/5' : 'bg-white border-black/5'}`}>
                    <span className="font-bold">{s.symbol}</span><span className="text-emerald-600">{safeFixed((s.funding_rate||0)*100,4)}% → {s.signal?.split('_')[0]}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="ui-card p-4">
              <h4 className={`font-bold text-[12px] mb-3 flex items-center gap-1.5 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Layers size={12} /> Market Making</h4>
              <div className="space-y-2">
                {(institutional.market_making || []).slice(0,3).map((s,i)=>(
                  <div key={i} className={`p-2 rounded-lg border text-[11px] ${isDark ? 'theme-bg border-white/5' : 'bg-white border-black/5'}`}>
                    <div className="flex justify-between"><span className="font-bold">{s.symbol}</span><span className="text-zinc-500">Spread ${safeFixed(s.spread,2)}</span></div>
                    <div className="flex justify-between text-[10px] text-zinc-500"><span>Bid ${safeFixed(s.bid_price,0)}</span><span>Ask ${safeFixed(s.ask_price,0)}</span></div>
                  </div>
                ))}
              </div>
            </div>
            <div className="ui-card p-4">
              <h4 className={`font-bold text-[12px] mb-3 flex items-center gap-1.5 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Repeat size={12} /> Stat Arb Pairs</h4>
              <div className="space-y-2">
                {(institutional.stat_arb || []).slice(0,3).map((s,i)=>(
                  <div key={i} className={`p-2 rounded-lg border text-[11px] flex justify-between ${isDark ? 'theme-bg border-white/5' : 'bg-white border-black/5'}`}>
                    <span className="font-bold">{s.pair}</span><span className={s.signal?.includes('LONG') ? 'text-emerald-600' : s.signal?.includes('SHORT') ? 'text-red-500' : 'text-zinc-500'}>{s.signal} Z:{safeFixed(s.z_score,1)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Breakouts */}
        <div className="ui-card p-5">
          <h3 className={`font-bold mb-4 flex items-center gap-2 text-[13px] ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Zap size={14} /> Breakout Signals • Volume Confirmed</h3>
          {breakouts.length === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-[12px]">No breakouts detected - market ranging</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {breakouts.map((b, i) => (
                <div key={i} className={`p-3 rounded-xl border text-[11px] ${b.signal?.includes('BUY') ? 'bg-emerald-500/5 border-emerald-500/20' : b.signal?.includes('SELL') ? 'bg-red-500/5 border-red-500/10' : 'bg-zinc-50 dark:bg-zinc-900 border-black/5 dark:border-white/5'}`}>
                  <div className="flex justify-between"><span className="font-bold">{b.symbol}</span><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${b.signal?.includes('BUY') ? 'bg-emerald-500 text-black' : b.signal?.includes('SELL') ? 'bg-red-500 text-[var(--text)]' : 'ui-pill'}`}>{b.signal}</span></div>
                  <div className="mt-2 space-y-1"><div className="flex justify-between"><span className="text-zinc-500">Entry</span><span>${safeFixed(b.entry_price,2)}</span></div><div className="flex justify-between"><span className="text-zinc-500">SL</span><span className="text-red-500">${safeFixed(b.stop_loss,2)}</span></div><div className="flex justify-between"><span className="text-zinc-500">TP</span><span className="text-emerald-600">${safeFixed(b.take_profit,2)}</span></div></div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modals */}
        {showDCA && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-bg/70 backdrop-blur p-4">
            <div className="ui-card w-full max-w-md p-5">
              <h3 className={`font-bold mb-4 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Create DCA Bot</h3>
              <div className="space-y-2">
                <select value={dcaForm.symbol} onChange={e => setDcaForm({ ...dcaForm, symbol: e.target.value })} className="ui-input"><option>BTC-USD</option><option>ETH-USD</option><option>SOL-USD</option></select>
                <input type="number" placeholder="Total Investment" value={dcaForm.total_investment} onChange={e => setDcaForm({ ...dcaForm, total_investment: parseFloat(e.target.value)||1000 })} className="ui-input" />
                <div className="grid grid-cols-2 gap-2"><input type="number" placeholder="Orders" value={dcaForm.num_orders} onChange={e => setDcaForm({ ...dcaForm, num_orders: parseInt(e.target.value)||5 })} className="ui-input" /><input type="number" step="0.1" placeholder="Deviation %" value={dcaForm.price_deviation_pct} onChange={e => setDcaForm({ ...dcaForm, price_deviation_pct: parseFloat(e.target.value)||1.5 })} className="ui-input" /></div>
                <div className="flex gap-2"><button onClick={() => setShowDCA(false)} className="flex-1 py-2 rounded-xl ui-card">Cancel</button><button onClick={createDCA} className="flex-1 py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] font-bold">Create</button></div>
              </div>
            </div>
          </div>
        )}
        {showGrid && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-bg/70 backdrop-blur p-4">
            <div className="ui-card w-full max-w-md p-5">
              <h3 className={`font-bold mb-4 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Create Grid Bot</h3>
              <div className="space-y-2">
                <select value={gridForm.symbol} onChange={e => setGridForm({ ...gridForm, symbol: e.target.value })} className="ui-input"><option>BTC-USD</option><option>ETH-USD</option></select>
                <div className="grid grid-cols-2 gap-2"><input type="number" placeholder="Lower" value={gridForm.lower_price} onChange={e => setGridForm({ ...gridForm, lower_price: parseFloat(e.target.value)||0 })} className="ui-input" /><input type="number" placeholder="Upper" value={gridForm.upper_price} onChange={e => setGridForm({ ...gridForm, upper_price: parseFloat(e.target.value)||0 })} className="ui-input" /></div>
                <div className="flex gap-2"><button onClick={() => setShowGrid(false)} className="flex-1 py-2 rounded-xl ui-card">Cancel</button><button onClick={createGrid} className="flex-1 py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] font-bold">Create</button></div>
              </div>
            </div>
          </div>
        )}
        {showMM && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-bg/70 backdrop-blur p-4">
            <div className="ui-card w-full max-w-md p-5 border border-emerald-500/20">
              <h3 className={`font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}><Layers size={16} className="text-emerald-500" /> Market Making • Avellaneda-Stoikov</h3>
              <p className="text-[11px] text-zinc-500 mb-3">Optimal bid/ask with inventory risk γ, liquidity κ, volatility, order book imbalance filter</p>
              <div className="space-y-2">
                <select value={mmForm.symbol} onChange={e => setMmForm({ ...mmForm, symbol: e.target.value })} className="ui-input"><option>BTC-USD</option><option>ETH-USD</option><option>SOL-USD</option></select>
                <input type="number" placeholder="Investment" value={mmForm.total_investment} onChange={e => setMmForm({ ...mmForm, total_investment: parseFloat(e.target.value)||10000 })} className="ui-input" />
                <div className="grid grid-cols-2 gap-2"><input type="number" placeholder="Spread bps" value={mmForm.spread_bps} onChange={e => setMmForm({ ...mmForm, spread_bps: parseFloat(e.target.value)||20 })} className="ui-input" /><input type="number" step="0.1" placeholder="Max Inventory" value={mmForm.max_inventory} onChange={e => setMmForm({ ...mmForm, max_inventory: parseFloat(e.target.value)||1 })} className="ui-input" /></div>
                <div className="flex gap-2"><button onClick={() => setShowMM(false)} className="flex-1 py-2 rounded-xl ui-card">Cancel</button><button onClick={createMM} className="flex-1 py-2 rounded-xl bg-emerald-500 text-black font-bold">Create MM Bot</button></div>
              </div>
            </div>
          </div>
        )}
        {showExec && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-bg/70 backdrop-blur p-4">
            <div className="ui-card w-full max-w-md p-5">
              <h3 className={`font-bold mb-2 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>TWAP/VWAP Execution</h3>
              <p className="text-[11px] text-zinc-500 mb-3">Institutional execution to minimize slippage • Time slicing • Volume profile</p>
              <div className="space-y-2">
                <select value={execForm.symbol} onChange={e => setExecForm({ ...execForm, symbol: e.target.value })} className="ui-input"><option>BTC-USD</option><option>ETH-USD</option></select>
                <div className="grid grid-cols-2 gap-2"><select value={execForm.side} onChange={e => setExecForm({ ...execForm, side: e.target.value })} className="ui-input"><option>BUY</option><option>SELL</option></select><select value={execForm.strategy} onChange={e => setExecForm({ ...execForm, strategy: e.target.value })} className="ui-input"><option>TWAP</option><option>VWAP</option></select></div>
                <input type="number" step="0.001" placeholder="Quantity" value={execForm.total_quantity} onChange={e => setExecForm({ ...execForm, total_quantity: parseFloat(e.target.value)||0.1 })} className="ui-input" />
                <div className="flex gap-2"><button onClick={() => setShowExec(false)} className="flex-1 py-2 rounded-xl ui-card">Cancel</button><button onClick={createExec} className="flex-1 py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] font-bold">Execute {execForm.strategy}</button></div>
              </div>
            </div>
          </div>
        )}
        {showStat && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-bg/70 backdrop-blur p-4">
            <div className="ui-card w-full max-w-md p-5">
              <h3 className={`font-bold mb-2 ${isDark ? 'text-[var(--text)]' : 'text-black'}`}>Stat Arb • Pairs Trading</h3>
              <p className="text-[11px] text-zinc-500 mb-3">Cointegration Engle-Granger, OLS hedge ratio, z-score mean reversion, half-life</p>
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2"><select value={statForm.symbol_a} onChange={e => setStatForm({ ...statForm, symbol_a: e.target.value })} className="ui-input"><option>BTC-USD</option><option>ETH-USD</option><option>BNB-USD</option></select><select value={statForm.symbol_b} onChange={e => setStatForm({ ...statForm, symbol_b: e.target.value })} className="ui-input"><option>ETH-USD</option><option>BTC-USD</option><option>SOL-USD</option></select></div>
                <input type="number" step="0.1" placeholder="Entry Z" value={statForm.entry_z} onChange={e => setStatForm({ ...statForm, entry_z: parseFloat(e.target.value)||2 })} className="ui-input" />
                <div className="flex gap-2"><button onClick={() => setShowStat(false)} className="flex-1 py-2 rounded-xl ui-card">Cancel</button><button onClick={createStat} className="flex-1 py-2 rounded-xl theme-bg dark:bg-white text-[var(--text)] font-bold">Create Pair</button></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
