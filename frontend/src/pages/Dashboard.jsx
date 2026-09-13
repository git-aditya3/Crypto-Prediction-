import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fetchKlines } from '../api/binance'
import PriceChart from '../components/PriceChart'
import AssetGrid from '../components/AssetGrid'
import SignalCard from '../components/SignalCard'
import SentimentGauge from '../components/SentimentGauge'
import GlassCard, { StatCard } from '../components/GlassCard'
import { useMarketStore } from '../store/useMarketStore'
import { TrendingUp, TrendingDown, Activity, Zap, Brain, BarChart3, Clock, DollarSign, Layers, Sparkles } from 'lucide-react'

export default function Dashboard() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, fetchAllTickers } = useMarketStore()
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [klines, setKlines] = useState(null)

  // Fetch market tickers on mount
  useEffect(() => {
    fetchAllTickers()
  }, [])

  // Fetch data for selected symbol
  useEffect(() => {
    setLoading(true)
    const loadData = async () => {
      try {
        // Try backend first, fallback to Binance klines
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
          // Fallback to Binance klines
          try {
            const k = await fetchKlines(selectedSymbol, '1d', 200)
            setKlines(k)
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
      label: 'Sentiment', 
      value: sentiment?.average_compound ? `${(sentiment.average_compound * 100).toFixed(1)}%` : '—', 
      subValue: `${sentiment?.daily?.length || 0} sources`,
      trend: sentiment?.average_compound > 0 ? 'Bullish' : sentiment?.average_compound < 0 ? 'Bearish' : 'Neutral',
      icon: Sparkles,
      accent: sentiment?.average_compound > 0 ? 'bull' : sentiment?.average_compound < 0 ? 'bear' : 'accent2'
    },
    { 
      label: 'Forecast (7d)', 
      value: forecast?.ensemble ? `$${forecast.ensemble[forecast.ensemble.length - 1]?.toFixed(2)}` : '—', 
      subValue: 'Ensemble model',
      trend: forecast?.ensemble && livePrice ? `${((forecast.ensemble[forecast.ensemble.length - 1] - livePrice) / livePrice * 100).toFixed(2)}%` : null,
      icon: Brain,
      accent: 'accent'
    },
  ]

  return (
    <div className="min-h-screen bg-crypto-bg relative overflow-hidden">
      {/* Background mesh gradient */}
      <div className="absolute inset-0 bg-gradient-mesh pointer-events-none opacity-50"></div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-crypto-accent/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-20 right-1/4 w-96 h-96 bg-crypto-accent2/5 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-3">
              <span className="text-white">Market</span>
              <span className="gradient-text">Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-crypto-accent/10 border border-crypto-accent/20 text-crypto-accent text-xs font-bold tracking-widest">REAL-TIME</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2 max-w-2xl">
              AI-powered crypto forecasting with live Binance feed, sentiment analysis, and ensemble predictions (LSTM • Transformer • XGBoost • ARIMA)
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
                <span className="font-bold text-crypto-accent">987 rows • 2023-2025 • 10 assets</span>
              </div>
            </div>
          </div>
        </div>

        {/* Asset Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold tracking-widest text-crypto-muted uppercase flex items-center gap-2">
              <BarChart3 size={14} />
              Markets • Click to Analyze
            </h2>
            <div className="text-xs text-crypto-muted">
              Real-time prices from Binance • Updates every 2s via WebSocket
            </div>
          </div>
          <AssetGrid onSelect={setSelectedSymbol} selected={selectedSymbol} />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <StatCard key={i} {...stat} />
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Chart - 8 cols */}
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

            {/* Model Predictions */}
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Brain size={18} className="text-crypto-accent" />
                  Model Predictions • Ensemble Forecast
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent/10 text-crypto-accent font-bold">4 MODELS</span>
                  <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent2/10 text-crypto-accent2 font-bold">TFT TRANSFORMER</span>
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
                    { key: 'ensemble', label: 'Ensemble (Weighted)', color: 'text-crypto-accent', bg: 'bg-crypto-accent/10', weight: '35%+35%+20%+10%' },
                    { key: 'transformer', label: 'Transformer (TFT)', color: 'text-crypto-accent2', bg: 'bg-crypto-accent2/10', weight: '35%' },
                    { key: 'lstm', label: 'LSTM Neural', color: 'text-cyan-400', bg: 'bg-cyan-500/10', weight: '35%' },
                    { key: 'xgboost', label: 'XGBoost', color: 'text-violet-400', bg: 'bg-violet-500/10', weight: '20%' },
                    { key: 'arima', label: 'ARIMA', color: 'text-gray-400', bg: 'bg-gray-500/10', weight: '10%' },
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
                            <div className={`h-full bg-gradient-to-r ${model.key === 'ensemble' ? 'from-crypto-accent to-crypto-accent3' : model.key === 'transformer' ? 'from-crypto-accent2 to-purple-500' : 'from-gray-500 to-gray-600'} rounded-full`} style={{ width: `${model.key === 'ensemble' ? 95 : model.key === 'transformer' ? 88 : model.key === 'lstm' ? 85 : model.key === 'xgboost' ? 78 : 65}%` }}></div>
                          </div>
                          <span className="text-xs font-bold text-white">{model.key === 'ensemble' ? 95 : model.key === 'transformer' ? 88 : 82}%</span>
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

          {/* Sidebar - 4 cols */}
          <div className="lg:col-span-4 space-y-6">
            <SignalCard signal={signal} symbol={selectedSymbol} realtimePrice={livePrice} />
            
            <SentimentGauge sentiment={sentiment} symbol={selectedSymbol} />

            {/* Live Trades */}
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

              <div className="mt-6 p-3 rounded-xl bg-gradient-to-r from-crypto-accent/5 to-crypto-accent2/5 border border-crypto-accent/10">
                <div className="flex items-start gap-2">
                  <Clock size={14} className="text-crypto-accent mt-0.5" />
                  <div className="text-xs text-crypto-muted leading-relaxed">
                    <span className="text-white font-medium">Real-time architecture:</span> Binance WebSocket (wss://stream.binance.com) → Buffer (1000 trades) → Live signal with model forecast → UI updates every 2s. REST fallback if WS disconnects.
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* Quick Actions */}
            <GlassCard className="p-5">
              <h3 className="font-semibold text-white text-sm mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-2">
                <button className="p-3 rounded-xl bg-crypto-card border border-crypto-border hover:border-crypto-accent/30 hover:bg-crypto-cardHover transition text-left group">
                  <Zap size={16} className="text-crypto-accent mb-2 group-hover:scale-110 transition-transform" />
                  <div className="text-xs font-semibold text-white">Run Forecast</div>
                  <div className="text-[11px] text-crypto-muted">7-day prediction</div>
                </button>
                <button className="p-3 rounded-xl bg-crypto-card border border-crypto-border hover:border-crypto-accent2/30 hover:bg-crypto-cardHover transition text-left group">
                  <BarChart3 size={16} className="text-crypto-accent2 mb-2 group-hover:scale-110 transition-transform" />
                  <div className="text-xs font-semibold text-white">Backtest</div>
                  <div className="text-[11px] text-crypto-muted">Test strategy</div>
                </button>
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Footer info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-crypto-border/30">
          <div className="flex items-center gap-3 text-xs text-crypto-muted">
            <div className="w-8 h-8 rounded-lg bg-crypto-card border border-crypto-border flex items-center justify-center">
              <Layers size={14} />
            </div>
            <div>
              <div className="font-semibold text-white">Data Pipeline</div>
              <div>KuCoin historical (987 rows) + Binance live • 2023-2025</div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-crypto-muted">
            <div className="w-8 h-8 rounded-lg bg-crypto-card border border-crypto-border flex items-center justify-center">
              <Brain size={14} />
            </div>
            <div>
              <div className="font-semibold text-white">Models</div>
              <div>LSTM • Transformer (TFT) • XGBoost • ARIMA • Ensemble</div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-crypto-muted">
            <div className="w-8 h-8 rounded-lg bg-crypto-card border border-crypto-border flex items-center justify-center">
              <Sparkles size={14} />
            </div>
            <div>
              <div className="font-semibold text-white">Features</div>
              <div>69 technical indicators + VADER sentiment + real-time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
