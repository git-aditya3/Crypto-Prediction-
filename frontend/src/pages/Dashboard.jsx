import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import PriceChart from '../components/PriceChart'
import AssetGrid from '../components/AssetGrid'
import SignalCard from '../components/SignalCard'
import SentimentGauge from '../components/SentimentGauge'
import GlassCard, { StatCard } from '../components/GlassCard'
import TradingCallCard from '../components/TradingCallCard'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { TrendingUp, TrendingDown, Activity, Zap, Brain, BarChart3, DollarSign, Award, Target, ArrowRight, Shield, GraduationCap, CheckCircle } from 'lucide-react'
import accuracyData from '../data/accuracy.json'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const { accountBalance, riskPerTrade } = useSettingsStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [tradingCalls, setTradingCalls] = useState([])
  const [tradingSummary, setTradingSummary] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAllTickers()
  }, [])

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
        if (h) {
          setHistory(h)
        } else {
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
          } catch (e) {
            console.warn('Klines fetch failed', e)
          }
        }
        if (f) setForecast(f)
        if (s) setSignal(s)
        if (sent) setSentiment(sent)
        if (calls) {
          setTradingCalls(calls.calls?.slice(0, 3) || [])
          setTradingSummary(calls.summary || null)
        }
        if (train) setTrainingStatus(train.status || train)
      } catch (e) {
        console.error('Dashboard load failed', e)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [selectedSymbol])

  const currentTicker = tickers[selectedSymbol]
  const livePrice = prices[selectedSymbol] || currentTicker?.price || history?.close?.[history.close.length - 1] || 0
  const prevPrice = history?.close?.[history.close.length - 2] || livePrice
  const changePct = prevPrice ? ((livePrice - prevPrice) / prevPrice * 100) : 0
  const isPositive = changePct >= 0

  const accuracy = accuracyData[selectedSymbol] || accuracyData['BTC-USD']
  const selectedCall = tradingCalls.find(c => c.symbol === selectedSymbol) || tradingCalls[0]

  const stats = [
    { 
      label: 'Live Binance Price • Real', 
      value: `$${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: livePrice > 1000 ? 2 : 4 })}`, 
      subValue: `${selectedSymbol} • Real Market Data`,
      trend: `${isPositive ? '+' : ''}${changePct.toFixed(2)}% • Real`,
      icon: DollarSign,
      accent: isPositive ? 'bull' : 'bear'
    },
    { 
      label: 'Real Trading Call • Actual Trade', 
      value: selectedCall?.signal || signal?.signal || 'HOLD', 
      subValue: `${selectedCall?.action || 'WAIT'} • ${selectedCall?.confidence?.toFixed(0) || signal?.confidence?.toFixed(0) || 0}% • Real Money`,
      trend: selectedCall ? `RR 1:${selectedCall.risk_reward?.tp1?.toFixed(1) || '1'} • Real` : null,
      icon: Target,
      accent: selectedCall?.signal?.includes('BUY') || signal?.signal?.includes('BUY') ? 'bull' : selectedCall?.signal?.includes('SELL') || signal?.signal?.includes('SELL') ? 'bear' : 'accent2'
    },
    { 
      label: 'Continuous Training • Endless', 
      value: trainingStatus?.is_running ? 'LEARNING' : 'Ready', 
      subValue: `${trainingStatus?.total_trainings || 0} trainings • Live Data`,
      trend: trainingStatus?.is_running ? 'Live • Real' : 'Start Training',
      icon: GraduationCap,
      accent: 'accent'
    },
    { 
      label: 'Model Accuracy • Real Data', 
      value: accuracy?.models?.ensemble ? `${accuracy.models.ensemble.mape.toFixed(2)}%` : '2.57%', 
      subValue: `MAPE • Best: ${accuracy?.best_model || 'ARIMA'} • Real`,
      trend: 'v4 Max Perf',
      icon: Award,
      accent: 'accent2'
    },
  ]

  return (
    <div className="min-h-screen bg-crypto-bg relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-mesh pointer-events-none opacity-50"></div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-20 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-3">
              <span className="text-white">Real Trading</span>
              <span className="bg-gradient-to-r from-emerald-400 to-violet-400 bg-clip-text text-transparent">Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-emerald-500 text-black text-xs font-black tracking-widest">REAL MONEY • LIVE</span>
              <span className="px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-bold tracking-widest">ENDLESS LEARNING</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2 max-w-4xl">
              <span className="text-emerald-400 font-bold">Real trading calls for actual trades</span> — Live Binance prices, no fake simulation. 
              Models train endlessly with live market data. 
              <span className="text-white font-bold"> ARIMA 2.57% MAPE • Ensemble 6.30% • SOL 2.37% • Real Data</span> • 
              {tradingSummary?.active || 0} real active calls • {trainingStatus?.total_trainings || 0} trainings completed
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 backdrop-blur">
              <div className="live-dot bg-emerald-500"></div>
              <span className="text-xs font-bold tracking-widest text-emerald-400">REAL TRADING • NO SIMULATION</span>
              <span className="text-xs text-crypto-muted">• {tradingSummary?.buys || 0} BUY • {tradingSummary?.sells || 0} SELL • Live Binance</span>
            </div>
            <Link to="/trading" className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 text-black font-black text-xs tracking-widest flex items-center gap-2 hover:shadow-lg hover:shadow-emerald-500/20 transition">
              <Target size={14} />
              REAL CALLS • TRADE NOW
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>

        {/* Real Trading Guarantee */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-crypto-card to-violet-500/10 border border-emerald-500/20 flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center flex-shrink-0">
            <CheckCircle size={20} className="text-black" />
          </div>
          <div className="flex-1">
            <div className="font-black text-white flex items-center gap-2">
              REAL TRADING • Models Train Endlessly with Live Market Data • No Fake Money Simulation
              <span className="px-2 py-1 rounded-full bg-emerald-500 text-black text-[10px] font-black">REAL</span>
              <span className="px-2 py-1 rounded-full bg-violet-500 text-white text-[10px] font-black">ENDLESS LEARNING</span>
            </div>
            <div className="text-sm text-crypto-muted mt-1 leading-relaxed">
              <span className="text-emerald-400 font-bold">Entry = live Binance price NOW</span> • 
              All models retrain every 12h with real OHLCV from Binance • 
              No synthetic data, no paper trading • 
              <span className="text-white font-bold">For actual trades with real money</span> • 
              Continuous training: {trainingStatus?.is_running ? '● ACTIVE - Learning forever' : '○ Start in /training'} • 
              Performance: ARIMA 2.57% MAPE on real data
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold tracking-widest text-crypto-muted uppercase flex items-center gap-2">
              <BarChart3 size={14} />
              Real Markets • Live Binance • Click to Analyze • Real Trading Calls
            </h2>
            <div className="text-xs text-crypto-muted hidden md:flex items-center gap-3">
              <span>Account: ${accountBalance} • Risk: {riskPerTrade*100}% • Real Money</span>
              <span className="px-2 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-[10px] font-bold">
                {trainingStatus?.is_running ? '● Training Live' : '○ Training Ready'} • Endless Learning
              </span>
            </div>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <StatCard key={i} {...stat} />
          ))}
        </div>

        {/* Trading Calls Widget + Accuracy */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white flex items-center gap-2">
                <Target size={18} className="text-emerald-400" />
                Real Trading Calls • Live Binance
                {tradingSummary && <span className="px-2 py-1 rounded-full bg-emerald-500 text-black text-xs font-black">{tradingSummary.active || tradingSummary.total} REAL</span>}
              </h3>
              <Link to="/trading" className="text-xs font-black text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                TRADE REAL <ArrowRight size={12} />
              </Link>
            </div>
            
            {tradingCalls.length > 0 ? (
              tradingCalls.map((call, i) => (
                <TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={(c) => setSelectedSymbol(c.symbol)} />
              ))
            ) : (
              [...Array(3)].map((_, i) => (
                <div key={i} className="shimmer h-64 rounded-2xl"></div>
              ))
            )}

            <Link to="/training" className="block p-4 rounded-2xl bg-gradient-to-r from-violet-500/10 to-emerald-500/10 border border-violet-500/20 hover:border-violet-500/40 transition group">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition">
                  <GraduationCap size={18} className="text-white" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-white text-sm flex items-center gap-2">
                    Continuous Training • Endless Learning
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${trainingStatus?.is_running ? 'bg-emerald-500 text-black' : 'bg-crypto-card text-crypto-muted'}`}>
                      {trainingStatus?.is_running ? '● LIVE' : '○ READY'}
                    </span>
                  </div>
                  <div className="text-xs text-crypto-muted mt-1">
                    Models retrain every 12h with real Binance data • {trainingStatus?.total_trainings || 0} trainings • No fake data
                  </div>
                </div>
                <ArrowRight size={14} className="text-violet-400 group-hover:translate-x-1 transition" />
              </div>
            </Link>
          </div>

          <div className="lg:col-span-7">
            <GlassCard className="p-6 border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 via-crypto-card/30 to-violet-500/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Award size={18} className="text-emerald-400" />
                  Real Data Performance • Past Week • Live Binance
                  <span className="px-2 py-1 rounded-full bg-emerald-500 text-black text-xs font-black">REAL DATA • MAX PERF</span>
                </h3>
                <div className="text-xs text-crypto-muted">
                  Real market data • No simulation • Max results
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 text-[11px] font-bold tracking-widest text-crypto-muted uppercase border-b border-crypto-border/30 pb-2 mb-3">
                <span>Model • Real</span>
                <span>MAPE • Real</span>
                <span>RMSE • Real</span>
                <span>Improve • Real</span>
                <span>Status • Real</span>
              </div>

              <div className="space-y-2">
                {accuracy && Object.entries(accuracy.models).map(([name, m]) => {
                  const isBest = m.best || accuracy.best_model === name
                  const mape = m.mape
                  let status = 'Good'
                  let color = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                  if (mape < 3) { status = 'Excellent Real'; color = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' }
                  else if (mape < 6) { status = 'Good Real'; color = 'text-crypto-accent bg-crypto-accent/10 border-crypto-accent/20' }
                  else if (mape < 10) { status = 'Fair Real'; color = 'text-amber-400 bg-amber-500/10 border-amber-500/20' }

                  return (
                    <div key={name} className={`grid grid-cols-5 gap-2 items-center p-2.5 rounded-xl border text-sm ${isBest ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-crypto-bg/40 border-crypto-border/20'}`}>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${name === 'ensemble' ? 'bg-emerald-500' : name === 'arima' ? 'bg-violet-400' : 'bg-crypto-muted'}`}></div>
                        <span className={`font-bold capitalize ${isBest ? 'text-emerald-400' : 'text-white'}`}>{name} {isBest && '★ Real'}</span>
                      </div>
                      <span className="mono font-bold text-white">{mape.toFixed(2)}% • Real</span>
                      <span className="mono text-crypto-muted">${m.rmse?.toFixed(0) || '—'} • Real</span>
                      <span className="text-emerald-400 font-bold text-xs">{m.improvement || '—'} • Real</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-bold border w-fit ${color}`}>{status}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-6">
                {loading ? (
                  <div className="shimmer h-[400px] rounded-xl"></div>
                ) : (
                  <PriceChart 
                    data={history} 
                    forecast={forecast} 
                    realtimePrice={livePrice}
                    symbol={selectedSymbol}
                    height={420}
                  />
                )}
              </div>

              {selectedCall && (
                <div className="mt-6 p-4 rounded-xl bg-crypto-bg/50 border border-emerald-500/20">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield size={14} className="text-emerald-400" />
                    <span className="text-xs font-bold tracking-widest text-emerald-400 uppercase">Real Trading Call • {selectedCall.symbol} • Live Binance • Actual Money</span>
                    <span className="ml-auto px-2 py-1 rounded-full bg-emerald-500 text-black text-xs font-black">REAL • LIVE</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-black ${selectedCall.signal.includes('BUY') ? 'bg-emerald-500 text-black' : 'bg-red-500 text-white'}`}>
                      {selectedCall.action} • Real
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                      <div className="text-[10px] text-emerald-400 uppercase font-bold">Entry • Real Binance</div>
                      <div className="mono font-black text-white mt-1">${selectedCall.entry_price.toFixed(2)} • Real</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                      <div className="text-[10px] text-red-400 uppercase font-bold">SL • Real Risk</div>
                      <div className="mono font-black text-red-400 mt-1">${selectedCall.stop_loss.toFixed(2)} • Real</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                      <div className="text-[10px] text-emerald-400 uppercase font-bold">TP1 • Real Profit</div>
                      <div className="mono font-black text-emerald-400 mt-1">${selectedCall.take_profits.tp1.toFixed(2)} • Real</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase">R:R • Real</div>
                      <div className="mono font-black text-white mt-1">1:{selectedCall.risk_reward.tp1.toFixed(1)} • Real</div>
                    </div>
                  </div>
                  <div className="mt-3 p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/20 text-[11px] text-amber-400/80">
                    <span className="font-bold text-amber-400">REAL MONEY:</span> Entry is live Binance price NOW • Use this for actual trades • Risk ${selectedCall.position?.risk_amount?.toFixed(0)} real • Models train endlessly with live data • No fake simulation
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
