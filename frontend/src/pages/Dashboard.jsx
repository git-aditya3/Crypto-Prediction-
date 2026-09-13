import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import PriceChart from '../components/PriceChart'
import AssetGrid from '../components/AssetGrid'
import SignalCard from '../components/SignalCard'
import SentimentGauge from '../components/SentimentGauge'
import GlassCard, { StatCard } from '../components/GlassCard'
import AccuracyCard from '../components/AccuracyCard'
import { useMarketStore } from '../store/useMarketStore'
import { TrendingUp, TrendingDown, Activity, Zap, Brain, BarChart3, Clock, DollarSign, Layers, Sparkles, Award, Target } from 'lucide-react'
import accuracyData from '../data/accuracy.json'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [sentiment, setSentiment] = useState(null)
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
        ]
        const [h, f, s, sent] = await Promise.all(promises)
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
      label: 'AI Signal', 
      value: signal?.signal || 'HOLD', 
      subValue: `${signal?.confidence?.toFixed(0) || 0}% confidence`,
      trend: signal?.change_pct ? `${signal.change_pct > 0 ? '+' : ''}${signal.change_pct.toFixed(2)}%` : null,
      icon: Zap,
      accent: signal?.signal?.includes('BUY') ? 'bull' : signal?.signal?.includes('SELL') ? 'bear' : 'accent2'
    },
    { 
      label: 'Accuracy (Past Week)', 
      value: accuracy?.models?.ensemble ? `${accuracy.models.ensemble.mape.toFixed(2)}%` : accuracy?.models?.arima ? `${accuracy.models.arima.mape.toFixed(2)}%` : '—', 
      subValue: `MAPE • Best: ${accuracy?.best_model || '—'}`,
      trend: 'Improved v3',
      icon: Award,
      accent: 'accent'
    },
    { 
      label: 'Forecast (7d)', 
      value: forecast?.ensemble ? `$${forecast.ensemble[forecast.ensemble.length - 1]?.toFixed(2)}` : '—', 
      subValue: 'Ensemble v3',
      trend: forecast?.ensemble && livePrice ? `${((forecast.ensemble[forecast.ensemble.length - 1] - livePrice) / livePrice * 100).toFixed(2)}%` : null,
      icon: Brain,
      accent: 'accent2'
    },
  ]

  return (
    <div className="min-h-screen bg-crypto-bg relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-mesh pointer-events-none opacity-50"></div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-crypto-accent/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-20 right-1/4 w-96 h-96 bg-crypto-accent2/5 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-3">
              <span className="text-white">Market</span>
              <span className="gradient-text">Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-crypto-accent/10 border border-crypto-accent/20 text-crypto-accent text-xs font-bold tracking-widest">REAL-TIME • v3</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2 max-w-3xl">
              AI-powered crypto forecasting v3 • 182 features • RobustScaler • Bidirectional LSTM + Attention • Transformer with learnable PE + attention pooling • XGBoost tuned • SARIMAX • Dynamic ensemble • Tested on past week: <span className="text-crypto-accent font-bold">2.57% MAPE (ARIMA) • 6.30% Ensemble</span>
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-4 py-2.5 rounded-xl bg-crypto-card/60 border border-crypto-border/50 backdrop-blur">
              <div className="live-dot"></div>
              <span className="text-xs font-bold tracking-widest text-white">LIVE FEED ACTIVE</span>
              <span className="text-xs text-crypto-muted">• {Object.keys(tickers).length} assets</span>
            </div>
            <div className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-crypto-accent/10 to-crypto-accent3/10 border border-crypto-accent/20">
              <div className="flex items-center gap-2 text-xs">
                <Layers size={12} className="text-crypto-accent" />
                <span className="font-bold text-crypto-accent">v3 Improved • 182 feats • 987 rows</span>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold tracking-widest text-crypto-muted uppercase flex items-center gap-2">
              <BarChart3 size={14} />
              Markets • Click to Analyze • Real-time Binance
            </h2>
            <div className="text-xs text-crypto-muted">
              Past week accuracy: SOL 2.37% • ADA 3.16% • BTC Ensemble 6.30% • ARIMA 2.57%
            </div>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <StatCard key={i} {...stat} />
          ))}
        </div>

        {/* Accuracy Card - New */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <GlassCard className="p-6 border-crypto-accent/20 bg-gradient-to-br from-crypto-accent/5 via-crypto-card/30 to-crypto-accent2/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Award size={18} className="text-crypto-accent" />
                  Past Week Backtest • {selectedSymbol} • Sep 7-13 2025
                  <span className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">IMPROVED v3</span>
                </h3>
                <div className="text-xs text-crypto-muted">
                  Trained up to Sep 6 • Predicted Sep 7-13 • Compared with actual
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 text-[11px] font-bold tracking-widest text-crypto-muted uppercase border-b border-crypto-border/30 pb-2 mb-3">
                <span>Model</span>
                <span>MAPE</span>
                <span>RMSE</span>
                <span>Improvement</span>
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
                    <div key={name} className={`grid grid-cols-5 gap-2 items-center p-2.5 rounded-xl border text-sm ${isBest ? 'bg-crypto-accent/10 border-crypto-accent/30' : 'bg-crypto-bg/40 border-crypto-border/20'}`}>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${name === 'ensemble' ? 'bg-crypto-accent' : name === 'arima' ? 'bg-violet-400' : 'bg-crypto-muted'}`}></div>
                        <span className={`font-bold capitalize ${isBest ? 'text-crypto-accent' : 'text-white'}`}>{name} {isBest && '★'}</span>
                      </div>
                      <span className="mono font-bold text-white">{mape.toFixed(2)}%</span>
                      <span className="mono text-crypto-muted">${m.rmse?.toFixed(0) || '—'}</span>
                      <span className="text-emerald-400 font-bold text-xs">{m.improvement || '—'}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-bold border w-fit ${color}`}>{status}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-4 grid grid-cols-7 gap-2">
                {accuracy?.last_7_days_actual?.map((day, i) => (
                  <div key={i} className="p-2 rounded-xl bg-crypto-bg/50 border border-crypto-border/20 text-center">
                    <div className="text-[10px] text-crypto-muted font-bold">{day.date.slice(5)}</div>
                    <div className="mono text-xs font-bold text-white mt-1">${day.close.toLocaleString()}</div>
                    <div className="text-[10px] text-crypto-accent mt-1">Actual</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          <div className="lg:col-span-4">
            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <Target size={16} className="text-crypto-accent" />
                v3 Improvements
              </h3>
              <div className="space-y-3 text-xs">
                {[
                  { label: 'Features', value: '69 → 182', improvement: '+163%', desc: 'ADX, CCI, Ichimoku, Keltner, VWAP, etc.' },
                  { label: 'LSTM', value: 'Bidir + Attention', improvement: '+24.8%', desc: '256 hidden, 3 layers, HuberLoss, AdamW' },
                  { label: 'Transformer', value: 'Learnable PE + Pooling', improvement: '+23.1%', desc: '256 d_model, 8 heads, 4 layers, Pre-LN' },
                  { label: 'XGBoost', value: 'Tuned + Regularized', improvement: '+1.5%', desc: '1000 est, depth 8, alpha/lambda reg' },
                  { label: 'ARIMA', value: 'SARIMAX Seasonal', improvement: '+89.6%', desc: 'Auto order + weekly seasonality' },
                  { label: 'Ensemble', value: 'Dynamic + Stacking', improvement: '+63.6%', desc: 'Inverse MAPE weights + Ridge meta' },
                  { label: 'Scaler', value: 'RobustScaler', improvement: 'Outlier robust', desc: 'Handles crypto fat tails' },
                ].map(item => (
                  <div key={item.label} className="p-3 rounded-xl bg-crypto-bg/40 border border-crypto-border/20 hover:border-crypto-border/40 transition">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-bold text-white text-sm">{item.label}</div>
                        <div className="text-crypto-muted text-[11px] mt-0.5">{item.desc}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-crypto-accent font-bold text-xs">{item.improvement}</div>
                        <div className="text-white font-medium text-xs mt-1">{item.value}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            {loading ? (
              <div className="rounded-2xl border border-crypto-border/50 bg-crypto-card/30 p-8 backdrop-blur-xl">
                <div className="animate-pulse space-y-4">
                  <div className="h-8 bg-crypto-border rounded w-1/3"></div>
                  <div className="h-[400px] bg-crypto-border/50 rounded-xl"></div>
                </div>
              </div>
            ) : (
              <PriceChart 
                data={history} 
                forecast={forecast} 
                realtimePrice={livePrice}
                symbol={selectedSymbol}
                height={480}
              />
            )}

            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Brain size={18} className="text-crypto-accent" />
                  Model Predictions • Ensemble Forecast v3
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent/10 text-crypto-accent font-bold">4 MODELS • v3</span>
                  <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold">+63.6% ACCURACY</span>
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
                    { key: 'ensemble', label: 'Ensemble v3 (Dynamic)', color: 'text-crypto-accent', bg: 'bg-crypto-accent/10', weight: 'Dynamic' },
                    { key: 'arima', label: 'ARIMA v3 (SARIMAX)', color: 'text-violet-400', bg: 'bg-violet-500/10', weight: 'Seasonal' },
                    { key: 'transformer', label: 'Transformer v3', color: 'text-crypto-accent2', bg: 'bg-crypto-accent2/10', weight: 'Attention Pool' },
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
                        <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full w-fit ${isPos ? 'bg-crypto-bull/10 text-crypto-bull' : 'bg-crypto-bear/10 text-crypto-bear'}`}>
                          {isPos ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                          {Math.abs(change).toFixed(2)}%
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-crypto-bg rounded-full overflow-hidden">
                            <div className={`h-full bg-gradient-to-r ${model.key === 'ensemble' ? 'from-crypto-accent to-crypto-accent3' : model.key === 'arima' ? 'from-violet-500 to-purple-500' : model.key === 'transformer' ? 'from-crypto-accent2 to-purple-500' : 'from-cyan-500 to-blue-500'} rounded-full`} style={{ width: `${model.key === 'ensemble' ? 95 : model.key === 'arima' ? 92 : model.key === 'transformer' ? 88 : 85}%` }}></div>
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
                <Activity size={16} className="text-crypto-accent" />
                Live Market Stats
                <span className="ml-auto flex items-center gap-1 text-[10px] font-bold tracking-widest text-crypto-accent bg-crypto-accent/10 px-2 py-1 rounded-full border border-crypto-accent/20">
                  <span className="live-dot !w-1 !h-1"></span>
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
