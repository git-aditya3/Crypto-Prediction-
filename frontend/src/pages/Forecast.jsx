import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import { useMarketStore } from '../store/useMarketStore'
import PriceChart from '../components/PriceChart'
import GlassCard from '../components/GlassCard'
import { TrendingUp, Zap, BarChart3, Target } from 'lucide-react'

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
            <h1 className="text-[20px] font-semibold tracking-tight text-zinc-900 dark:text-white flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center"><TrendingUp size={14} /></span>
              Forecast
              <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[10px] font-medium">ENSEMBLE</span>
            </h1>
            <p className="text-[12px] mt-1 text-zinc-500">LSTM • Transformer • XGBoost • ARIMA • Minimal • 120fps</p>
          </div>
          <div className="flex items-center gap-2">
            <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="rounded-full border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 px-3 py-1.5 text-[12px] font-medium text-zinc-900 dark:text-white">
              {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD','AVAX-USD'].map(s => <option key={s}>{s}</option>)}
            </select>
            <select value={steps} onChange={e => setSteps(parseInt(e.target.value))} className="rounded-full border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 px-3 py-1.5 text-[12px] font-medium">
              {[7,14,21,30].map(n => <option key={n} value={n}>{n}d</option>)}
            </select>
            <button onClick={load} className="px-3 py-1.5 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-black text-[12px] font-medium flex items-center gap-1.5 hover:scale-105 transition-transform duration-200 gpu-accelerated">
              <Zap size={12} /> Refresh
            </button>
          </div>
        </div>

        {history && forecast && <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={420} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2">
                  <BarChart3 size={14} /> Forecast {steps}d • ${ (forecast?.current_price ?? livePrice ?? 0).toFixed(2)}
                </h3>
                <div className="flex gap-1 p-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                  {['ensemble','transformer','lstm','xgboost','arima'].map(m => (
                    <button key={m} onClick={() => setActiveModel(m)} className={`px-2.5 py-1 rounded-full text-[10px] font-medium uppercase transition-all duration-200 ${activeModel === m ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-white'}`}>{m}</button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                {chartData.slice(0, 7).map((row, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated">
                    <div>
                      <div className="text-[12px] font-medium text-zinc-900 dark:text-white">{row.fullDate}</div>
                      <div className="text-[10px] text-zinc-500">Day {i+1}</div>
                    </div>
                    <div className="text-right">
                      <div className="mono font-medium text-[12px] text-zinc-900 dark:text-white">${(row[activeModel] ?? row.ensemble ?? 0).toFixed(2)}</div>
                      <div className="text-[11px] mono text-zinc-500">{(((row.ensemble ?? 0) - (livePrice||1)) / (livePrice||1) * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
          <div className="space-y-4">
            <GlassCard className="p-5">
              <h3 className="font-medium text-[13px] text-zinc-900 dark:text-white mb-3 flex items-center gap-2"><Target size={14} /> Weights</h3>
              <div className="space-y-3">
                {[
                  { name: 'Transformer', weight: 35 },
                  { name: 'LSTM', weight: 35 },
                  { name: 'XGBoost', weight: 20 },
                  { name: 'ARIMA', weight: 10 },
                ].map(m => (
                  <div key={m.name} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-[11px] mb-1"><span className="font-medium text-zinc-700 dark:text-zinc-300">{m.name}</span><span className="font-medium mono text-zinc-900 dark:text-white">{m.weight}%</span></div>
                      <div className="h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden"><div className="h-full bg-zinc-900 dark:bg-white rounded-full transition-all duration-700" style={{ width: `${m.weight}%` }} /></div>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
