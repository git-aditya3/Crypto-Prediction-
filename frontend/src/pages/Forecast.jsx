import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import { useMarketStore } from '../store/useMarketStore'
import PriceChart from '../components/PriceChart'
import GlassCard from '../components/GlassCard'
import { TrendingUp, Zap, BarChart3, Target, Brain } from 'lucide-react'

export default function Forecast() {
  const { selectedSymbol, setSelectedSymbol, prices } = useMarketStore()
  const [steps, setSteps] = useState(7)
  const [forecast, setForecast] = useState(null)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeModel, setActiveModel] = useState('ensemble')

  const load = async () => {
    setLoading(true)
    try {
      const [f, h] = await Promise.all([
        api.getForecast(selectedSymbol, steps).catch(() => null),
        api.getHistory(selectedSymbol, '1y').catch(async () => {
          try {
            const k = await fetchKlines(selectedSymbol, '1d', 200)
            return { dates: k.map(x => x.time), open: k.map(x => x.open), high: k.map(x => x.high), low: k.map(x => x.low), close: k.map(x => x.close), volume: k.map(x => x.volume) }
          } catch { return null }
        })
      ])
      if (f) setForecast(f)
      if (h) setHistory(h)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [selectedSymbol, steps])

  const chartData = forecast?.dates?.map((d, i) => ({
    date: d.slice(5), fullDate: d,
    lstm: forecast.lstm?.[i], transformer: forecast.transformer?.[i], xgboost: forecast.xgboost?.[i], arima: forecast.arima?.[i], ensemble: forecast.ensemble?.[i]
  })) || []

  const livePrice = prices[selectedSymbol] || forecast?.current_price || 0

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-[20px] font-semibold tracking-tight text-[var(--text)] flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]"><TrendingUp size={14} /></span>
              Forecast
              <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-sm">ENSEMBLE</span>
              <span className="hidden md:inline-flex px-2 py-0.5 rounded-full bg-[var(--buy-soft)] text-[var(--buy)] border border-[var(--buy-border)] text-[10px] font-medium">AI • 5 models</span>
            </h1>
            <p className="text-[12px] mt-1 text-[var(--text-muted)]">LSTM • Transformer • XGBoost • ARIMA • Themed • 120fps</p>
          </div>
          <div className="flex items-center gap-2">
            <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="rounded-full border bg-[var(--card)] border-[var(--border)] px-3 py-1.5 text-[12px] font-medium text-[var(--text)]">
              {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD','AVAX-USD'].map(s => <option key={s}>{s}</option>)}
            </select>
            <select value={steps} onChange={e => setSteps(parseInt(e.target.value))} className="rounded-full border bg-[var(--card)] border-[var(--border)] px-3 py-1.5 text-[12px] font-medium">
              {[7,14,21,30].map(n => <option key={n} value={n}>{n}d</option>)}
            </select>
            <button onClick={load} className="px-3 py-1.5 rounded-full bg-[var(--accent)] text-white text-[12px] font-medium flex items-center gap-1.5 hover:scale-105 shadow-[var(--glow)] transition-all duration-200 gpu-accelerated">
              <Zap size={12} /> Refresh
            </button>
          </div>
        </div>

        {history && forecast && <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={420} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h3 className="font-medium text-[13px] tracking-tight text-[var(--text)] flex items-center gap-2">
                  <BarChart3 size={14} className="text-[var(--accent)]" /> Forecast {steps}d • ${ (forecast?.current_price ?? livePrice ?? 0).toFixed(2)}
                </h3>
                <div className="flex gap-1 p-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)]">
                  {['ensemble','transformer','lstm','xgboost','arima'].map(m => (
                    <button key={m} onClick={() => setActiveModel(m)} className={`px-2.5 py-1 rounded-full text-[10px] font-medium uppercase transition-all duration-200 ${activeModel === m ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text)]'}`}>{m}</button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                {chartData.slice(0, 7).map((row, i) => {
                  const change = ((row.ensemble ?? 0) - (livePrice||1)) / (livePrice||1) * 100
                  return (
                    <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[var(--border-strong)] transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated">
                      <div>
                        <div className="text-[12px] font-medium text-[var(--text)]">{row.fullDate}</div>
                        <div className="text-[10px] text-[var(--text-muted)]">Day {i+1}</div>
                      </div>
                      <div className="text-right">
                        <div className="mono font-medium text-[12px] text-[var(--text)]">${(row[activeModel] ?? row.ensemble ?? 0).toFixed(2)}</div>
                        <div className={`text-[11px] mono font-medium ${change >= 0 ? 'text-[var(--buy)]' : 'text-[var(--sell)]'}`}>{change >= 0 ? '+' : ''}{change.toFixed(1)}%</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </GlassCard>
          </div>
          <div className="space-y-4">
            <GlassCard className="p-5">
              <h3 className="font-medium text-[13px] text-[var(--text)] mb-3 flex items-center gap-2"><Target size={14} className="text-[var(--accent)]" /> Weights</h3>
              <div className="space-y-3">
                {[
                  { name: 'Transformer', weight: 35, color: 'var(--accent)' },
                  { name: 'LSTM', weight: 35, color: 'var(--buy)' },
                  { name: 'XGBoost', weight: 20, color: 'var(--text-muted)' },
                  { name: 'ARIMA', weight: 10, color: 'var(--text-faint)' },
                ].map(m => (
                  <div key={m.name} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-[11px] mb-1"><span className="font-medium text-[var(--text-sec)]">{m.name}</span><span className="font-medium mono text-[var(--text)]">{m.weight}%</span></div>
                      <div className="h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden"><div className="h-full rounded-full transition-all duration-700" style={{ width: `${m.weight}%`, background: m.color }} /></div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 rounded-lg bg-[var(--accent-soft)] border border-[var(--border)]">
                <div className="text-[11px] text-[var(--text-sec)] leading-relaxed">
                  <span className="font-medium text-[var(--text)] flex items-center gap-1"><Brain size={10} className="text-[var(--accent)]" /> Ensemble:</span> Weighted average of all models. Themed colors adapt to selected theme.
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
