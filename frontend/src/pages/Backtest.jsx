import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import GlassCard, { StatCard } from '../components/GlassCard'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { BarChart3, TrendingUp, TrendingDown, Zap, Target, Shield, DollarSign, Activity, AlertCircle } from 'lucide-react'

const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)? (0).toFixed(d) : n.toFixed(d) }

export default function Backtest() {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isDark = !isLight

  const { selectedSymbol, setSelectedSymbol } = useMarketStore()
  const [strategy, setStrategy] = useState('ma')
  const [result, setResult] = useState(null)
  const [compare, setCompare] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [symbols, setSymbols] = useState(['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD'])

  useEffect(() => {
    api.getSymbols().then(d => {
      if (d.symbols?.length) setSymbols(d.symbols.slice(0,12))
    }).catch(()=>{})
  }, [])

  const runBacktest = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.backtest({ symbol: selectedSymbol, strategy, period: '1y', initial_capital: 10000 })
      setResult(res)
      setCompare(null)
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Backtest failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const runCompare = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.backtestCompare(selectedSymbol)
      setCompare(res.comparison)
      setResult(null)
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Compare failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen relative ${isDark ? 'theme-bg' : 'theme-bg'}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-semibold tracking-tight flex items-center gap-3 text-[var(--text)]">
              <span className="w-8 h-8 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]">
                <BarChart3 size={16} />
              </span>
              Backtesting Engine
              <span className="px-2.5 py-0.5 rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--text)] text-[11px] font-medium">PORTFOLIO SIM</span>
              {result && <span className="px-2 py-0.5 rounded-full bg-[var(--buy-soft)] border border-[var(--buy-border)] text-[var(--buy)] text-[10px] font-bold">{result.strategy} • {safeFixed(result.metrics?.total_return_pct,1)}%</span>}
            </h1>
            <p className="text-[12px] mt-1 text-[var(--text-muted)]">Long-only simulation • $10k initial • 0.1% commission • 0.05% slippage • Sharpe, DD, Win Rate • Real Binance data</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">
              <Shield size={12} /> Risk-free 2% • Annualized
            </span>
          </div>
        </div>

        <GlassCard className="p-5">
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">Asset</label>
              <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="block mt-1 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px] font-medium text-[var(--text)] min-w-[140px] focus:border-[var(--accent)] focus:outline-none">
                {symbols.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">Strategy</label>
              <select value={strategy} onChange={e => setStrategy(e.target.value)} className="block mt-1 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px] font-medium text-[var(--text)] min-w-[220px] focus:border-[var(--accent)] focus:outline-none">
                <option value="ma">Moving Average (20/50)</option>
                <option value="rsi">RSI (30/70)</option>
                <option value="ensemble">Ensemble (Pred+Sentiment+RSI)</option>
                <option value="prediction">Prediction Based</option>
              </select>
            </div>
            <button onClick={runBacktest} disabled={loading} className="px-4 h-[38px] rounded-full bg-[var(--accent)] text-white text-[13px] font-medium flex items-center gap-2 disabled:opacity-50 hover:scale-[1.02] transition shadow-[var(--glow)]">
              <Zap size={14} /> {loading ? 'Running...' : 'Run Backtest'}
            </button>
            <button onClick={runCompare} disabled={loading} className="px-4 h-[38px] rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--text)] text-[13px] font-medium flex items-center gap-2 disabled:opacity-50 hover:border-[var(--border-strong)] transition">
              <Target size={14} /> Compare All
            </button>
            
            <div className="ml-auto flex items-center gap-2">
              <span className="text-[11px] text-[var(--text-muted)] hidden md:inline">Real data • No mock</span>
              <span className="w-2 h-2 rounded-full bg-[var(--buy)] animate-pulse" />
            </div>
          </div>
          {error && (
            <div className="mt-4 p-3 rounded-xl bg-[var(--sell-soft)] border border-[var(--sell-border)] text-[12px] text-[var(--sell)] flex items-start gap-2">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <div><span className="font-semibold">Error:</span> {error}<br/><span className="text-[11px] opacity-80">Check backend logs at /docs or try another symbol</span></div>
            </div>
          )}
        </GlassCard>

        {result && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard label="Total Return" value={`${safeFixed(result.metrics?.total_return_pct,2)}%`} subValue={`${result.metrics.num_trades} trades`} trend={result.metrics.total_return_pct >= 0 ? `+${safeFixed(result.metrics?.total_return_pct,2)}%` : `${safeFixed(result.metrics?.total_return_pct,2)}%`} icon={TrendingUp} accent={result.metrics.total_return_pct >= 0 ? 'bull' : 'bear'} />
              <StatCard label="Sharpe Ratio" value={safeFixed(result.metrics?.sharpe_ratio,2)} subValue="Risk-adjusted" icon={Activity} accent="accent2" />
              <StatCard label="Max Drawdown" value={`${safeFixed(result.metrics?.max_drawdown_pct,2)}%`} subValue="Worst drop" icon={TrendingDown} accent="bear" />
              <StatCard label="Win Rate" value={`${safeFixed(result.metrics?.win_rate_pct,1)}%`} subValue={`PF: ${result.metrics?.profit_factor ? safeFixed(result.metrics.profit_factor,2) : "—"}`} icon={Target} accent="accent" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              <div className="lg:col-span-8">
                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] text-[var(--text)] mb-4 flex items-center gap-2">
                    <Activity size={14} className="text-[var(--accent)]" />
                    Equity Curve • {result.strategy} • {selectedSymbol} • ${safeFixed(result.metrics?.final_equity,0)}
                  </h3>
                  <ResponsiveContainer width="100%" height={380}>
                    <AreaChart data={result.equity_curve}>
                      <defs>
                        <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--buy)" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="var(--buy)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickFormatter={d => d.slice(5)} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} />
                      <Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', fontSize: '12px' }} />
                      <Area type="monotone" dataKey="equity" stroke="var(--buy)" fill="url(#equityGrad)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </GlassCard>
              </div>

              <div className="lg:col-span-4 space-y-5">
                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] text-[var(--text)] mb-3">Detailed Metrics</h3>
                  <div className="space-y-2">
                    {Object.entries(result.metrics || {}).map(([k, v]) => (
                      <div key={k} className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[var(--border-strong)] transition">
                        <span className="text-[11px] text-[var(--text-muted)] font-medium">{k.replace(/_/g, ' ')}</span>
                        <span className="mono text-[11px] font-semibold text-[var(--text)]">{typeof v === 'number' ? v.toFixed(2) : String(v)}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] text-[var(--text)] mb-3">Recent Trades ({result.trades?.length || 0})</h3>
                  <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
                    {(result.trades || []).slice(-12).reverse().map((t, i) => (
                      <div key={i} className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                        <div>
                          <div className="text-[11px] font-medium text-[var(--text)]">{t.entry_date?.slice(0,10)} → {t.exit_date?.slice(0,10)}</div>
                          <div className="text-[11px] text-[var(--text-muted)] mono">{safeFixed(t.entry_price,2)} → {safeFixed(t.exit_price,2)}</div>
                        </div>
                        <div className={`px-2.5 py-1 rounded-full text-[11px] font-bold mono border ${t.pnl >= 0 ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'}`}>
                          {t.pnl >= 0 ? '+' : ''}${safeFixed(t.pnl,2)}
                        </div>
                      </div>
                    ))}
                    {(!result.trades || result.trades.length === 0) && (
                      <div className="text-[11px] text-[var(--text-muted)] p-3 text-center">No trades in this period</div>
                    )}
                  </div>
                </GlassCard>
              </div>
            </div>
          </>
        )}

        {compare && (
          <GlassCard className="p-5">
            <h3 className="font-medium text-[13px] text-[var(--text)] mb-4 flex items-center gap-2">
              <BarChart3 size={14} className="text-[var(--accent)]" />
              Strategy Comparison • {selectedSymbol}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase border-b border-[var(--border)]">
                    <th className="text-left p-2.5">Strategy</th>
                    <th className="text-right p-2.5">Return</th>
                    <th className="text-right p-2.5">Sharpe</th>
                    <th className="text-right p-2.5">Max DD</th>
                    <th className="text-right p-2.5">Win Rate</th>
                    <th className="text-right p-2.5">Trades</th>
                    <th className="text-right p-2.5">Profit Factor</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(compare).map(([name, m]) => (
                    <tr key={name} className="border-b border-[var(--border)]/60 hover:bg-[var(--bg-secondary)]/50 transition">
                      <td className="p-2.5 font-medium text-[var(--text)]">{name}</td>
                      <td className={`p-2.5 text-right mono font-semibold ${m.total_return_pct >= 0 ? 'text-[var(--buy)]' : 'text-[var(--sell)]'}`}>{safeFixed(m.total_return_pct,2)}%</td>
                      <td className="p-2.5 text-right mono text-[var(--text)]">{safeFixed(m.sharpe_ratio,2)}</td>
                      <td className="p-2.5 text-right mono text-[var(--sell)]">{safeFixed(m.max_drawdown_pct,2)}%</td>
                      <td className="p-2.5 text-right mono text-[var(--text)]">{safeFixed(m.win_rate_pct,1)}%</td>
                      <td className="p-2.5 text-right mono text-[var(--text-muted)]">{m.num_trades}</td>
                      <td className="p-2.5 text-right mono text-[var(--text)]">{m.profit_factor ? safeFixed(m.profit_factor,2) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 text-[11px] text-[var(--text-muted)]">Comparison runs all 4 strategies (MA, RSI, Ensemble, Prediction) with same capital and period. Best Sharpe usually indicates most robust.</div>
          </GlassCard>
        )}

        {!result && !compare && (
          <GlassCard className="p-10 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--accent-soft)] border border-[var(--border)] flex items-center justify-center">
              <BarChart3 size={28} className="text-[var(--accent)]" />
            </div>
            <h3 className="font-semibold text-[var(--text)] text-[14px] mb-2">Backtesting Engine Ready</h3>
            <p className="text-[12px] text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">Select a symbol and strategy, then run backtest. Compares MA crossover, RSI, Ensemble (prediction + sentiment + RSI), and Prediction-based strategies with full portfolio simulation. Real Binance OHLCV data – no mocks.</p>
            <div className="mt-5 flex justify-center gap-2 flex-wrap">
              <span className="px-3 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Commission 0.1%</span>
              <span className="px-3 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Slippage 0.05%</span>
              <span className="px-3 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Long-only</span>
              <span className="px-3 py-1 rounded-full bg-[var(--buy-soft)] border border-[var(--buy-border)] text-[11px] text-[var(--buy)]">Real Data</span>
            </div>
            <div className="mt-6 flex justify-center gap-2">
              <button onClick={runBacktest} className="px-5 py-2 rounded-full bg-[var(--accent)] text-white text-[13px] font-medium shadow-[var(--glow)] hover:scale-[1.02] transition">Run {selectedSymbol} • {strategy.toUpperCase()}</button>
              <button onClick={runCompare} className="px-5 py-2 rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--text)] text-[13px] font-medium hover:border-[var(--border-strong)] transition">Compare All</button>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  )
}
