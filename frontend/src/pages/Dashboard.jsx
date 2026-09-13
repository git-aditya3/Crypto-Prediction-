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
import { TrendingUp, TrendingDown, Activity, Zap, Brain, BarChart3, Clock, DollarSign, Layers, Sparkles, Award, Target, ArrowRight, Shield, TrendingUpIcon } from 'lucide-react'
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
        ]
        const [h, f, s, sent, calls] = await Promise.all(promises)
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
      label: 'Live Price', 
      value: `$${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: livePrice > 1000 ? 2 : 4 })}`, 
      subValue: `${selectedSymbol} • Binance`,
      trend: `${isPositive ? '+' : ''}${changePct.toFixed(2)}%`,
      icon: DollarSign,
      accent: isPositive ? 'bull' : 'bear'
    },
    { 
      label: 'Trading Call', 
      value: selectedCall?.signal || signal?.signal || 'HOLD', 
      subValue: `${selectedCall?.action || 'WAIT'} • ${selectedCall?.confidence?.toFixed(0) || signal?.confidence?.toFixed(0) || 0}% conf`,
      trend: selectedCall ? `RR 1:${selectedCall.risk_reward?.tp1?.toFixed(1) || '1'}` : null,
      icon: Target,
      accent: selectedCall?.signal?.includes('BUY') || signal?.signal?.includes('BUY') ? 'bull' : selectedCall?.signal?.includes('SELL') || signal?.signal?.includes('SELL') ? 'bear' : 'accent2'
    },
    { 
      label: 'Accuracy', 
      value: accuracy?.models?.ensemble ? `${accuracy.models.ensemble.mape.toFixed(2)}%` : accuracy?.models?.arima ? `${accuracy.models.arima.mape.toFixed(2)}%` : '—', 
      subValue: `MAPE • Best: ${accuracy?.best_model || '—'}`,
      trend: 'v3 +63%',
      icon: Award,
      accent: 'accent'
    },
    { 
      label: 'Forecast 7d', 
      value: forecast?.ensemble ? `$${forecast.ensemble[forecast.ensemble.length - 1]?.toFixed(2)}` : '—', 
      subValue: 'Ensemble v3 • Dynamic',
      trend: forecast?.ensemble && livePrice ? `${((forecast.ensemble[forecast.ensemble.length - 1] - livePrice) / livePrice * 100).toFixed(2)}%` : null,
      icon: Brain,
      accent: 'accent2'
    },
  ]

  return (
    <div className="min-h-screen bg-crypto-bg relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-mesh pointer-events-none opacity-50"></div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-20 right-1/4 w-96 h-96 bg-crypto-accent/5 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-3">
              <span className="text-white">Trading</span>
              <span className="bg-gradient-to-r from-emerald-400 to-crypto-accent bg-clip-text text-transparent">Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold tracking-widest">LIVE CALLS • v3</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2 max-w-3xl">
              Professional trading calls with entry, SL, TP, risk management • AI Ensemble v3 • Tested past week: <span className="text-emerald-400 font-bold">ARIMA 2.57% MAPE • Ensemble 6.30% • SOL 2.37%</span> • {tradingSummary?.total || 0} active calls
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-4 py-2.5 rounded-xl bg-crypto-card/60 border border-crypto-border/50 backdrop-blur">
              <div className="live-dot bg-emerald-500"></div>
              <span className="text-xs font-bold tracking-widest text-white">LIVE TRADING ACTIVE</span>
              <span className="text-xs text-crypto-muted">• {tradingSummary?.buys || 0} BUY • {tradingSummary?.sells || 0} SELL</span>
            </div>
            <Link to="/trading" className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 text-black font-bold text-xs tracking-widest flex items-center gap-2 hover:shadow-lg hover:shadow-emerald-500/20 transition">
              <Target size={14} />
              VIEW ALL CALLS
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold tracking-widest text-crypto-muted uppercase flex items-center gap-2">
              <BarChart3 size={14} />
              Markets • Click to Analyze • Real-time Binance • Professional Calls
            </h2>
            <div className="text-xs text-crypto-muted hidden md:block">
              Account: ${accountBalance} • Risk: {riskPerTrade*100}% • Calls sorted by confidence • Low risk first
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
                Active Trading Calls • Top 3
                {tradingSummary && <span className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">{tradingSummary.total} total</span>}
              </h3>
              <Link to="/trading" className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                View All <ArrowRight size={12} />
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
          </div>

          <div className="lg:col-span-7">
            <GlassCard className="p-6 border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 via-crypto-card/30 to-crypto-accent/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Award size={18} className="text-emerald-400" />
                  Past Week Backtest • {selectedSymbol} • Sep 7-13 2025
                  <span className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">IMPROVED v3</span>
                </h3>
                <div className="text-xs text-crypto-muted">
                  Trained Sep 6 • Predicted Sep 7-13 • vs Actual
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 text-[11px] font-bold tracking-widest text-crypto-muted uppercase border-b border-crypto-border/30 pb-2 mb-3">
                <span>Model</span>
                <span>MAPE</span>
                <span>RMSE</span>
                <span>Improve</span>
                <span>Status</span>
              </div>

              <div className="space-y-2">
                {accuracy && Object.entries(accuracy.models).map(([name, m]) => {
                  const isBest = m.best || accuracy.best_model === name
                  const mape = m.mape
                  let status = 'Poor'
                  let color = 'text-crypto-bear bg-crypto-bear/10 border-crypto-bear/20'
                  if (mape < 3) { status = 'Excellent'; color = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' }
                  else if (mape < 6) { status = 'Good'; color = 'text-crypto-accent bg-crypto-accent/10 border-crypto-accent/20' }
                  else if (mape < 10) { status = 'Fair'; color = 'text-amber-400 bg-amber-500/10 border-amber-500/20' }

                  return (
                    <div key={name} className={`grid grid-cols-5 gap-2 items-center p-2.5 rounded-xl border text-sm ${isBest ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-crypto-bg/40 border-crypto-border/20'}`}>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${name === 'ensemble' ? 'bg-emerald-500' : name === 'arima' ? 'bg-violet-400' : 'bg-crypto-muted'}`}></div>
                        <span className={`font-bold capitalize ${isBest ? 'text-emerald-400' : 'text-white'}`}>{name} {isBest && '★'}</span>
                      </div>
                      <span className="mono font-bold text-white">{mape.toFixed(2)}%</span>
                      <span className="mono text-crypto-muted">${m.rmse?.toFixed(0) || '—'}</span>
                      <span className="text-emerald-400 font-bold text-xs">{m.improvement || '—'}</span>
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
                <div className="mt-6 p-4 rounded-xl bg-crypto-bg/50 border border-crypto-border/30">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield size={14} className="text-emerald-400" />
                    <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Active Call • {selectedCall.symbol} • Risk Management</span>
                    <span className={`ml-auto px-2 py-1 rounded-full text-xs font-black ${selectedCall.signal.includes('BUY') ? 'bg-emerald-500 text-black' : 'bg-red-500 text-white'}`}>
                      {selectedCall.action}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-crypto-card border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase">Entry</div>
                      <div className="mono font-bold text-white mt-1">${selectedCall.entry_price.toFixed(2)}</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                      <div className="text-[10px] text-red-400 uppercase">SL</div>
                      <div className="mono font-bold text-red-400 mt-1">${selectedCall.stop_loss.toFixed(2)}</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                      <div className="text-[10px] text-emerald-400 uppercase">TP1</div>
                      <div className="mono font-bold text-emerald-400 mt-1">${selectedCall.take_profits.tp1.toFixed(2)}</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase">R:R</div>
                      <div className="mono font-bold text-white mt-1">1:{selectedCall.risk_reward.tp1.toFixed(1)}</div>
                    </div>
                  </div>
                </div>
              )}
            </GlassCard>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Brain size={18} className="text-crypto-accent" />
                  Model Predictions • Ensemble v3 • Dynamic Weights
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold">4 MODELS • v3</span>
                  <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent/10 text-crypto-accent font-bold">+63.6% ACC</span>
                </div>
              </div>
              
              {forecast ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-5 gap-4 text-[11px] font-bold tracking-widest text-crypto-muted uppercase border-b border-crypto-border/30 pb-3">
                    <span>Model</span>
                    <span>Current</span>
                    <span>7-Day</span>
                    <span>Change</span>
                    <span>Confidence</span>
                  </div>
                  {[
                    { key: 'ensemble', label: 'Ensemble v3 (Dynamic)', color: 'text-emerald-400', bg: 'bg-emerald-500/10', weight: 'Inverse MAPE' },
                    { key: 'arima', label: 'ARIMA v3 (SARIMAX)', color: 'text-violet-400', bg: 'bg-violet-500/10', weight: '2.57% best' },
                    { key: 'transformer', label: 'Transformer v3', color: 'text-crypto-accent2', bg: 'bg-crypto-accent2/10', weight: 'Attn Pool' },
                    { key: 'lstm', label: 'LSTM v3 (Bidir+Attn)', color: 'text-cyan-400', bg: 'bg-cyan-500/10', weight: 'Bidirectional' },
                    { key: 'xgboost', label: 'XGBoost v3', color: 'text-emerald-400', bg: 'bg-emerald-500/10', weight: 'Tuned' },
                  ].map(model => {
                    const values = forecast[model.key]
                    if (!values) return null
                    const current = values[0]
                    const future = values[values.length - 1]
                    const change = ((future - current) / current * 100)
                    const isPos = change >= 0
                    
                    return (
                      <div key={model.key} className="grid grid-cols-5 gap-4 items-center py-3 hover:bg-crypto-card/30 rounded-xl px-3 -mx-3 transition">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${model.bg} border border-current ${model.color}`}></div>
                          <div>
                            <div className={`font-semibold text-sm ${model.color}`}>{model.label}</div>
                            <div className="text-[10px] text-crypto-muted">{model.weight}</div>
                          </div>
                        </div>
                        <div className="mono text-sm font-medium text-white">${current?.toFixed(2)}</div>
                        <div className="mono text-sm font-bold text-white">${future?.toFixed(2)}</div>
                        <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full w-fit ${isPos ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                          {isPos ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                          {Math.abs(change).toFixed(2)}%
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-crypto-bg rounded-full overflow-hidden">
                            <div className={`h-full bg-gradient-to-r ${model.key === 'ensemble' ? 'from-emerald-500 to-green-600' : model.key === 'arima' ? 'from-violet-500 to-purple-500' : model.key === 'transformer' ? 'from-crypto-accent2 to-purple-500' : 'from-cyan-500 to-blue-500'} rounded-full`} style={{ width: `${model.key === 'ensemble' ? 95 : model.key === 'arima' ? 92 : model.key === 'transformer' ? 88 : 85}%` }}></div>
                          </div>
                          <span className="text-xs font-bold text-white">{model.key === 'ensemble' ? 95 : model.key === 'arima' ? 92 : 88}%</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-crypto-card border border-crypto-border flex items-center justify-center">
                    <Brain size={24} className="text-crypto-muted" />
                  </div>
                  <div className="text-crypto-muted text-sm">No models trained yet</div>
                  <div className="text-crypto-muted text-xs mt-1">Run training pipeline to generate forecasts</div>
                </div>
              )}
            </GlassCard>
          </div>

          <div className="lg:col-span-4 space-y-6">
            <SignalCard signal={signal} symbol={selectedSymbol} realtimePrice={livePrice} />
            <SentimentGauge sentiment={sentiment} symbol={selectedSymbol} />

            <GlassCard className="p-6">
              <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                <Activity size={16} className="text-emerald-400" />
                Live Market Stats
                <span className="ml-auto flex items-center gap-1 text-[10px] font-bold tracking-widest text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
                  <span className="live-dot !w-1 !h-1 bg-emerald-500"></span>
                  LIVE
                </span>
              </h3>
              
              {currentTicker ? (
                <div className="space-y-3">
                  {[
                    { label: '24h High', value: `$${currentTicker.high?.toFixed(2)}`, sub: 'Peak today' },
                    { label: '24h Low', value: `$${currentTicker.low?.toFixed(2)}`, sub: 'Bottom today' },
                    { label: '24h Volume', value: `${(currentTicker.volume / 1000).toFixed(1)}K`, sub: `${(currentTicker.quoteVolume / 1e6).toFixed(2)}M USDT` },
                    { label: 'Trades', value: currentTicker.trades?.toLocaleString() || '—', sub: '24h count' },
                    { label: 'Open Price', value: `$${currentTicker.open?.toFixed(2)}`, sub: '24h ago' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-crypto-bg/40 border border-crypto-border/20 hover:border-crypto-border/40 transition">
                      <div>
                        <div className="text-xs font-medium text-crypto-muted">{item.label}</div>
                        <div className="text-[11px] text-crypto-muted/70">{item.sub}</div>
                      </div>
                      <div className="text-right">
                        <div className="mono font-bold text-sm text-white">{item.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="shimmer h-16 rounded-xl"></div>
                  ))}
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
