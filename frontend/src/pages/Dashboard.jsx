import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import PriceChart from '../components/PriceChart'
import AssetGrid from '../components/AssetGrid'
import GlassCard, { StatCard } from '../components/GlassCard'
import TradingCallCard from '../components/TradingCallCard'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { DollarSign, Award, Target, ArrowRight, Shield, GraduationCap, BarChart3 } from 'lucide-react'
import accuracyData from '../data/accuracy.json'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const { accountBalance, riskPerTrade, theme } = useSettingsStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [tradingCalls, setTradingCalls] = useState([])
  const [tradingSummary, setTradingSummary] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  const isDark = theme === 'dark'
  const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
  const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: n > 1000 ? 2 : 4 }) }

  useEffect(() => { fetchAllTickers() }, [])

  useEffect(() => {
    setLoading(true)
    const loadData = async () => {
      try {
        const [h, f, s, calls, train] = await Promise.all([
          api.getHistory(selectedSymbol, '1y').catch(() => null),
          api.getForecast(selectedSymbol, 7).catch(() => null),
          api.getSignal(selectedSymbol).catch(() => null),
          api.getTradingCalls({ accountBalance, riskPerTrade }).catch(() => null),
          api.getTrainingStatus().catch(() => null),
        ])
        if (h) setHistory(h)
        else {
          try {
            const k = await fetchKlines(selectedSymbol, '1d', 200)
            setHistory({ dates: k.map(x => x.time), open: k.map(x => x.open), high: k.map(x => x.high), low: k.map(x => x.low), close: k.map(x => x.close), volume: k.map(x => x.volume) })
          } catch {}
        }
        if (f) setForecast(f)
        if (s) setSignal(s)
        if (calls) { setTradingCalls(calls.calls?.slice(0, 3) || []); setTradingSummary(calls.summary || null) }
        if (train) setTrainingStatus(train.status || train)
      } catch (e) { console.error(e) } finally { setLoading(false) }
    }
    loadData()
  }, [selectedSymbol])

  const currentTicker = tickers[selectedSymbol]
  const livePrice = prices[selectedSymbol] || currentTicker?.price || history?.close?.[history.close.length - 1] || 0
  const prevPrice = history?.close?.[history.close.length - 2] || livePrice
  const changePct = prevPrice ? ((livePrice - prevPrice) / prevPrice * 100) : 0
  const isPositive = changePct >= 0
  const accuracy = accuracyData[selectedSymbol] || accuracyData['BTC-USD'] || { models: { ensemble: { mape: 6.3 }, arima: { mape: 2.57 } }, best_model: 'arima' }
  const selectedCall = tradingCalls.find(c => c.symbol === selectedSymbol) || tradingCalls[0]

  const stats = [
    { label: 'Live Price', value: `$${safeLocale(livePrice)}`, subValue: selectedSymbol, trend: `${isPositive ? '+' : ''}${safeFixed(changePct,2)}%`, icon: DollarSign },
    { label: 'Signal', value: selectedCall?.signal || signal?.signal || 'HOLD', subValue: `${safeFixed(selectedCall?.confidence ?? signal?.confidence ?? 0,0)}% confidence`, icon: Target },
    { label: 'Training', value: trainingStatus?.is_running ? 'Active' : 'Ready', subValue: `${trainingStatus?.total_trainings || 0} runs`, icon: GraduationCap },
    { label: 'Best Model', value: `${safeFixed(accuracy?.models?.arima?.mape || 2.57,2)}%`, subValue: `MAPE • ${accuracy?.best_model || 'arima'}`, icon: Award },
  ]

  return (
    <div className={`min-h-screen font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="ui-card p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className={`text-2xl md:text-3xl font-bold tracking-tight flex items-center gap-3 ${isDark ? 'text-white' : 'text-black'}`}>
              Real Trading Intelligence
              <span className="ui-pill-live px-3 py-1 text-[10px]">LIVE • REAL MONEY</span>
            </h1>
            <p className={`text-[13px] mt-2 max-w-3xl ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Live Binance prices • Models train endlessly • ARIMA 2.57% MAPE • {tradingSummary?.active || 0} active calls • No simulation
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] ${isDark ? 'bg-zinc-900 border-white/5 text-zinc-400' : 'bg-zinc-50 border-black/5 text-zinc-500'}`}>
              <div className="live-dot"></div> {tradingSummary?.buys || 0} BUY • {tradingSummary?.sells || 0} SELL
            </div>
            <Link to="/trading" className={`px-4 py-2.5 rounded-xl text-[12px] font-bold flex items-center gap-1.5 ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}>
              <Target size={14} /> Trading Calls <ArrowRight size={12} />
            </Link>
          </div>
        </div>

        <div className="ui-card p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className={`text-[11px] font-bold tracking-widest uppercase flex items-center gap-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
              <BarChart3 size={14} /> Markets • Live • Click to Analyze
            </h2>
            <span className="ui-pill text-[10px]">Account ${accountBalance} • Risk {(riskPerTrade||0.02)*100}%</span>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => <StatCard key={i} {...stat} />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className={`font-semibold flex items-center gap-2 text-[14px] ${isDark ? 'text-white' : 'text-black'}`}>
                <Target size={16} /> Trading Calls {tradingSummary && <span className="ui-pill text-[10px]">{tradingSummary.active || tradingSummary.total}</span>}
              </h3>
              <Link to="/trading" className={`text-[11px] font-semibold flex items-center gap-1 ${isDark ? 'text-zinc-400 hover:text-white' : 'text-zinc-500 hover:text-black'}`}>View all <ArrowRight size={12} /></Link>
            </div>
            {tradingCalls.length > 0 ? tradingCalls.map((call, i) => (
              <TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={(c) => setSelectedSymbol(c.symbol)} />
            )) : [...Array(3)].map((_, i) => <div key={i} className="shimmer h-48 rounded-[20px]"></div>)}

            <Link to="/training" className="block ui-card p-4 hover:translate-y-[-1px] transition-transform">
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}><GraduationCap size={16} /></div>
                <div className="flex-1">
                  <div className={`font-semibold text-[13px] flex items-center gap-2 ${isDark ? 'text-white' : 'text-black'}`}>Continuous Training {trainingStatus?.is_running && <span className="ui-pill-live text-[9px]">LIVE</span>}</div>
                  <div className={`text-[11px] ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>{trainingStatus?.total_trainings || 0} trainings • Retrain every 12h</div>
                </div>
                <ArrowRight size={14} className={isDark ? 'text-zinc-500' : 'text-zinc-400'} />
              </div>
            </Link>
          </div>

          <div className="lg:col-span-7">
            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`font-semibold flex items-center gap-2 text-[14px] ${isDark ? 'text-white' : 'text-black'}`}><Award size={16} /> Model Performance</h3>
                <span className="ui-pill text-[10px]">Real data • No simulation</span>
              </div>

              <div className={`grid grid-cols-4 gap-2 text-[10px] font-bold uppercase border-b pb-2 mb-3 ${isDark ? 'text-zinc-500 border-white/5' : 'text-zinc-400 border-black/5'}`}>
                <span>Model</span><span>MAPE</span><span>RMSE</span><span>Status</span>
              </div>

              <div className="space-y-2">
                {accuracy && Object.entries(accuracy.models || {}).slice(0,5).map(([name, m]) => {
                  const isBest = accuracy.best_model === name
                  return (
                    <div key={name} className={`grid grid-cols-4 gap-2 items-center p-3 rounded-xl text-[13px] ${isBest ? (isDark ? 'bg-white text-black' : 'bg-black text-white') : (isDark ? 'bg-zinc-900' : 'bg-zinc-50')}`}>
                      <span className="font-semibold capitalize flex items-center gap-1.5"><span className={`w-1.5 h-1.5 rounded-full ${isBest ? 'bg-emerald-500' : 'bg-zinc-400'}`}></span>{name} {isBest && '★'}</span>
                      <span className="mono font-bold">{safeFixed(m.mape,2)}%</span>
                      <span className="mono text-[12px] opacity-70">${m.rmse ? safeFixed(m.rmse,0) : '—'}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full w-fit font-bold ${m.mape < 3 ? 'ui-pill-buy' : m.mape < 6 ? 'ui-pill' : 'ui-pill-sell'}`}>{m.mape < 3 ? 'Excellent' : m.mape < 6 ? 'Good' : 'Fair'}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-5">
                {loading ? <div className="shimmer h-[380px] rounded-[16px]"></div> : history ? <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={380} /> : <div className={`h-[380px] flex items-center justify-center rounded-xl border ${isDark ? 'border-white/5 text-zinc-500' : 'border-black/5 text-zinc-400'}`}>Loading chart...</div>}
              </div>

              {selectedCall && (
                <div className={`mt-5 p-4 rounded-xl border ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Shield size={14} className="text-emerald-500" />
                    <span className={`text-[11px] font-bold uppercase ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{selectedCall.symbol} • Real Trading Call</span>
                    <span className={`ml-auto px-2 py-0.5 rounded-full text-[10px] font-bold ${selectedCall.signal?.includes('BUY') ? 'ui-pill-buy' : 'ui-pill-sell'}`}>{selectedCall.action}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-[11px]">
                    {[
                      { label: 'Entry', value: `$${safeFixed(selectedCall.entry_price,2)}` },
                      { label: 'SL', value: `$${safeFixed(selectedCall.stop_loss,2)}` },
                      { label: 'TP1', value: `$${safeFixed(selectedCall.take_profits?.tp1,2)}` },
                      { label: 'R:R', value: `1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)}` },
                    ].map((it, i) => (
                      <div key={i} className={`p-2.5 rounded-xl text-center ${isDark ? 'bg-black border border-white/5' : 'bg-white border border-black/5'}`}>
                        <div className={`text-[9px] uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{it.label}</div>
                        <div className="mono font-bold mt-0.5">{it.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
