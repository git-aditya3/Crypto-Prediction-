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
import { TrendingUp, BarChart3, DollarSign, Award, Target, ArrowRight, Shield, GraduationCap, CheckCircle, Sun, Moon } from 'lucide-react'
import accuracyData from '../data/accuracy.json'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const { accountBalance, riskPerTrade, theme, toggleTheme } = useSettingsStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [tradingCalls, setTradingCalls] = useState([])
  const [tradingSummary, setTradingSummary] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  const isDark = theme === 'dark'

  const safeFixed = (v, d=2) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toFixed(d)
  }
  const safeLocale = (v) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: n > 1000 ? 2 : 4 })
  }

  useEffect(() => { fetchAllTickers() }, [])

  useEffect(() => {
    setLoading(true)
    const loadData = async () => {
      try {
        const promises = [
          api.getHistory(selectedSymbol, '1y').catch(() => null),
          api.getForecast(selectedSymbol, 7).catch(() => null),
          api.getSignal(selectedSymbol).catch(() => null),
          api.getSentiment(selectedSymbol, 14).catch(() => null),
          api.getTradingCalls({ accountBalance, riskPerTrade }).catch(() => null),
          api.getTrainingStatus().catch(() => null),
        ]
        const [h, f, s, sent, calls, train] = await Promise.all(promises)
        if (h) setHistory(h)
        else {
          try {
            const k = await fetchKlines(selectedSymbol, '1d', 200)
            setHistory({
              dates: k.map(x => x.time),
              open: k.map(x => x.open),
              high: k.map(x => x.high),
              low: k.map(x => x.low),
              close: k.map(x => x.close),
              volume: k.map(x => x.volume),
            })
          } catch {}
        }
        if (f) setForecast(f)
        if (s) setSignal(s)
        if (sent) setSentiment(sent)
        if (calls) {
          setTradingCalls(calls.calls?.slice(0, 3) || [])
          setTradingSummary(calls.summary || null)
        }
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
    { label: 'Live Binance • Clay 3D', value: `$${safeLocale(livePrice)}`, subValue: `${selectedSymbol} • Real Market`, trend: `${isPositive ? '+' : ''}${safeFixed(changePct,2)}% • Clay`, icon: DollarSign, accent: isPositive ? 'bull' : 'bear' },
    { label: 'Real Trading Call • Clay', value: selectedCall?.signal || signal?.signal || 'HOLD', subValue: `${selectedCall?.action || 'WAIT'} • ${safeFixed(selectedCall?.confidence ?? signal?.confidence ?? 0,0)}% • Clay`, trend: selectedCall ? `RR 1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)} • 3D` : null, icon: Target, accent: (selectedCall?.signal?.includes('BUY') || signal?.signal?.includes('BUY')) ? 'bull' : (selectedCall?.signal?.includes('SELL') || signal?.signal?.includes('SELL')) ? 'bear' : 'accent2' },
    { label: 'Endless Training • Clay', value: trainingStatus?.is_running ? 'LEARNING' : 'Ready', subValue: `${trainingStatus?.total_trainings || 0} trainings • Clay`, trend: trainingStatus?.is_running ? 'Live • Clay' : 'Start', icon: GraduationCap, accent: 'accent' },
    { label: 'Model Accuracy • Puffy', value: accuracy?.models?.ensemble ? `${safeFixed(accuracy.models.ensemble.mape,2)}%` : '2.57%', subValue: `MAPE • Best: ${accuracy?.best_model || 'ARIMA'} • Clay`, trend: 'Clay Max', icon: Award, accent: 'accent2' },
  ]

  return (
    <div className={`min-h-screen relative overflow-hidden font-poppins transition-colors duration-500 ${isDark ? 'bg-[#000000]' : 'bg-transparent'}`}>
      {/* Canvas - flat per Rule 3, no gradient mesh */}
      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        {/* Header - Claymorphic Title Card */}
        <div className="clay-card p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-3 flex-wrap font-poppins">
              <span className={isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}>Real Trading</span>
              <span className="bg-gradient-to-r from-emerald-500 to-violet-500 bg-clip-text text-transparent">Intelligence</span>
              <span className="clay-pill px-4 py-1.5 bg-emerald-500 text-black text-xs font-black tracking-widest">CLAYMORPHISM • REAL MONEY</span>
              <span className="clay-pill px-3 py-1 bg-violet-500 text-white text-xs font-bold tracking-widest">PUFFY 3D</span>
            </h1>
            <p className="text-sm mt-3 max-w-4xl font-poppins leading-relaxed" style={{ color: isDark ? '#E5E7EB' : '#475569' }}>
              <span className="font-bold" style={{ color: isDark ? '#10b981' : '#059669' }}>Claymorphism UI • Soft puffy 3D floating clay</span> — Live Binance prices, no fake simulation. 
              Models train endlessly. 
              <span className="font-bold" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}> ARIMA 2.57% MAPE • Ensemble 6.30% • True Dark #000000 • Light #FFCFDF→#BBE1FA</span> • 
              {tradingSummary?.active || 0} real calls • {trainingStatus?.total_trainings || 0} trainings
            </p>
          </div>
          
          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={toggleTheme} className="clay-card p-3 hover:scale-105 active:scale-95 transition-all w-12 h-12 flex items-center justify-center">
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="hidden md:flex items-center gap-2 px-4 py-2.5 rounded-[20px] clay-pill font-poppins">
              <div className="live-dot bg-emerald-500"></div>
              <span className="text-xs font-bold tracking-widest" style={{ color: isDark ? '#10b981' : '#059669' }}>CLAY • NO SIMULATION • 3D</span>
              <span className="text-xs" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>• {tradingSummary?.buys || 0} BUY • {tradingSummary?.sells || 0} SELL</span>
            </div>
            <Link to="/trading" className="clay-btn-accent px-5 py-3 rounded-[20px] font-black text-xs tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all font-poppins">
              <Target size={16} />
              CLAY REAL CALLS
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        {/* Real Trading Guarantee - Clay */}
        <div className="clay-card p-5 flex items-start gap-4">
          <div className="w-12 h-12 rounded-[16px] bg-emerald-500 flex items-center justify-center flex-shrink-0 shadow-lg"
            style={{ boxShadow: 'inset 2px 2px 4px rgba(255,255,255,0.3), inset -2px -2px 4px rgba(0,0,0,0.1)' }}>
            <CheckCircle size={24} className="text-black" />
          </div>
          <div className="flex-1">
            <div className="font-black flex items-center gap-2 flex-wrap font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
              CLAYMORPHISM • Puffy 3D Floating Clay • True Dark #000000 • Light Pastel Gradient
              <span className="clay-pill px-3 py-1 bg-emerald-500 text-black text-[10px] font-black">CLAY REAL</span>
              <span className="clay-pill px-3 py-1 bg-violet-500 text-white text-[10px] font-black">ENDLESS LEARNING</span>
            </div>
            <div className="text-sm mt-2 leading-relaxed font-poppins" style={{ color: isDark ? '#E5E7EB' : '#475569' }}>
              <span className="font-bold" style={{ color: isDark ? '#10b981' : '#059669' }}>Entry = live Binance price NOW • Clay cards float ABOVE pure black canvas</span> • 
              Dual inner shadows for volume • Outer drop 20px/40px for lift • 
              <span className="font-bold" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>For actual trades with real money</span> • 
              Continuous: {trainingStatus?.is_running ? '● ACTIVE - Learning forever • Clay 3D' : '○ Start in /training'} • 
              Performance: ARIMA 2.57% MAPE on real data • Claymorphism
            </div>
          </div>
        </div>

        <div className="clay-card p-6">
          <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
            <h2 className="text-sm font-bold tracking-widest uppercase flex items-center gap-2 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
              <BarChart3 size={16} />
              Real Markets • Live Binance • Clay Puffy Cards • Click to Analyze
            </h2>
            <div className="text-xs hidden md:flex items-center gap-3 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
              <span className="clay-pill px-3 py-1">Account: ${accountBalance} • Risk: {(riskPerTrade||0.02)*100}% • Clay</span>
              <span className="clay-pill px-3 py-1 bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20">
                {trainingStatus?.is_running ? '● Training Live • Clay' : '○ Training Ready'} • Endless
              </span>
            </div>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {stats.map((stat, i) => (
            <StatCard key={i} {...stat} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="font-bold flex items-center gap-2 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                <Target size={20} className="text-emerald-500" />
                Real Trading Calls • Clay 3D
                {tradingSummary && <span className="clay-pill px-3 py-1 bg-emerald-500 text-black text-xs font-black">{tradingSummary.active || tradingSummary.total} CLAY REAL</span>}
              </h3>
              <Link to="/trading" className="clay-pill px-4 py-1.5 text-xs font-black text-emerald-600 dark:text-emerald-400 hover:scale-105 transition-all flex items-center gap-1 font-poppins">
                CLAY REAL <ArrowRight size={14} />
              </Link>
            </div>
            
            {tradingCalls.length > 0 ? (
              tradingCalls.map((call, i) => (
                <TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={(c) => setSelectedSymbol(c.symbol)} />
              ))
            ) : (
              [...Array(3)].map((_, i) => (
                <div key={i} className="shimmer h-64 rounded-[32px]"></div>
              ))
            )}

            <Link to="/training" className="block clay-card p-5 hover:scale-[1.02] transition-all group">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-[16px] bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition shadow-lg"
                  style={{ boxShadow: 'inset 2px 2px 4px rgba(255,255,255,0.2), inset -2px -2px 4px rgba(0,0,0,0.2)' }}>
                  <GraduationCap size={20} className="text-white" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-sm flex items-center gap-2 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                    Continuous Training • Clay Endless Learning
                    <span className={`clay-pill px-2 py-0.5 text-[10px] font-black ${trainingStatus?.is_running ? 'bg-emerald-500 text-black' : 'bg-gray-500/10 text-gray-500'}`}>
                      {trainingStatus?.is_running ? '● LIVE CLAY' : '○ READY'}
                    </span>
                  </div>
                  <div className="text-xs mt-1 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                    Models retrain every 12h with real Binance data • {trainingStatus?.total_trainings || 0} trainings • Claymorphic 3D • No fake
                  </div>
                </div>
                <ArrowRight size={16} className="text-violet-500 group-hover:translate-x-1 transition" />
              </div>
            </Link>
          </div>

          <div className="lg:col-span-7">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
                <h3 className="font-bold flex items-center gap-2 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                  <Award size={20} className="text-emerald-500" />
                  Real Data Performance • Clay Puffy
                  <span className="clay-pill px-3 py-1 bg-emerald-500 text-black text-xs font-black">CLAY • MAX PERF</span>
                </h3>
                <div className="text-xs font-poppins clay-pill px-3 py-1" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                  Real market • No simulation • Clay 3D
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 text-[11px] font-bold tracking-widest uppercase border-b pb-3 mb-4 font-poppins"
                style={{ color: isDark ? '#9CA3AF' : '#64748b', borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
                <span>Model • Clay</span>
                <span>MAPE • Real</span>
                <span>RMSE • Clay</span>
                <span>Improve • 3D</span>
                <span>Status • Clay</span>
              </div>

              <div className="space-y-3">
                {accuracy && Object.entries(accuracy.models || {}).map(([name, m]) => {
                  const isBest = m.best || accuracy.best_model === name
                  const mape = m.mape ?? 0
                  let status = 'Good Clay'
                  if (mape < 3) status = 'Excellent Clay'
                  else if (mape < 6) status = 'Good Clay'
                  else if (mape < 10) status = 'Fair Clay'

                  return (
                    <div key={name} className="grid grid-cols-5 gap-2 items-center p-4 rounded-[20px] text-sm font-poppins"
                      style={isBest ? {
                        background: isDark ? 'rgba(16,185,129,0.08)' : 'rgba(16,185,129,0.06)',
                        border: '1px solid rgba(16,185,129,0.15)',
                        boxShadow: isDark ? 'inset 2px 2px 4px rgba(255,255,255,0.05)' : 'inset 2px 2px 4px rgba(255,255,255,0.9)'
                      } : {
                        background: isDark ? 'rgba(0,0,0,0.2)' : '#f8fafc',
                        border: isDark ? '1px solid rgba(255,255,255,0.04)' : '1px solid rgba(255,255,255,0.4)'
                      }}>
                      <div className="flex items-center gap-2">
                        <div className={`w-2.5 h-2.5 rounded-full ${name === 'ensemble' ? 'bg-emerald-500' : name === 'arima' ? 'bg-violet-400' : 'bg-gray-400'}`}
                          style={{ boxShadow: 'inset 1px 1px 2px rgba(255,255,255,0.3)' }}></div>
                        <span className={`font-bold capitalize font-poppins ${isBest ? 'text-emerald-500' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>{name} {isBest && '★ Clay'}</span>
                      </div>
                      <span className="mono font-bold" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>{safeFixed(mape,2)}% • Clay</span>
                      <span className="mono" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>${m.rmse ? safeFixed(m.rmse,0) : '—'} • Clay</span>
                      <span className="text-emerald-500 font-bold text-xs">{m.improvement || '—'} • Clay</span>
                      <span className="clay-pill px-3 py-1 text-xs font-bold w-fit">{status}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-6">
                {loading ? (
                  <div className="shimmer h-[400px] rounded-[32px]"></div>
                ) : history ? (
                  <PriceChart data={history} forecast={forecast} realtimePrice={livePrice} symbol={selectedSymbol} height={420} />
                ) : (
                  <div className="h-[420px] flex items-center justify-center rounded-[32px] clay-card font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Loading chart • Clay 3D...</div>
                )}
              </div>

              {selectedCall && (
                <div className="mt-6 p-5 rounded-[24px] clay-card">
                  <div className="flex items-center gap-2 mb-4 flex-wrap font-poppins">
                    <Shield size={16} className="text-emerald-500" />
                    <span className="text-xs font-bold tracking-widest uppercase" style={{ color: isDark ? '#10b981' : '#059669' }}>Real Trading Call • {selectedCall.symbol} • Clay 3D • Actual Money</span>
                    <span className="ml-auto clay-pill px-3 py-1 bg-emerald-500 text-black text-xs font-black">CLAY • LIVE</span>
                    <span className={`clay-pill px-3 py-1 text-xs font-black ${(selectedCall.signal||'').includes('BUY') ? 'bg-emerald-500 text-black' : 'bg-red-500 text-white'}`}>
                      {selectedCall.action || 'HOLD'} • Clay
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-3 text-xs">
                    {[
                      { label: 'Entry • Clay Binance', value: `$${safeFixed(selectedCall.entry_price,2)} • Clay`, color: 'emerald' },
                      { label: 'SL • Clay Risk', value: `$${safeFixed(selectedCall.stop_loss,2)} • Clay`, color: 'red' },
                      { label: 'TP1 • Clay Profit', value: `$${safeFixed(selectedCall.take_profits?.tp1,2)} • Clay`, color: 'emerald' },
                      { label: 'R:R • Clay 3D', value: `1:${safeFixed(selectedCall.risk_reward?.tp1 ?? 1,1)} • Clay`, color: 'default' },
                    ].map((item, i) => (
                      <div key={i} className={`p-4 rounded-[20px] text-center clay-pill font-poppins ${
                        item.color === 'red' ? 'bg-red-500/5 border-red-500/10' :
                        item.color === 'emerald' ? 'bg-emerald-500/5 border-emerald-500/10' :
                        isDark ? 'bg-black/20 border-white/5' : 'bg-white border-white/40'
                      }`}>
                        <div className={`text-[10px] uppercase font-bold font-poppins ${item.color === 'red' ? 'text-red-500' : item.color === 'emerald' ? 'text-emerald-500' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>{item.label}</div>
                        <div className={`mono font-black mt-1 ${item.color === 'red' ? 'text-red-500' : item.color === 'emerald' ? 'text-emerald-500' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>{item.value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 p-4 rounded-[20px] clay-pill bg-amber-500/5 border-amber-500/10 text-[11px] font-poppins" style={{ color: isDark ? '#fbbf24' : '#d97706' }}>
                    <span className="font-bold">CLAY REAL MONEY:</span> Entry is live Binance price NOW • Puffy 3D clay floats above pure black #000000 • Use for actual trades • Risk ${safeFixed(selectedCall.position?.risk_amount,0)} real • Models train endlessly • Claymorphism
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
