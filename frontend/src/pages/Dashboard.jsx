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
import { DollarSign, Target, ArrowRight, Activity, BarChart3, Zap, Sparkles } from 'lucide-react'
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
        {/* Hero - themed */}
        <div className="rounded-xl border bg-[var(--card)] border-[var(--border)] p-5 md:p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 gpu-accelerated relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent-soft)] via-transparent to-transparent pointer-events-none" />
          <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/5 rounded-full blur-3xl -translate-y-32 translate-x-32 pointer-events-none" />
          <div className="relative z-10">
            <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--text)] flex items-center gap-3">
              Trading Intelligence
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[var(--accent)] text-white shadow-[var(--glow)] tracking-wide animate-pulse">LIVE</span>
              <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[10px] font-medium text-[var(--accent)]"><Zap size={10} /> Real Money</span>
            </h1>
            <p className="text-[13px] mt-2 text-[var(--text-sec)] leading-relaxed max-w-2xl flex items-center gap-2 flex-wrap">
              <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--buy)] animate-pulse" /> Live Binance + CoinDCX</span>
              <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
              <span>{tradingSummary?.active || 0} active calls</span>
              <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
              <span className="flex items-center gap-1"><Sparkles size={10} className="text-[var(--accent)]" /> 182 features</span>
              <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
              <span>No simulation</span>
            </p>
          </div>
          <div className="flex items-center gap-2 relative z-10">
            <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] font-medium text-[var(--text-sec)]">
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[var(--buy)] animate-pulse" /> {tradingSummary?.buys || 0} BUY</span>
              <span className="w-px h-3 bg-[var(--border)]" />
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[var(--sell)] animate-pulse" /> {tradingSummary?.sells || 0} SELL</span>
            </div>
            <Link to="/trading" className="px-4 py-2 rounded-full text-[13px] font-medium bg-[var(--accent)] text-white shadow-[var(--glow)] hover:shadow-[var(--shadow-md)] hover:scale-[1.02] transition-all duration-200 gpu-accelerated flex items-center gap-1.5">
              Trading <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        <div className="rounded-xl border bg-[var(--card)] border-[var(--border)] p-4 md:p-5 gpu-accelerated">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[11px] font-medium tracking-wide uppercase text-[var(--text-muted)] flex items-center gap-2">
              <BarChart3 size={12} className="text-[var(--accent)]" /> Markets • Live
            </h2>
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-muted)]">${accountBalance.toLocaleString()} • {(riskPerTrade*100).toFixed(1)}% risk • {theme}</span>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 stagger-children">
          {stats.map((stat, i) => <StatCard key={i} {...stat} />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-[13px] tracking-tight text-[var(--text)] flex items-center gap-2">
                <Target size={14} className="text-[var(--accent)]" /> Trading Calls
                {tradingSummary && <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-sm">{tradingSummary.active || tradingSummary.total} ACTIVE</span>}
              </h3>
              <Link to="/trading" className="text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1 transition-colors duration-200">
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
            <GlassCard className="p-5" hover={false} glow>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[13px] tracking-tight text-[var(--text)] flex items-center gap-2">
                  <Activity size={14} className="text-[var(--accent)]" /> Performance
                  <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-sm">V5 MAX</span>
                </h3>
                <span className="text-[10px] px-2.5 py-1 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[var(--accent)] font-medium">Real data • No simulation</span>
              </div>

              <div className="grid grid-cols-4 gap-2 text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)] border-b border-[var(--border)] pb-2 mb-3">
                <span>Model</span>
                <span>MAPE</span>
                <span>RMSE</span>
                <span>Status</span>
              </div>

              <div className="space-y-2">
                {accuracy && Object.entries(accuracy.models || {}).slice(0,5).map(([name, m]) => {
                  const isBest = accuracy.best_model === name
                  return (
                    <div key={name} className={`grid grid-cols-4 gap-2 items-center p-3 rounded-lg text-[12px] border transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated ${isBest ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--bg-secondary)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-sm)]'}`}>
                      <span className="font-medium capitalize flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${isBest ? 'bg-white animate-pulse' : m.mape < 3 ? 'bg-[var(--buy)]' : m.mape < 6 ? 'bg-amber-500' : 'bg-[var(--text-faint)]'}`} />
                        {name}
                      </span>
                      <span className="mono font-medium">{safeFixed(m.mape,2)}%</span>
                      <span className="mono text-[11px] opacity-70">${m.rmse ? safeFixed(m.rmse,0) : '—'}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full w-fit font-medium border ${m.mape < 3 ? 'bg-[var(--buy)] text-white border-[var(--buy)] shadow-sm' : m.mape < 6 ? 'bg-amber-500/15 text-amber-600 border-amber-500/20' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] border-[var(--border)]'}`}>
                        {m.mape < 3 ? 'Excellent' : m.mape < 6 ? 'Good' : 'Fair'}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-5">
                {loading ? <div className="skeleton h-[360px] rounded-xl"></div> : history ? <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={360} /> : <div className="h-[360px] flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border)] gap-2 text-[var(--text-muted)]"><BarChart3 size={20} /> Loading chart</div>}
              </div>

              {selectedCall && (
                <div className="mt-5 p-4 rounded-xl border bg-[var(--bg-secondary)] border-[var(--border)]">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--text-muted)]">{selectedCall.symbol} • Real Call</span>
                    <span className={`ml-auto px-2.5 py-1 rounded-full text-[11px] font-medium ${selectedCall.signal?.includes('BUY') ? 'bg-[var(--buy)] text-white shadow-sm' : 'bg-[var(--sell-soft)] text-[var(--sell)] border border-[var(--sell-border)]'}`}>{selectedCall.action}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-[11px]">
                    {[
                      { label: 'Entry', value: `$${safeFixed(selectedCall.entry_price,2)}`, accent: false },
                      { label: 'SL', value: `$${safeFixed(selectedCall.stop_loss,2)}`, color: 'sell' },
                      { label: 'TP1', value: `$${safeFixed(selectedCall.take_profits?.tp1,2)}`, color: 'buy' },
                      { label: 'R:R', value: `1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)}`, accent: true },
                    ].map((it, i) => (
                      <div key={i} className={`p-2.5 rounded-lg text-center border ${it.accent ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-sm' : it.color === 'buy' ? 'bg-[var(--buy)] text-white border-[var(--buy)] shadow-sm' : it.color === 'sell' ? 'bg-[var(--sell-soft)] border-[var(--sell-border)] text-[var(--sell)]' : 'bg-[var(--card)] border-[var(--border)]'}`}>
                        <div className={`text-[9px] uppercase tracking-wide ${it.accent || it.color === 'buy' ? 'text-white/70' : it.color === 'sell' ? 'text-[var(--sell)]/70' : 'text-[var(--text-muted)]'}`}>{it.label}</div>
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
