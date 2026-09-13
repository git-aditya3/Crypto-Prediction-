import { useSettingsStore } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import { useMarketStore } from '../store/useMarketStore'
import PriceChart from '../components/PriceChart'
import GlassCard from '../components/GlassCard'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { TrendingUp, Brain, Zap, Target, Clock, BarChart3 } from 'lucide-react'

export default function Forecast() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

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
            return {
              dates: k.map(x => x.time),
              open: k.map(x => x.open),
              high: k.map(x => x.high),
              low: k.map(x => x.low),
              close: k.map(x => x.close),
              volume: k.map(x => x.volume),
            }
          } catch { return null }
        })
      ])
      if (f) setForecast(f)
      if (h) setHistory(h)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [selectedSymbol, steps])

  const chartData = forecast?.dates?.map((d, i) => ({
    date: d.slice(5),
    fullDate: d,
    lstm: forecast.lstm?.[i],
    transformer: forecast.transformer?.[i],
    xgboost: forecast.xgboost?.[i],
    arima: forecast.arima?.[i],
    ensemble: forecast.ensemble?.[i]
  })) || []

  const livePrice = prices[selectedSymbol] || forecast?.current_price || 0

  return (
    <div className={`min-h-screen relative font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>

      
      
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-black dark:bg-white flex items-center justify-center shadow-lg">
                <TrendingUp size={20} className="text-black" />
              </span>
              <span className="text-white">AI Forecast</span>
              <span className="px-3 py-1 rounded-full bg-crypto-accent2/10 border border-crypto-accent2/20 text-zinc-900 dark:text-white text-xs font-bold tracking-widest">ENSEMBLE</span>
            </h1>
            <p className="text-zinc-500 text-sm mt-2">Multi-model predictions • LSTM + Transformer TFT + XGBoost + ARIMA • Weighted ensemble</p>
          </div>
          
          <div className="flex items-center gap-2">
            <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="ui-card border border-black/5 dark:border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-white">
              {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD','AVAX-USD'].map(s => <option key={s}>{s}</option>)}
            </select>
            <select value={steps} onChange={e => setSteps(parseInt(e.target.value))} className="ui-card border border-black/5 dark:border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-white">
              {[7,14,21,30].map(n => <option key={n} value={n}>{n} days</option>)}
            </select>
            <button onClick={load} className="btn-primary flex items-center gap-2">
              <Zap size={14} /> Refresh
            </button>
          </div>
        </div>

        {history && forecast && (
          <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={460} />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <BarChart3 size={18} className="text-zinc-900 dark:text-white" />
                  Forecast Comparison ({steps} days) • Current: ${(forecast?.current_price ?? livePrice ?? 0).toFixed(2)}
                </h3>
                <div className="flex gap-1 p-1 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                  {['ensemble','transformer','lstm','xgboost','arima'].map(m => (
                    <button
                      key={m}
                      onClick={() => setActiveModel(m)}
                      className={`px-3 py-1 rounded-lg text-xs font-bold uppercase transition ${activeModel === m ? 'bg-white text-black' : 'text-zinc-500 hover:text-white'}`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
              
              {loading ? (
                <div className="h-[400px] flex items-center justify-center">
                  <div className="text-zinc-500">Loading forecast...</div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="ensembleGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d395" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00d395" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#475569" fontSize={11} />
                    <YAxis stroke="#475569" fontSize={11} domain={['auto','auto']} />
                    <Tooltip 
                      contentStyle={{ background: '#10161f', border: '1px solid #1e2a3a', borderRadius: '12px' }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="ensemble" stroke="#00d395" fill="url(#ensembleGrad)" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="transformer" stroke="#6366f1" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                    <Line type="monotone" dataKey="lstm" stroke="#06b6d4" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="xgboost" stroke="#8b5cf6" strokeWidth={1} dot={false} />
                    <Line type="monotone" dataKey="arima" stroke="#64748b" strokeWidth={1} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </GlassCard>
          </div>

          <div className="space-y-6">
            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <Target size={16} className="text-zinc-900 dark:text-white" />
                Prediction Details
              </h3>
              {forecast ? (
                <div className="space-y-3">
                  {chartData.slice(0, 7).map((row, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-transparent/40 border border-black/5 dark:border-white/5/20 hover:border-black/5 dark:border-white/5/40 transition">
                      <div>
                        <div className="text-xs font-bold text-white">{row.fullDate}</div>
                        <div className="text-[11px] text-zinc-500">Day {i+1}</div>
                      </div>
                      <div className="text-right">
                        <div className="mono font-bold text-sm text-white">${(row[activeModel] ?? row.ensemble ?? 0).toFixed(2)}</div>
                        <div className={`text-xs font-bold ${row.ensemble > livePrice ? 'text-emerald-600' : 'text-red-500'}`}>
                          {(((row.ensemble ?? 0) - (livePrice||1)) / (livePrice||1) * 100).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-zinc-500 text-sm">No forecast data</div>
              )}
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                <Brain size={16} className="text-zinc-900 dark:text-white" />
                Model Weights
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'Transformer TFT', weight: 35, color: 'from-black to-black' },
                  { name: 'LSTM', weight: 35, color: 'from-zinc-700 to-zinc-900' },
                  { name: 'XGBoost', weight: 20, color: 'from-zinc-600 to-zinc-800' },
                  { name: 'ARIMA', weight: 10, color: 'from-zinc-400 to-zinc-600' },
                ].map(m => (
                  <div key={m.name} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-medium text-white">{m.name}</span>
                        <span className="font-bold text-white">{m.weight}%</span>
                      </div>
                      <div className="h-1.5 bg-transparent rounded-full overflow-hidden">
                        <div className={`h-full bg-gradient-to-r ${m.color} rounded-full`} style={{ width: `${m.weight}%` }}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 rounded-xl bg-crypto-accent/5 border border-crypto-accent/10">
                <div className="text-xs text-zinc-500 leading-relaxed">
                  <span className="text-white font-medium">Ensemble:</span> Weighted average of all models. Transformer excels at long-range dependencies, LSTM at sequential patterns, XGBoost at feature importance, ARIMA as statistical baseline.
                </div>
              </div>
            </GlassCard>
          </div>
        </div>

        {forecast && (
          <GlassCard className="p-6">
            <h3 className="font-bold text-white mb-4">Detailed Forecast Table • {steps} Days</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[11px] font-bold tracking-widest text-zinc-500 uppercase border-b border-black/5 dark:border-white/5/30">
                    <th className="text-left p-3">Date</th>
                    <th className="text-right p-3">LSTM</th>
                    <th className="text-right p-3">Transformer</th>
                    <th className="text-right p-3">XGBoost</th>
                    <th className="text-right p-3">ARIMA</th>
                    <th className="text-right p-3">Ensemble</th>
                    <th className="text-right p-3">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((row, i) => {
                    const change = (((row.ensemble ?? 0) - (livePrice||1)) / (livePrice||1) * 100)
                    return (
                      <tr key={i} className="border-b border-black/5 dark:border-white/5/20 hover:ui-card/30 transition">
                        <td className="p-3 font-medium text-white">{row.fullDate}</td>
                        <td className="p-3 text-right mono text-zinc-500">${row.lstm != null ? row.lstm.toFixed(2) : '-'}</td>
                        <td className="p-3 text-right mono text-zinc-900 dark:text-white">${row.transformer != null ? row.transformer.toFixed(2) : '-'}</td>
                        <td className="p-3 text-right mono text-zinc-500">${row.xgboost != null ? row.xgboost.toFixed(2) : '-'}</td>
                        <td className="p-3 text-right mono text-gray-400">${row.arima != null ? row.arima.toFixed(2) : '-'}</td>
                        <td className="p-3 text-right mono font-bold text-zinc-900 dark:text-white">${row.ensemble != null ? row.ensemble.toFixed(2) : '-'}</td>
                        <td className={`p-3 text-right mono font-bold ${change >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  )
}
