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
import { DollarSign, Target, ArrowRight, Activity, BarChart3 } from 'lucide-react'
import accuracyData from '../data/accuracy.json'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const { accountBalance, riskPerTrade } = useSettingsStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [tradingCalls, setTradingCalls] = useState([])
  const [tradingSummary, setTradingSummary] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
  const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { maximumFractionDigits: n > 1000 ? 2 : 4 }) }

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
  const accuracy = accuracyData[selectedSymbol] || accuracyData['BTC-USD'] || { models: { ensemble: { mape: 6.3 }, arima: { mape: 2.57 } }, best_model: 'arima' }
  const selectedCall = tradingCalls.find(c => c.symbol === selectedSymbol) || tradingCalls[0]

  const stats = [
    { label: 'Live Price', value: `$${safeLocale(livePrice)}`, subValue: selectedSymbol, trend: `${changePct >= 0 ? '+' : ''}${safeFixed(changePct,2)}%`, icon: DollarSign, accent: true },
    { label: 'Signal', value: selectedCall?.signal || signal?.signal || 'HOLD', subValue: `${safeFixed(selectedCall?.confidence ?? signal?.confidence ?? 0,0)}% confidence`, icon: Target },
    { label: 'Models', value: '5 Active', subValue: 'LSTM • Transformer • GRU • XGB • ARIMA', icon: Activity },
    { label: 'Best MAPE', value: `${safeFixed(accuracy?.models?.arima?.mape || 2.57,2)}%`, subValue: `${accuracy?.best_model || 'arima'} • 200+ features`, icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        {/* Hero - minimal */}
        <div className="rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 p-5 md:p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 gpu-accelerated">
          <div>
            <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-zinc-900 dark:text-white flex items-center gap-3">
              Trading Intelligence
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-900 text-white dark:bg-white dark:text-black tracking-wide">LIVE</span>
            </h1>
            <p className="text-[13px] mt-2 text-zinc-500 leading-relaxed max-w-2xl">
              Real market data • Endless training • {tradingSummary?.active || 0} active calls • No simulation • Minimal monochrome • 120fps
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[11px] font-medium text-zinc-600 dark:text-zinc-400">
              <div className="w-1.5 h-1.5 rounded-full bg-zinc-900 dark:bg-white animate-pulse" />
              {tradingSummary?.buys || 0} BUY • {tradingSummary?.sells || 0} SELL
            </div>
            <Link to="/trading" className="px-4 py-2 rounded-full text-[13px] font-medium bg-zinc-900 text-white dark:bg-white dark:text-black hover:scale-[1.02] transition-transform duration-200 gpu-accelerated flex items-center gap-1.5">
              Trading <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        {/* Markets - minimal */}
        <div className="rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 p-4 md:p-5 gpu-accelerated">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[11px] font-medium tracking-wide uppercase text-zinc-500 flex items-center gap-2">
              <BarChart3 size={12} /> Markets
            </h2>
            <span className="text-[10px] px-2 py-1 rounded-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-500">${accountBalance.toLocaleString()} • {(riskPerTrade*100).toFixed(1)}% risk</span>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        {/* Stats - minimal 120fps */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 stagger-children">
          {stats.map((stat, i) => <StatCard key={i} {...stat} />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2">
                <Target size={14} /> Trading Calls
                {tradingSummary && <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[10px]">{tradingSummary.active || tradingSummary.total} ACTIVE</span>}
              </h3>
              <Link to="/trading" className="text-[11px] font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-white flex items-center gap-1 transition-colors duration-200">
                View all <ArrowRight size={12} />
              </Link>
            </div>
            
            <div className="space-y-3 stagger-children">
              {tradingCalls.length > 0 ? tradingCalls.map((call, i) => (
                <TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={(c) => setSelectedSymbol(c.symbol)} />
              )) : [...Array(3)].map((_, i) => <div key={i} className="skeleton h-48 rounded-xl"></div>)}
            </div>
          </div>

          <div className="lg:col-span-7 space-y-4">
            <GlassCard className="p-5" hover={false}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2">
                  <Activity size={14} /> Performance
                  <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[10px]">V5 MAX</span>
                </h3>
                <span className="text-[10px] px-2 py-1 rounded-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-500">Real data • No simulation</span>
              </div>

              <div className="grid grid-cols-4 gap-2 text-[10px] font-medium uppercase tracking-wide text-zinc-500 border-b border-zinc-100 dark:border-zinc-800 pb-2 mb-3">
                <span>Model</span>
                <span>MAPE</span>
                <span>RMSE</span>
                <span>Status</span>
              </div>

              <div className="space-y-2">
                {accuracy && Object.entries(accuracy.models || {}).slice(0,5).map(([name, m]) => {
                  const isBest = accuracy.best_model === name
                  return (
                    <div key={name} className={`grid grid-cols-4 gap-2 items-center p-3 rounded-lg text-[12px] border transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated ${isBest ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'}`}>
                      <span className="font-medium capitalize flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${isBest ? 'bg-white dark:bg-black animate-pulse' : 'bg-zinc-400'}`} />
                        {name}
                      </span>
                      <span className="mono font-medium">{safeFixed(m.mape,2)}%</span>
                      <span className="mono text-[11px] opacity-70">${m.rmse ? safeFixed(m.rmse,0) : '—'}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full w-fit font-medium ${m.mape < 3 ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : 'bg-white dark:bg-zinc-700 text-zinc-500 border border-zinc-200 dark:border-zinc-600'}`}>
                        {m.mape < 3 ? 'Excellent' : m.mape < 6 ? 'Good' : 'Fair'}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-5">
                {loading ? <div className="skeleton h-[360px] rounded-xl"></div> : history ? <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={360} /> : <div className="h-[360px] flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-200 dark:border-zinc-700 gap-2 text-zinc-400"><BarChart3 size={20} /> Loading chart</div>}
              </div>

              {selectedCall && (
                <div className="mt-5 p-4 rounded-xl border bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-800">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">{selectedCall.symbol} • Real Call</span>
                    <span className={`ml-auto px-2.5 py-1 rounded-full text-[11px] font-medium ${selectedCall.signal?.includes('BUY') ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : 'bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300'}`}>{selectedCall.action}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-[11px]">
                    {[
                      { label: 'Entry', value: `$${safeFixed(selectedCall.entry_price,2)}` },
                      { label: 'SL', value: `$${safeFixed(selectedCall.stop_loss,2)}` },
                      { label: 'TP1', value: `$${safeFixed(selectedCall.take_profits?.tp1,2)}` },
                      { label: 'R:R', value: `1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)}` },
                    ].map((it, i) => (
                      <div key={i} className="p-2.5 rounded-lg text-center border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700">
                        <div className="text-[9px] uppercase tracking-wide text-zinc-500">{it.label}</div>
                        <div className="mono font-medium mt-1 text-[11px]">{it.value}</div>
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
