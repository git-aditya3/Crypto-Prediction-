import { useState } from 'react'
import { api } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Backtest() {
  const [symbol, setSymbol] = useState('BTC-USD')
  const [strategy, setStrategy] = useState('ma')
  const [result, setResult] = useState(null)
  const [compare, setCompare] = useState(null)
  const [loading, setLoading] = useState(false)

  const runBacktest = async () => {
    setLoading(true)
    try {
      const res = await api.backtest({ symbol, strategy, period: '1y', initial_capital: 10000 })
      setResult(res)
    } catch (e) {
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  const runCompare = async () => {
    setLoading(true)
    try {
      const res = await api.backtestCompare(symbol)
      setCompare(res.comparison)
    } catch (e) {
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Backtesting Engine</h1>

      <div className="card">
        <div className="flex gap-3 items-end">
          <div>
            <label className="text-xs text-gray-400">Symbol</label>
            <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="block bg-crypto-bg border border-crypto-border rounded-lg px-3 py-2 mt-1">
              {['BTC-USD','ETH-USD','SOL-USD'].map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400">Strategy</label>
            <select value={strategy} onChange={e=>setStrategy(e.target.value)} className="block bg-crypto-bg border border-crypto-border rounded-lg px-3 py-2 mt-1">
              <option value="ma">Moving Average (20/50)</option>
              <option value="rsi">RSI (30/70)</option>
              <option value="ensemble">Ensemble Signal (Pred+Sentiment+RSI)</option>
              <option value="prediction">Prediction Based</option>
            </select>
          </div>
          <button onClick={runBacktest} disabled={loading} className="btn-primary h-10">{loading ? 'Running...' : 'Run Backtest'}</button>
          <button onClick={runCompare} disabled={loading} className="btn-secondary h-10">Compare All</button>
        </div>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <div className="card"><div className="text-gray-400 text-sm">Total Return</div><div className={`text-2xl font-bold ${result.metrics.total_return_pct>=0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>{result.metrics.total_return_pct.toFixed(2)}%</div></div>
            <div className="card"><div className="text-gray-400 text-sm">Sharpe</div><div className="text-2xl font-bold mono">{result.metrics.sharpe_ratio.toFixed(2)}</div></div>
            <div className="card"><div className="text-gray-400 text-sm">Max DD</div><div className="text-2xl font-bold text-crypto-bear">{result.metrics.max_drawdown_pct.toFixed(2)}%</div></div>
            <div className="card"><div className="text-gray-400 text-sm">Win Rate</div><div className="text-2xl font-bold">{result.metrics.win_rate_pct.toFixed(1)}% ({result.metrics.num_trades} trades)</div></div>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-3">Equity Curve - {result.strategy}</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={result.equity_curve}>
                <XAxis dataKey="date" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip contentStyle={{background:'#151a21', border:'1px solid #232a34'}} />
                <Line type="monotone" dataKey="equity" stroke="#00d395" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold mb-3">Metrics</h3>
              <div className="space-y-1 text-sm">
                {Object.entries(result.metrics).map(([k,v])=>(
                  <div key={k} className="flex justify-between"><span className="text-gray-400">{k}</span><span className="mono">{typeof v==='number' ? v.toFixed(2) : v}</span></div>
                ))}
              </div>
            </div>
            <div className="card">
              <h3 className="font-semibold mb-3">Trades ({result.trades.length})</h3>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="text-gray-400"><tr><th>Entry</th><th>Exit</th><th>PnL</th></tr></thead>
                  <tbody>
                    {result.trades.slice(-10).map((t,i)=>(
                      <tr key={i} className="border-t border-crypto-border/50"><td>{t.entry_date?.slice(0,10)}</td><td>{t.exit_date?.slice(0,10)}</td><td className={t.pnl>=0 ? 'text-crypto-bull' : 'text-crypto-bear'}>${t.pnl?.toFixed(2)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {compare && (
        <div className="card">
          <h3 className="font-semibold mb-3">Strategy Comparison</h3>
          <table className="w-full text-sm">
            <thead className="text-gray-400 border-b border-crypto-border"><tr><th className="text-left p-2">Strategy</th><th>Return</th><th>Sharpe</th><th>DD</th><th>Win Rate</th><th>Trades</th></tr></thead>
            <tbody>
              {Object.entries(compare).map(([name, m])=>(
                <tr key={name} className="border-b border-crypto-border/30">
                  <td className="p-2 font-medium">{name}</td>
                  <td className={`p-2 ${m.total_return_pct>=0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>{m.total_return_pct.toFixed(2)}%</td>
                  <td className="p-2 mono">{m.sharpe_ratio.toFixed(2)}</td>
                  <td className="p-2 text-crypto-bear">{m.max_drawdown_pct.toFixed(2)}%</td>
                  <td className="p-2">{m.win_rate_pct.toFixed(1)}%</td>
                  <td className="p-2">{m.num_trades}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
