import { useState } from 'react'
import { api } from '../api/client'
import { useMarketStore } from '../store/useMarketStore'
import GlassCard, { StatCard } from '../components/GlassCard'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { BarChart3, TrendingUp, TrendingDown, Zap, Target, Shield, DollarSign, Activity } from 'lucide-react'

const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)? (0).toFixed(d) : n.toFixed(d) }

export default function Backtest() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const { selectedSymbol, setSelectedSymbol } = useMarketStore()
  const [strategy, setStrategy] = useState('ma')
  const [result, setResult] = useState(null)
  const [compare, setCompare] = useState(null)
  const [loading, setLoading] = useState(false)

  const runBacktest = async () => {
    setLoading(true)
    try {
      const res = await api.backtest({ symbol: selectedSymbol, strategy, period: '1y', initial_capital: 10000 })
      setResult(res)
      setCompare(null)
    } catch (e) {
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  const runCompare = async () => {
    setLoading(true)
    try {
      const res = await api.backtestCompare(selectedSymbol)
      setCompare(res.comparison)
      setResult(null)
    } catch (e) {
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen relative font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>

      
      
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-crypto-accent2 to-purple-600 flex items-center justify-center shadow-lg">
                <BarChart3 size={20} className="text-white" />
              </span>
              <span className="text-white">Backtesting Engine</span>
              <span className="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-black/5 dark:border-white/5 text-zinc-900 dark:text-white text-xs font-bold tracking-widest">PORTFOLIO SIM</span>
            </h1>
            <p className="text-zinc-500 text-sm mt-2">Long-only simulation • $10k initial • 0.1% commission • 0.05% slippage • Sharpe, DD, Win Rate</p>
          </div>
        </div>

        <GlassCard className="p-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="text-[11px] font-bold tracking-widest text-zinc-500 uppercase">Asset</label>
              <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="block mt-1 bg-transparent border border-black/5 dark:border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-white min-w-[140px]">
                {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[11px] font-bold tracking-widest text-zinc-500 uppercase">Strategy</label>
              <select value={strategy} onChange={e => setStrategy(e.target.value)} className="block mt-1 bg-transparent border border-black/5 dark:border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-white min-w-[200px]">
                <option value="ma">Moving Average (20/50)</option>
                <option value="rsi">RSI (30/70)</option>
                <option value="ensemble">Ensemble (Pred+Sentiment+RSI)</option>
                <option value="prediction">Prediction Based</option>
              </select>
            </div>
            <button onClick={runBacktest} disabled={loading} className="btn-primary h-[42px] flex items-center gap-2 disabled:opacity-50">
              <Zap size={14} /> {loading ? 'Running...' : 'Run Backtest'}
            </button>
            <button onClick={runCompare} disabled={loading} className="btn-secondary h-[42px] flex items-center gap-2 disabled:opacity-50">
              <Target size={14} /> Compare All
            </button>
            
            <div className="ml-auto hidden md:flex items-center gap-2 text-xs text-zinc-500">
              <Shield size={12} />
              <span>Risk-free 2% • Annualized metrics</span>
            </div>
          </div>
        </GlassCard>

        {result && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard label="Total Return" value={`${safeFixed(result.metrics?.total_return_pct,2)}%`} subValue={`${result.metrics.num_trades} trades`} trend={result.metrics.total_return_pct >= 0 ? `+${safeFixed(result.metrics?.total_return_pct,2)}%` : `${safeFixed(result.metrics?.total_return_pct,2)}%`} icon={TrendingUp} accent={result.metrics.total_return_pct >= 0 ? 'bull' : 'bear'} />
              <StatCard label="Sharpe Ratio" value={safeFixed(result.metrics?.sharpe_ratio,2)} subValue="Risk-adjusted" icon={Activity} accent="accent2" />
              <StatCard label="Max Drawdown" value={`${safeFixed(result.metrics?.max_drawdown_pct,2)}%`} subValue="Worst drop" icon={TrendingDown} accent="bear" />
              <StatCard label="Win Rate" value={`${safeFixed(result.metrics?.win_rate_pct,1)}%`} subValue={`PF: ${result.metrics?.profit_factor ? safeFixed(result.metrics.profit_factor,2) : "—" || '—'}`} icon={Target} accent="accent" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-8">
                <GlassCard className="p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <Activity size={18} className="text-zinc-900 dark:text-white" />
                    Equity Curve • {result.strategy} • {selectedSymbol}
                  </h3>
                  <ResponsiveContainer width="100%" height={380}>
                    <AreaChart data={result.equity_curve}>
                      <defs>
                        <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00d395" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#00d395" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" stroke="#475569" fontSize={11} tickFormatter={d => d.slice(5)} />
                      <YAxis stroke="#475569" fontSize={11} />
                      <Tooltip contentStyle={{ background: '#10161f', border: '1px solid #1e2a3a', borderRadius: '12px' }} />
                      <Area type="monotone" dataKey="equity" stroke="#00d395" fill="url(#equityGrad)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </GlassCard>
              </div>

              <div className="lg:col-span-4 space-y-6">
                <GlassCard className="p-6">
                  <h3 className="font-bold text-white mb-4">Detailed Metrics</h3>
                  <div className="space-y-2.5">
                    {Object.entries(result.metrics).map(([k, v]) => (
                      <div key={k} className="flex justify-between items-center p-2.5 rounded-xl bg-transparent/40 border border-black/5 dark:border-white/5/20 hover:border-black/5 dark:border-white/5/40 transition">
                        <span className="text-xs text-zinc-500 font-medium">{k.replace(/_/g, ' ')}</span>
                        <span className="mono text-xs font-bold text-white">{typeof v === 'number' ? v.toFixed(2) : v}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard className="p-6">
                  <h3 className="font-bold text-white mb-4">Recent Trades ({result.trades.length})</h3>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {result.trades.slice(-10).reverse().map((t, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-transparent/40 border border-black/5 dark:border-white/5/20">
                        <div>
                          <div className="text-xs font-bold text-white">{t.entry_date?.slice(0,10)} → {t.exit_date?.slice(0,10)}</div>
                          <div className="text-[11px] text-zinc-500">{safeFixed(t.entry_price,2)} → {safeFixed(t.exit_price,2)}</div>
                        </div>
                        <div className={`px-2.5 py-1 rounded-full text-xs font-bold mono ${t.pnl >= 0 ? 'bg-emerald-500/10 text-emerald-600 border border-black/5 dark:border-white/5' : 'bg-red-500/10 text-red-500 border border-red-500/10'}`}>
                          {t.pnl >= 0 ? '+' : ''}${safeFixed(t.pnl,2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </div>
          </>
        )}

        {compare && (
          <GlassCard className="p-6">
            <h3 className="font-bold text-white mb-6 flex items-center gap-2">
              <BarChart3 size={18} className="text-zinc-900 dark:text-white" />
              Strategy Comparison • {selectedSymbol}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[11px] font-bold tracking-widest text-zinc-500 uppercase border-b border-black/5 dark:border-white/5/30">
                    <th className="text-left p-3">Strategy</th>
                    <th className="text-right p-3">Return</th>
                    <th className="text-right p-3">Sharpe</th>
                    <th className="text-right p-3">Max DD</th>
                    <th className="text-right p-3">Win Rate</th>
                    <th className="text-right p-3">Trades</th>
                    <th className="text-right p-3">Profit Factor</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(compare).map(([name, m]) => (
                    <tr key={name} className="border-b border-black/5 dark:border-white/5/20 hover:ui-card/30 transition">
                      <td className="p-3 font-bold text-white">{name}</td>
                      <td className={`p-3 text-right mono font-bold ${m.total_return_pct >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>{safeFixed(m.total_return_pct,2)}%</td>
                      <td className="p-3 text-right mono text-white">{safeFixed(m.sharpe_ratio,2)}</td>
                      <td className="p-3 text-right mono text-red-500">{safeFixed(m.max_drawdown_pct,2)}%</td>
                      <td className="p-3 text-right mono text-white">{safeFixed(m.win_rate_pct,1)}%</td>
                      <td className="p-3 text-right mono text-zinc-500">{m.num_trades}</td>
                      <td className="p-3 text-right mono text-white">{m.profit_factor ? safeFixed(m.profit_factor,2) : "—" || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}

        {!result && !compare && (
          <GlassCard className="p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-crypto-accent2/20 to-purple-500/20 border border-crypto-accent2/20 flex items-center justify-center">
              <BarChart3 size={32} className="text-zinc-900 dark:text-white" />
            </div>
            <h3 className="font-bold text-white text-lg mb-2">Backtesting Engine Ready</h3>
            <p className="text-zinc-500 text-sm max-w-md mx-auto">Select a symbol and strategy, then run backtest. Compares MA crossover, RSI, Ensemble (prediction + sentiment + RSI), and Prediction-based strategies with full portfolio simulation.</p>
            <div className="mt-6 flex justify-center gap-2">
              <span className="px-3 py-1 rounded-full ui-card border border-black/5 dark:border-white/5 text-xs text-zinc-500">Commission 0.1%</span>
              <span className="px-3 py-1 rounded-full ui-card border border-black/5 dark:border-white/5 text-xs text-zinc-500">Slippage 0.05%</span>
              <span className="px-3 py-1 rounded-full ui-card border border-black/5 dark:border-white/5 text-xs text-zinc-500">Long-only</span>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  )
}
