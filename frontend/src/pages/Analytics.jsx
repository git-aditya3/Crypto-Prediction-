import { useEffect, useState } from 'react'
import { BarChart3, TrendingUp, Award, Target, Activity, PieChart } from 'lucide-react'

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const res = await fetch('/api/analytics')
      const json = await res.json()
      setData(json)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 15000); return () => clearInterval(i) }, [])

  if (loading) return <div className="p-6 text-center">Loading real analytics - live P&L...</div>

  const metrics = data?.metrics || {}
  const equity = data?.equity_curve || []
  const symbols = data?.symbol_performance || {}

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-black flex items-center gap-3"><BarChart3 className="text-violet-400" /> Performance Analytics - Real Trading</h1>
        <p className="text-crypto-muted mt-1">Real P&L tracking - win rate, profit factor, Sharpe, equity curve - no fake simulation</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Total Trades</div>
          <div className="text-xl font-black">{metrics.total_trades || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Win Rate</div>
          <div className="text-xl font-black text-emerald-400">{metrics.win_rate?.toFixed(1) || 0}%</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Profit Factor</div>
          <div className="text-xl font-black">{metrics.profit_factor?.toFixed(2) || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Total P&L</div>
          <div className={`text-xl font-black ${metrics.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${metrics.total_pnl?.toFixed(2) || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Sharpe</div>
          <div className="text-xl font-black">{metrics.sharpe?.toFixed(2) || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Sortino</div>
          <div className="text-xl font-black">{metrics.sortino?.toFixed(2) || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Max DD</div>
          <div className="text-xl font-black text-red-400">{metrics.max_drawdown?.toFixed(1) || 0}%</div>
        </div>
        <div className="p-4 rounded-xl bg-crypto-card border border-crypto-border">
          <div className="text-[10px] text-crypto-muted uppercase">Best Trade</div>
          <div className="text-xl font-black text-emerald-400">${metrics.best_trade?.toFixed(2) || 0}</div>
        </div>
      </div>

      {/* Equity Curve */}
      <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
        <h3 className="font-bold flex items-center gap-2 mb-4"><TrendingUp size={16} /> Equity Curve - Real P&L Growth</h3>
        {equity.length === 0 ? (
          <div className="text-center py-8 text-crypto-muted">No equity curve - start trading to see real P&L growth</div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-crypto-muted">
              <span>Initial: ${equity[0]?.equity?.toFixed(2)}</span>
              <span>→</span>
              <span>Current: ${equity[equity.length - 1]?.equity?.toFixed(2)}</span>
              <span className={`ml-auto font-bold ${equity[equity.length - 1]?.equity >= equity[0]?.equity ? 'text-emerald-400' : 'text-red-400'}`}>
                {((equity[equity.length - 1]?.equity / equity[0]?.equity - 1) * 100).toFixed(2)}%
              </span>
            </div>
            <div className="h-[200px] flex items-end gap-0.5">
              {equity.slice(-100).map((e, i) => {
                const min = Math.min(...equity.map(x => x.equity))
                const max = Math.max(...equity.map(x => x.equity))
                const range = max - min || 1
                const height = ((e.equity - min) / range) * 100
                return <div key={i} className="flex-1 bg-gradient-to-t from-emerald-500 to-violet-500 rounded-t" style={{ height: `${Math.max(2, height)}%` }} title={`$${e.equity?.toFixed(2)} ${e.symbol || ''} ${e.pnl ? `P&L $${e.pnl.toFixed(2)}` : ''}`} />
              })}
            </div>
            <div className="flex justify-between text-[10px] text-crypto-muted">
              <span>{equity.length} trades</span>
              <span>Real trading - no fake simulation</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Symbol Performance */}
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold flex items-center gap-2 mb-4"><PieChart size={16} /> Symbol Performance - Real Trading</h3>
          {Object.keys(symbols).length === 0 ? (
            <div className="text-center py-8 text-crypto-muted">No symbol performance - trade to see real stats</div>
          ) : (
            <div className="space-y-3">
              {Object.entries(symbols).map(([sym, perf]) => (
                <div key={sym} className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50 flex items-center justify-between">
                  <div>
                    <div className="font-bold">{sym}</div>
                    <div className="text-xs text-crypto-muted">{perf.total_trades} trades • {perf.wins}W / {perf.losses}L</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${perf.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${perf.total_pnl?.toFixed(2)}</div>
                    <div className="text-xs text-crypto-muted">{perf.win_rate?.toFixed(1)}% win rate</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Portfolio */}
        <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
          <h3 className="font-bold flex items-center gap-2 mb-4"><Activity size={16} /> Portfolio Summary - Live Binance</h3>
          {data?.portfolio ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
                  <div className="text-xs text-crypto-muted">Total Value</div>
                  <div className="text-lg font-bold">${data.portfolio.total_value?.toFixed(2)}</div>
                </div>
                <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
                  <div className="text-xs text-crypto-muted">Total P&L</div>
                  <div className={`text-lg font-bold ${data.portfolio.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>${data.portfolio.total_pnl?.toFixed(2)}</div>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <div className="text-xs font-bold text-emerald-400">Real Trading - No Fake</div>
                <div className="text-xs text-crypto-muted mt-1">{data.no_fake} • {data.data_source}</div>
              </div>
              {data.portfolio.allocation && (
                <div>
                  <div className="text-xs text-crypto-muted uppercase mb-2">Allocation</div>
                  <div className="space-y-2">
                    {Object.entries(data.portfolio.allocation).map(([sym, pct]) => (
                      <div key={sym} className="flex items-center gap-2">
                        <span className="w-16 text-xs font-medium">{sym}</span>
                        <div className="flex-1 h-1.5 bg-crypto-bg rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: `${pct}%` }}></div>
                        </div>
                        <span className="text-xs text-crypto-muted w-8">{pct.toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-crypto-muted">No portfolio data</div>
          )}
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="p-5 rounded-2xl bg-crypto-card border border-crypto-border">
        <h3 className="font-bold flex items-center gap-2 mb-4"><Award size={16} /> Advanced Metrics - Real Performance</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
            <div className="text-xs text-crypto-muted">Avg Win</div>
            <div className="font-bold text-emerald-400">${metrics.avg_win?.toFixed(2) || 0}</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
            <div className="text-xs text-crypto-muted">Avg Loss</div>
            <div className="font-bold text-red-400">${metrics.avg_loss?.toFixed(2) || 0}</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
            <div className="text-xs text-crypto-muted">Total Wins</div>
            <div className="font-bold text-emerald-400">${metrics.total_wins?.toFixed(2) || 0}</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border/50">
            <div className="text-xs text-crypto-muted">Total Losses</div>
            <div className="font-bold text-red-400">${metrics.total_losses?.toFixed(2) || 0}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
