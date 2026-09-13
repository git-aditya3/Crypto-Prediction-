import { useSettingsStore } from '../store/useSettingsStore'
import { useEffect, useState, useMemo } from 'react'
import { BarChart3, TrendingUp, Award, Target, Activity, PieChart } from 'lucide-react'
import { api } from '../api/client'

export default function Analytics() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const safeFixed = (v, d=2) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return (0).toFixed(d)
    return n.toFixed(d)
  }

  const fetchData = async () => {
    try {
      const json = await api.getAnalytics().catch(() => fetch('/api/analytics').then(r => r.json()))
      setData(json)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 15000); return () => clearInterval(i) }, [])

  const metrics = data?.metrics || {}
  const equity = data?.equity_curve || []
  const symbols = data?.symbol_performance || {}

  const equityStats = useMemo(() => {
    if (equity.length === 0) return { min: 0, max: 0, range: 1, initial: 0, current: 0, pct: 0 }
    const values = equity.map(x => x.equity ?? 0)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1
    const initial = values[0] ?? 0
    const current = values[values.length-1] ?? 0
    const pct = initial ? ((current / initial - 1) * 100) : 0
    return { min, max, range, initial, current, pct }
  }, [equity])

  if (loading) return <div className="p-6 text-center">Loading real analytics - live P&L...</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 font-poppins space-y-6">
      <div>
        <h1 className="text-3xl font-black flex items-center gap-3"><BarChart3 className="text-zinc-500" /> Performance Analytics - Real Trading</h1>
        <p className="text-zinc-500 mt-1">Real P&L tracking - win rate, profit factor, Sharpe, equity curve - no fake simulation</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Total Trades</div>
          <div className="text-xl font-black">{metrics.total_trades ?? 0}</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Win Rate</div>
          <div className="text-xl font-black text-emerald-600">{safeFixed(metrics.win_rate,1)}%</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Profit Factor</div>
          <div className="text-xl font-black">{safeFixed(metrics.profit_factor,2)}</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Total P&L</div>
          <div className={`text-xl font-black ${(metrics.total_pnl??0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>${safeFixed(metrics.total_pnl,2)}</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Sharpe</div>
          <div className="text-xl font-black">{safeFixed(metrics.sharpe,2)}</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Sortino</div>
          <div className="text-xl font-black">{safeFixed(metrics.sortino,2)}</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Max DD</div>
          <div className="text-xl font-black text-red-500">{safeFixed(metrics.max_drawdown,1)}%</div>
        </div>
        <div className="p-4 rounded-xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Best Trade</div>
          <div className="text-xl font-black text-emerald-600">${safeFixed(metrics.best_trade,2)}</div>
        </div>
      </div>

      {/* Equity Curve */}
      <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h3 className="font-bold flex items-center gap-2 mb-4"><TrendingUp size={16} /> Equity Curve - Real P&L Growth</h3>
        {equity.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">No equity curve - start trading to see real P&L growth</div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-zinc-500 flex-wrap">
              <span>Initial: ${safeFixed(equityStats.initial,2)}</span>
              <span>→</span>
              <span>Current: ${safeFixed(equityStats.current,2)}</span>
              <span className={`ml-auto font-bold ${equityStats.pct >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {safeFixed(equityStats.pct,2)}%
              </span>
            </div>
            <div className="h-[200px] flex items-end gap-0.5">
              {equity.slice(-100).map((e, i) => {
                const height = (( (e.equity ?? 0) - equityStats.min) / equityStats.range) * 100
                return <div key={i} className="flex-1 bg-gradient-to-t from-emerald-500 to-violet-500 rounded-t" style={{ height: `${Math.max(2, Math.min(100, height))}%` }} title={`$${safeFixed(e.equity,2)} ${e.symbol || ''} ${e.pnl ? `P&L $${safeFixed(e.pnl,2)}` : ''}`} />
              })}
            </div>
            <div className="flex justify-between text-[10px] text-zinc-500">
              <span>{equity.length} trades</span>
              <span>Real trading - no fake simulation</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Symbol Performance */}
        <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <h3 className="font-bold flex items-center gap-2 mb-4"><PieChart size={16} /> Symbol Performance - Real Trading</h3>
          {Object.keys(symbols).length === 0 ? (
            <div className="text-center py-8 text-zinc-500">No symbol performance - trade to see real stats</div>
          ) : (
            <div className="space-y-3">
              {Object.entries(symbols).map(([sym, perf]) => (
                <div key={sym} className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50 flex items-center justify-between">
                  <div>
                    <div className="font-bold">{sym}</div>
                    <div className="text-xs text-zinc-500">{perf.total_trades ?? 0} trades • {perf.wins ?? 0}W / {perf.losses ?? 0}L</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${(perf.total_pnl??0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>${safeFixed(perf.total_pnl,2)}</div>
                    <div className="text-xs text-zinc-500">{safeFixed(perf.win_rate,1)}% win rate</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Portfolio */}
        <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <h3 className="font-bold flex items-center gap-2 mb-4"><Activity size={16} /> Portfolio Summary - Live Binance</h3>
          {data?.portfolio ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
                  <div className="text-xs text-zinc-500">Total Value</div>
                  <div className="text-lg font-bold">${safeFixed(data.portfolio.total_value,2)}</div>
                </div>
                <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
                  <div className="text-xs text-zinc-500">Total P&L</div>
                  <div className={`text-lg font-bold ${(data.portfolio.total_pnl??0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>${safeFixed(data.portfolio.total_pnl,2)}</div>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-black/5 dark:border-white/5">
                <div className="text-xs font-bold text-emerald-600">Real Trading - No Fake</div>
                <div className="text-xs text-zinc-500 mt-1">{data.no_fake || 'Real trading'} • {data.data_source || 'Live Binance'}</div>
              </div>
              {data.portfolio.allocation && Object.keys(data.portfolio.allocation).length>0 && (
                <div>
                  <div className="text-xs text-zinc-500 uppercase mb-2">Allocation</div>
                  <div className="space-y-2">
                    {Object.entries(data.portfolio.allocation).map(([sym, pct]) => {
                      const pctNum = typeof pct === 'number' ? pct : parseFloat(pct) || 0
                      return (
                        <div key={sym} className="flex items-center gap-2">
                          <span className="w-16 text-xs font-medium">{sym}</span>
                          <div className="flex-1 h-1.5 bg-transparent rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500" style={{ width: `${Math.min(100, Math.max(0, pctNum))}%` }}></div>
                          </div>
                          <span className="text-xs text-zinc-500 w-8">{safeFixed(pctNum,0)}%</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">No portfolio data</div>
          )}
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h3 className="font-bold flex items-center gap-2 mb-4"><Award size={16} /> Advanced Metrics - Real Performance</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
            <div className="text-xs text-zinc-500">Avg Win</div>
            <div className="font-bold text-emerald-600">${safeFixed(metrics.avg_win,2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
            <div className="text-xs text-zinc-500">Avg Loss</div>
            <div className="font-bold text-red-500">${safeFixed(metrics.avg_loss,2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
            <div className="text-xs text-zinc-500">Total Wins</div>
            <div className="font-bold text-emerald-600">${safeFixed(metrics.total_wins,2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
            <div className="text-xs text-zinc-500">Total Losses</div>
            <div className="font-bold text-red-500">${safeFixed(metrics.total_losses,2)}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
