import { useEffect, useState, useRef } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { fetchOrderBook, fetchRecentTrades, BinanceTradeWS } from '../api/binance'
import { api } from '../api/client'
import GlassCard from '../components/GlassCard'
import { Radio, Activity, TrendingUp, TrendingDown, Zap, BarChart3, Clock, Layers } from 'lucide-react'

const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)? (0).toFixed(d) : n.toFixed(d) }

export default function Realtime() {
  const { selectedSymbol, setSelectedSymbol, tickers, prices, isLive, startLive, stopLive } = useMarketStore()
  const [orderBook, setOrderBook] = useState(null)
  const [trades, setTrades] = useState([])
  const [liveTrades, setLiveTrades] = useState([])
  const [liveSignal, setLiveSignal] = useState(null)
  const tradeWsRef = useRef(null)

  const currentTicker = tickers[selectedSymbol]
  const livePrice = prices[selectedSymbol] || currentTicker?.price || 0

  // Fetch orderbook and recent trades
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ob, recent] = await Promise.all([
          fetchOrderBook(selectedSymbol, 15).catch(() => null),
          fetchRecentTrades(selectedSymbol, 20).catch(() => null)
        ])
        if (ob) setOrderBook(ob)
        if (recent) setTrades(recent)
      } catch (e) {
        console.warn('Orderbook fetch failed', e)
      }

      // Also try backend live signal
      try {
        const signal = await api.getSignal(selectedSymbol).catch(() => null)
        if (signal) setLiveSignal(signal)
      } catch {}
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [selectedSymbol])

  // Live trade WS
  useEffect(() => {
    if (tradeWsRef.current) {
      tradeWsRef.current.disconnect()
    }

    const ws = new BinanceTradeWS(selectedSymbol, (trade) => {
      setLiveTrades(prev => [trade, ...prev.slice(0, 49)])
    })
    ws.connect()
    tradeWsRef.current = ws

    return () => {
      ws.disconnect()
    }
  }, [selectedSymbol])

  // Ensure live ticker is running
  useEffect(() => {
    if (!isLive) startLive()
  }, [])

  const symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD']

  return (
    <div className="min-h-screen bg-crypto-bg relative">
      <div className="absolute inset-0 bg-gradient-mesh opacity-30 pointer-events-none"></div>
      
      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-crypto-accent to-crypto-accent2 flex items-center justify-center shadow-lg shadow-crypto-accent/20">
                <Radio size={20} className="text-black" />
              </span>
              <span className="text-white">Live Trading</span>
              <span className="px-3 py-1 rounded-full bg-crypto-bear/10 border border-crypto-bear/20 text-crypto-bear text-xs font-black tracking-widest animate-pulse flex items-center gap-2">
                <span className="w-2 h-2 bg-crypto-bear rounded-full animate-ping"></span>
                LIVE • BINANCE WS
              </span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2">
              Real-time Binance WebSocket feed • wss://stream.binance.com:9443 • Buffer 1000 trades • 2s UI refresh
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select 
              value={selectedSymbol} 
              onChange={e => setSelectedSymbol(e.target.value)} 
              className="bg-crypto-card border border-crypto-border rounded-xl px-4 py-2.5 text-sm font-medium text-white focus:border-crypto-accent/50 focus:outline-none"
            >
              {symbols.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            
            <button 
              onClick={() => isLive ? stopLive() : startLive()} 
              className={`px-5 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${
                isLive 
                  ? 'bg-crypto-bear text-white hover:bg-red-600 shadow-lg shadow-crypto-bear/20' 
                  : 'bg-crypto-bull text-black hover:bg-emerald-400 shadow-lg shadow-crypto-bull/20'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-white animate-pulse' : 'bg-black'}`}></div>
              {isLive ? 'Stop Live' : 'Start Live'}
            </button>
          </div>
        </div>

        {/* Live Price Hero */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <GlassCard className="p-8 relative overflow-hidden" gradient>
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-crypto-accent/10 to-crypto-accent2/10 rounded-full blur-[60px] pointer-events-none"></div>
              
              <div className="relative">
                <div className="flex items-start justify-between mb-8">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-2xl font-black text-white tracking-tight">{selectedSymbol}</h2>
                      <span className="px-2.5 py-1 rounded-full bg-crypto-accent/10 border border-crypto-accent/20 text-crypto-accent text-xs font-bold">
                        {currentTicker?.binanceSymbol || selectedSymbol.replace('-','')}
                      </span>
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-crypto-bg border border-crypto-border text-xs font-bold text-white">
                        <span className="live-dot !w-1.5 !h-1.5"></span>
                        LIVE
                      </span>
                    </div>
                    <div className="flex items-baseline gap-4">
                      <span className="text-5xl font-black mono tracking-tight text-white">
                        ${(livePrice ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: livePrice > 1000 ? 2 : 4 })}
                      </span>
                      <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold ${
                        (currentTicker?.priceChangePercent || 0) >= 0 
                          ? 'bg-crypto-bull/10 text-crypto-bull border border-crypto-bull/20' 
                          : 'bg-crypto-bear/10 text-crypto-bear border border-crypto-bear/20'
                      }`}>
                        {(currentTicker?.priceChangePercent || 0) >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {Math.abs(currentTicker?.priceChangePercent || 0).toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-sm text-crypto-muted mt-2">
                      24h Change: <span className={currentTicker?.priceChangePercent >= 0 ? 'text-crypto-bull' : 'text-crypto-bear'}>${safeFixed(currentTicker?.priceChange,2) || '0.00'}</span> • 
                      Volume: <span className="text-white font-medium">{(currentTicker?.volume ?? 0).toLocaleString()} {selectedSymbol.split('-')[0]}</span>
                    </div>
                  </div>

                  <div className="hidden md:block text-right">
                    <div className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2">Live Signal</div>
                    {liveSignal ? (
                      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl font-black text-sm border ${
                        liveSignal.signal?.includes('BUY') 
                          ? 'bg-crypto-bull/10 text-crypto-bull border-crypto-bull/20' 
                          : liveSignal.signal?.includes('SELL')
                            ? 'bg-crypto-bear/10 text-crypto-bear border-crypto-bear/20'
                            : 'bg-crypto-card text-crypto-muted border-crypto-border'
                      }`}>
                        <Zap size={14} />
                        {liveSignal.signal} • {safeFixed(liveSignal.confidence,0)}%
                      </div>
                    ) : (
                      <div className="px-4 py-2 rounded-xl bg-crypto-card border border-crypto-border text-crypto-muted text-sm">
                        Calculating...
                      </div>
                    )}
                  </div>
                </div>

                {/* Mini chart - live trades */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Live Price Action (Last 50 Trades)</span>
                    <span className="text-xs text-crypto-muted">{liveTrades.length} trades • Real-time</span>
                  </div>
                  <div className="h-24 flex items-end gap-0.5 p-3 rounded-xl bg-crypto-bg/50 border border-crypto-border/30">
                    {liveTrades.length > 0 ? (
                      liveTrades.slice(0, 50).reverse().map((trade, i) => {
                        const min = Math.min(...liveTrades.map(t => t.price))
                        const max = Math.max(...liveTrades.map(t => t.price))
                        const range = max - min || 1
                        const height = ((trade.price - min) / range) * 100
                        return (
                          <div
                            key={i}
                            className={`flex-1 rounded-t transition-all duration-300 ${trade.isBuyerMaker ? 'bg-crypto-bear/60' : 'bg-crypto-bull/60'} hover:opacity-80`}
                            style={{ height: `${Math.max(4, height)}%` }}
                            title={`${trade.price} • ${trade.qty}`}
                          />
                        )
                      })
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-crypto-muted text-xs">
                        Waiting for live trades...
                      </div>
                    )}
                  </div>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-4 gap-3 mt-6">
                  {[
                    { label: 'High', value: currentTicker?.high, icon: TrendingUp, color: 'text-crypto-bull' },
                    { label: 'Low', value: currentTicker?.low, icon: TrendingDown, color: 'text-crypto-bear' },
                    { label: 'Open', value: currentTicker?.open, icon: Clock, color: 'text-crypto-muted' },
                    { label: 'Quote Vol', value: currentTicker?.quoteVolume ? `${safeFixed(currentTicker.quoteVolume/1e6,2)}M` : '—', icon: BarChart3, color: 'text-crypto-accent' },
                  ].map((stat, i) => (
                    <div key={i} className="p-3 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <stat.icon size={10} className={stat.color} />
                        <span className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">{stat.label}</span>
                      </div>
                      <div className="mono font-bold text-sm text-white">
                        {typeof stat.value === 'number' ? `$${stat.value.toFixed(2)}` : stat.value || '—'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Orderbook */}
          <div className="lg:col-span-4 space-y-6">
            <GlassCard className="p-6">
              <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                <Layers size={16} className="text-crypto-accent" />
                Order Book • {selectedSymbol}
                <span className="ml-auto text-[10px] px-2 py-1 rounded-full bg-crypto-card border border-crypto-border text-crypto-muted">LIVE</span>
              </h3>
              
              {orderBook ? (
                <div className="space-y-4">
                  {/* Asks */}
                  <div>
                    <div className="flex justify-between text-[10px] font-bold tracking-widest text-crypto-muted uppercase mb-2">
                      <span>Price (USDT)</span>
                      <span>Amount ({selectedSymbol.split('-')[0]})</span>
                      <span>Total</span>
                    </div>
                    <div className="space-y-1">
                      {orderBook.asks?.slice(0, 7).reverse().map((ask, i) => {
                        const price = parseFloat(ask[0])
                        const qty = parseFloat(ask[1])
                        return (
                          <div key={i} className="flex justify-between text-xs mono relative group hover:bg-crypto-bear/5 p-1 rounded transition">
                            <span className="text-crypto-bear font-medium">{(price ?? 0).toFixed(2)}</span>
                            <span className="text-white">{(qty ?? 0).toFixed(4)}</span>
                            <span className="text-crypto-muted">{((price ?? 0)*(qty ?? 0)).toFixed(2)}</span>
                            <div className="absolute inset-0 bg-crypto-bear/5 opacity-0 group-hover:opacity-100 rounded transition" style={{ width: `${Math.min(100, qty*10)}%`, right: 0, left: 'auto' }}></div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="py-2 flex items-center justify-center gap-2">
                    <div className="h-px flex-1 bg-crypto-border"></div>
                    <span className="text-xs font-black mono text-crypto-accent px-3 py-1 rounded-full bg-crypto-accent/10 border border-crypto-accent/20">
                      ${safeFixed(livePrice,2)}
                    </span>
                    <div className="h-px flex-1 bg-crypto-border"></div>
                  </div>

                  {/* Bids */}
                  <div className="space-y-1">
                    {orderBook.bids?.slice(0, 7).map((bid, i) => {
                      const price = parseFloat(bid[0])
                      const qty = parseFloat(bid[1])
                      return (
                        <div key={i} className="flex justify-between text-xs mono relative group hover:bg-crypto-bull/5 p-1 rounded transition">
                          <span className="text-crypto-bull font-medium">{(price ?? 0).toFixed(2)}</span>
                          <span className="text-white">{(qty ?? 0).toFixed(4)}</span>
                          <span className="text-crypto-muted">{((price ?? 0)*(qty ?? 0)).toFixed(2)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {[...Array(10)].map((_, i) => (
                    <div key={i} className="shimmer h-6 rounded"></div>
                  ))}
                </div>
              )}
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                <Activity size={16} className="text-crypto-accent2" />
                Recent Trades
              </h3>
              <div className="space-y-1 max-h-[300px] overflow-y-auto">
                {trades.length > 0 ? trades.slice(0, 15).map((trade, i) => {
                  const isBuy = !trade.isBuyerMaker
                  return (
                    <div key={i} className="flex justify-between items-center text-xs mono p-2 rounded-lg hover:bg-crypto-card/50 transition">
                      <span className={isBuy ? 'text-crypto-bull' : 'text-crypto-bear'}>{parseFloat(trade.price ?? 0).toFixed(2)}</span>
                      <span className="text-white">{parseFloat(trade.qty ?? 0).toFixed(4)}</span>
                      <span className="text-crypto-muted text-[11px]">{new Date(trade.time).toLocaleTimeString()}</span>
                    </div>
                  )
                }) : liveTrades.slice(0, 15).map((trade, i) => (
                  <div key={i} className="flex justify-between items-center text-xs mono p-2 rounded-lg hover:bg-crypto-card/50 transition">
                    <span className={trade.isBuyerMaker ? 'text-crypto-bear' : 'text-crypto-bull'}>{safeFixed(trade.price,2)}</span>
                    <span className="text-white">{safeFixed(trade.qty,4)}</span>
                    <span className="text-crypto-muted text-[11px]">{new Date(trade.time).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Architecture */}
        <GlassCard className="p-6">
          <h3 className="font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 size={16} className="text-crypto-accent" />
            Realtime Architecture • How It Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { step: '1', title: 'Binance WebSocket', desc: 'wss://stream.binance.com:9443/ws/*@ticker, @trade, @kline_1m', color: 'from-crypto-accent to-crypto-accent3' },
              { step: '2', title: 'Buffer & Manager', desc: 'Deque 1000 trades, RealtimeManager multi-symbol, auto-reconnect 5s', color: 'from-crypto-accent2 to-purple-500' },
              { step: '3', title: 'Live Predictor', desc: 'Merges live price with LSTM/Transformer forecast → live signal', color: 'from-cyan-500 to-blue-500' },
              { step: '4', title: 'React UI', desc: 'Zustand store, 2s refresh, lightweight-charts, live price lines', color: 'from-violet-500 to-purple-500' },
            ].map(item => (
              <div key={item.step} className="p-4 rounded-xl bg-crypto-bg/40 border border-crypto-border/30 hover:border-crypto-border/60 transition group">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center font-black text-black text-sm shadow-lg group-hover:scale-110 transition-transform`}>
                    {item.step}
                  </div>
                  <div className="font-bold text-white text-sm">{item.title}</div>
                </div>
                <div className="text-xs text-crypto-muted leading-relaxed">{item.desc}</div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
