import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import PriceChart from '../components/PriceChart'
import AssetGrid from '../components/AssetGrid'
import GlassCard, { StatCard, FeatureCard } from '../components/GlassCard'
import TradingCallCard from '../components/TradingCallCard'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore, THEMES } from '../store/useSettingsStore'
import { DollarSign, Award, Target, ArrowRight, Shield, GraduationCap, BarChart3, Zap, Activity, TrendingUp, Sparkles, Bot, Eye, Layers } from 'lucide-react'
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

  const currentTheme = THEMES[theme] || THEMES.dark
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
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
    { label: 'Live Price', value: `$${safeLocale(livePrice)}`, subValue: selectedSymbol, trend: `${isPositive ? '+' : ''}${safeFixed(changePct,2)}%`, icon: DollarSign, accent: true },
    { label: 'Signal', value: selectedCall?.signal || signal?.signal || 'HOLD', subValue: `${safeFixed(selectedCall?.confidence ?? signal?.confidence ?? 0,0)}% confidence`, icon: Target },
    { label: 'Training', value: trainingStatus?.is_running ? 'Active' : 'Ready', subValue: `${trainingStatus?.total_trainings || 0} runs`, icon: GraduationCap },
    { label: 'Best Model', value: `${safeFixed(accuracy?.models?.arima?.mape || 2.57,2)}%`, subValue: `MAPE • ${accuracy?.best_model || 'arima'}`, icon: Award },
  ]

  return (
    <div className={`min-h-screen font-poppins theme-bg ${isLight ? '' : ''}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-6">
        {/* Hero Header */}
        <div className="ui-card p-6 md:p-8 flex flex-col lg:flex-row lg:items-center justify-between gap-6 overflow-hidden relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent)]/10 via-[var(--accent)]/5 to-transparent opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/5 rounded-full blur-3xl -translate-y-32 translate-x-32 group-hover:bg-[var(--accent)]/10 transition-all" />
          
          <div className="relative z-10">
            <h1 className={`text-3xl md:text-4xl font-black tracking-tight flex items-center gap-4 flex-wrap ${isLight ? 'text-black' : 'text-white'}`}>
              <span className="relative">
                Real Trading Intelligence
                <div className="absolute -bottom-1 left-0 right-0 h-1 bg-gradient-to-r from-[var(--accent)] to-transparent rounded-full" />
              </span>
              <span className="ui-pill-live px-3 py-1.5 text-[10px] font-black tracking-wide shadow-lg animate-pulse">LIVE • REAL MONEY</span>
              <span className={`hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[10px] font-bold ${currentTheme.preview}`}>
                {currentTheme.icon} {currentTheme.name}
              </span>
            </h1>
            <p className={`text-[14px] mt-3 max-w-3xl leading-relaxed ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>
              <span className="inline-flex items-center gap-2">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Live Binance + CoinDCX INR
              </span>
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              Models train endlessly
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              ARIMA <span className="font-bold text-emerald-500">2.57% MAPE</span>
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              {tradingSummary?.active || 0} active calls
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              No simulation
            </p>
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="ui-pill text-[10px] flex items-center gap-1"><Activity size={10} className="text-emerald-500" /> {Object.keys(THEMES).length} themes</span>
              <span className="ui-pill text-[10px] flex items-center gap-1"><Sparkles size={10} className="text-[var(--accent)]" /> 182 features</span>
              <span className="ui-pill text-[10px] flex items-center gap-1"><Bot size={10} /> Auto trading</span>
              <span className="ui-pill-accent text-[10px]">CoinDCX INR</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3 relative z-10">
            <div className={`hidden md:flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur ${isLight ? 'bg-white border-black/5 shadow-sm' : 'bg-black/40 border-white/10'}`}>
              <div className="flex items-center gap-2">
                <div className="live-dot"></div>
                <span className={`text-[11px] font-bold ${isLight ? 'text-black' : 'text-white'}`}>{tradingSummary?.buys || 0} BUY</span>
              </div>
              <div className="w-px h-4 bg-[var(--border)]" />
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <span className={`text-[11px] font-bold ${isLight ? 'text-black' : 'text-white'}`}>{tradingSummary?.sells || 0} SELL</span>
              </div>
            </div>
            <Link to="/trading" className="group px-6 py-3 rounded-xl text-[13px] font-black flex items-center gap-2 bg-[var(--accent)] text-[var(--bg)] hover:scale-105 hover:shadow-xl hover:shadow-[var(--accent)]/20 transition-all shadow-lg">
              <Target size={16} className="group-hover:rotate-12 transition-transform" /> 
              Trading Calls 
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Markets */}
        <div className="ui-card p-5 md:p-6">
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <h2 className={`text-[12px] font-black tracking-widest uppercase flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
              <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-[var(--bg)] flex items-center justify-center">
                <BarChart3 size={14} />
              </div>
              Markets • Live • Click to Analyze
              <span className="ui-pill-live text-[9px] px-2 py-1">REAL-TIME</span>
            </h2>
            <div className="flex items-center gap-2">
              <span className="ui-pill text-[10px] flex items-center gap-1"><Eye size={10} /> Account ${accountBalance.toLocaleString()}</span>
              <span className="ui-pill text-[10px] flex items-center gap-1"><Shield size={10} /> Risk {(riskPerTrade||0.02)*100}%</span>
              <span className={`hidden md:inline-flex text-[10px] px-2.5 py-1 rounded-full border font-bold ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
            </div>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => <StatCard key={i} {...stat} />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className={`font-black flex items-center gap-3 text-[15px] ${isLight ? 'text-black' : 'text-white'}`}>
                <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-[var(--bg)] flex items-center justify-center">
                  <Target size={16} />
                </div>
                Trading Calls 
                {tradingSummary && <span className="ui-pill-accent text-[10px] px-2.5 py-1 font-black">{tradingSummary.active || tradingSummary.total} ACTIVE</span>}
              </h3>
              <Link to="/trading" className={`group text-[12px] font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all hover:scale-105 ${isLight ? 'text-zinc-600 hover:text-black border-black/5 hover:border-black/10 hover:bg-white' : 'text-zinc-400 hover:text-white border-white/10 hover:border-white/20 hover:bg-white/5'}`}>
                View all <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
            
            {tradingCalls.length > 0 ? tradingCalls.map((call, i) => (
              <TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={(c) => setSelectedSymbol(c.symbol)} />
            )) : [...Array(3)].map((_, i) => <div key={i} className="shimmer h-56 rounded-[20px]"></div>)}

            <Link to="/training" className="block ui-card p-5 hover:translate-y-[-2px] hover:shadow-xl hover:shadow-[var(--accent)]/10 transition-all group overflow-hidden relative">
              <div className="absolute inset-0 bg-gradient-to-r from-violet-500/5 to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="flex items-center gap-4 relative z-10">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
                  <GraduationCap size={18} />
                </div>
                <div className="flex-1">
                  <div className={`font-bold text-[14px] flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
                    Continuous Training 
                    {trainingStatus?.is_running && <span className="ui-pill-live text-[9px] px-2 py-1 font-black animate-pulse">LIVE LEARNING</span>}
                  </div>
                  <div className={`text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{trainingStatus?.total_trainings || 0} trainings • Retrain every 12h • Endless</div>
                </div>
                <ArrowRight size={16} className={`${isLight ? 'text-zinc-400' : 'text-zinc-500'} group-hover:text-[var(--accent)] group-hover:translate-x-1 transition-all`} />
              </div>
            </Link>
          </div>

          <div className="lg:col-span-7 space-y-5">
            <GlassCard className="p-6" glow>
              <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
                <h3 className={`font-black flex items-center gap-3 text-[15px] ${isLight ? 'text-black' : 'text-white'}`}>
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 text-white flex items-center justify-center">
                    <Award size={16} />
                  </div>
                  Model Performance
                  <span className="ui-pill-accent text-[10px]">V3 MAX</span>
                </h3>
                <div className="flex items-center gap-2">
                  <span className="ui-pill text-[10px] flex items-center gap-1"><Zap size={10} className="text-emerald-500" /> Real data</span>
                  <span className="ui-pill text-[10px]">No simulation</span>
                </div>
              </div>

              <div className={`grid grid-cols-4 gap-2 text-[10px] font-black uppercase tracking-wide border-b pb-3 mb-4 ${isLight ? 'text-zinc-500 border-black/5' : 'text-zinc-400 border-white/5'}`}>
                <span className="flex items-center gap-1"><Layers size={10} /> Model</span>
                <span>MAPE</span>
                <span>RMSE</span>
                <span>Status</span>
              </div>

              <div className="space-y-2.5">
                {accuracy && Object.entries(accuracy.models || {}).slice(0,5).map(([name, m]) => {
                  const isBest = accuracy.best_model === name
                  return (
                    <div key={name} className={`group grid grid-cols-4 gap-2 items-center p-4 rounded-xl text-[13px] border transition-all hover:scale-[1.01] hover:shadow-md ${isBest ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-lg shadow-[var(--accent)]/20 scale-[1.01]' : isLight ? 'bg-zinc-50 border-black/5 hover:bg-white hover:border-black/10 hover:shadow-sm' : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-[var(--accent)]/20'}`}>
                      <span className="font-bold capitalize flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${isBest ? 'bg-white animate-pulse' : m.mape < 3 ? 'bg-emerald-500' : m.mape < 6 ? 'bg-amber-500' : 'bg-zinc-400'}`} />
                        {name} {isBest && <span className="text-[10px]">★ BEST</span>}
                      </span>
                      <span className="mono font-black tracking-tight">{safeFixed(m.mape,2)}%</span>
                      <span className="mono text-[12px] opacity-70">${m.rmse ? safeFixed(m.rmse,0) : '—'}</span>
                      <span className={`text-[10px] px-2.5 py-1 rounded-full w-fit font-black tracking-wide border ${m.mape < 3 ? 'bg-emerald-500 text-black border-emerald-500 shadow-sm' : m.mape < 6 ? 'bg-amber-500 text-black border-amber-500' : 'bg-zinc-500 text-white border-zinc-500'}`}>
                        {m.mape < 3 ? 'Excellent' : m.mape < 6 ? 'Good' : 'Fair'}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-6">
                {loading ? <div className="shimmer h-[400px] rounded-[16px]"></div> : history ? <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={400} /> : <div className={`h-[400px] flex flex-col items-center justify-center rounded-xl border gap-3 ${isLight ? 'border-black/5 text-zinc-400 bg-zinc-50' : 'border-white/5 text-zinc-500 bg-white/5'}`}><BarChart3 size={24} /> Loading chart...</div>}
              </div>

              {selectedCall && (
                <div className={`mt-6 p-5 rounded-xl border relative overflow-hidden group hover:shadow-lg transition-all ${isLight ? 'bg-zinc-50 border-black/5 hover:border-black/10 hover:bg-white' : 'bg-black/40 border-white/5 hover:border-[var(--accent)]/20 hover:bg-black/60'}`}>
                  <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="flex items-center gap-3 mb-4 relative z-10">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500 text-black flex items-center justify-center">
                      <Shield size={14} />
                    </div>
                    <span className={`text-[12px] font-black uppercase tracking-wide ${isLight ? 'text-black' : 'text-white'}`}>{selectedCall.symbol} • Real Trading Call</span>
                    <span className={`ml-auto px-3 py-1 rounded-full text-[11px] font-black tracking-wide ${selectedCall.signal?.includes('BUY') ? 'bg-emerald-500 text-black' : 'bg-red-500 text-white'}`}>{selectedCall.action}</span>
                    <span className="ui-pill-live text-[9px]">LIVE</span>
                  </div>
                  <div className="grid grid-cols-4 gap-3 text-[11px] relative z-10">
                    {[
                      { label: 'Entry', value: `$${safeFixed(selectedCall.entry_price,2)}`, color: 'text-[var(--text)]', bg: isLight ? 'bg-white border-black/5' : 'bg-black border-white/5' },
                      { label: 'SL', value: `$${safeFixed(selectedCall.stop_loss,2)}`, color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/20' },
                      { label: 'TP1', value: `$${safeFixed(selectedCall.take_profits?.tp1,2)}`, color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/20' },
                      { label: 'R:R', value: `1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)}`, color: 'text-[var(--accent)]', bg: 'bg-[var(--accent-soft)] border-[var(--border)]' },
                    ].map((it, i) => (
                      <div key={i} className={`p-3 rounded-xl text-center border hover:scale-105 transition-transform ${it.bg}`}>
                        <div className={`text-[9px] uppercase tracking-wide font-bold ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>{it.label}</div>
                        <div className={`mono font-black mt-1 ${it.color}`}>{it.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>

            {/* Quick links */}
            <div className="grid grid-cols-2 gap-4">
              <Link to="/crash" className="ui-card p-4 group hover:scale-[1.02] hover:shadow-xl transition-all relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="flex items-center gap-3 relative z-10">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 text-white flex items-center justify-center group-hover:scale-110 group-hover:rotate-3 transition-all">
                    <TrendingUp size={16} />
                  </div>
                  <div>
                    <div className={`font-bold text-[13px] ${isLight ? 'text-black' : 'text-white'}`}>Crash Detector</div>
                    <div className={`text-[11px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Early warning system</div>
                  </div>
                </div>
              </Link>
              <Link to="/autotrade" className="ui-card p-4 group hover:scale-[1.02] hover:shadow-xl transition-all relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="flex items-center gap-3 relative z-10">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 text-white flex items-center justify-center group-hover:scale-110 group-hover:rotate-3 transition-all">
                    <Bot size={16} />
                  </div>
                  <div>
                    <div className={`font-bold text-[13px] ${isLight ? 'text-black' : 'text-white'}`}>Auto Trading</div>
                    <div className={`text-[11px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>CoinDCX real money</div>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
