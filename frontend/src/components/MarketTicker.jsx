import { useEffect } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { TrendingUp, TrendingDown, Activity, Zap } from 'lucide-react'

export default function MarketTicker() {
  const { tickers, fetchAllTickers, isLive, startLive } = useMarketStore()
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)

  useEffect(() => {
    fetchAllTickers()
    const interval = setInterval(fetchAllTickers, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (Object.keys(tickers || {}).length > 0 && !isLive) {
      startLive()
    }
  }, [tickers])

  const items = Object.values(tickers || {})
  const loopItems = items.length > 0 ? [...items, ...items, ...items] : []

  if (items.length === 0) {
    return (
      <div className={`sticky top-0 z-[100] h-12 flex items-center px-4 text-[12px] font-medium border-b backdrop-blur-xl glass ${isLight ? 'bg-white/90 border-black/5 text-zinc-600' : 'bg-[var(--bg)]/90 border-[var(--border)] text-zinc-400'}`}>
        <div className="flex items-center gap-3">
          <div className="live-dot"></div>
          <span className="font-bold">Connecting to live market feed</span>
          <span className="flex gap-1">
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </span>
          <span className={`hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold ${isLight ? 'bg-black/5 text-zinc-600' : 'bg-white/5 text-zinc-400'}`}>
            <Activity size={10} /> BINANCE + COINDCX
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`sticky top-0 z-[100] h-12 overflow-hidden flex items-center border-b backdrop-blur-xl glass ${isLight ? 'bg-white/90 border-black/5' : 'bg-[var(--bg)]/90 border-[var(--border)]'}`}>
      {/* Left LIVE badge - fixed */}
      <div className={`absolute left-0 top-0 bottom-0 z-20 flex items-center gap-3 px-5 border-r backdrop-blur-xl ${isLight ? 'bg-white border-black/5' : 'bg-[var(--bg)] border-[var(--border)]'} glass`}>
        <div className="relative">
          <div className="live-dot"></div>
          <div className="absolute inset-0 live-dot animate-ping opacity-30" />
        </div>
        <span className="ui-pill-live px-3 py-1 text-[10px] rounded-full font-black tracking-wide shadow-lg">LIVE</span>
        <span className={`hidden md:flex items-center gap-1.5 text-[10px] font-bold tracking-wide px-2 py-1 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>
          <Zap size={10} className="text-[var(--accent)]" />
          BINANCE + COINDCX
        </span>
      </div>

      {/* Ticker track */}
      <div className="ticker-wrap h-full flex items-center" style={{ paddingLeft: '180px' }}>
        <div className="ticker flex items-center gap-3">
          {loopItems.map((t, i) => {
            const isPositive = (t.priceChangePercent ?? 0) >= 0
            const price = t.price ?? 0
            const symbol = t.symbol || 'BTC-USD'
            const shortSym = symbol.split('-')[0].slice(0, 4)
            const change = t.priceChangePercent ?? 0
            
            return (
              <div
                key={`${t.symbol}-${i}`}
                className={`group flex items-center gap-2.5 shrink-0 px-4 py-2 rounded-full border text-[12px] font-medium transition-all duration-300 hover:scale-105 hover:shadow-lg cursor-pointer ${
                  isLight
                    ? 'bg-zinc-50 border-black/5 hover:bg-white hover:border-black/10 hover:shadow-md'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-[var(--accent)]/30 hover:shadow-[var(--glow)]'
                }`}
              >
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-black shadow-md group-hover:scale-110 group-hover:rotate-3 transition-all ${isLight ? 'bg-black text-white' : 'bg-white text-black group-hover:bg-[var(--accent)] group-hover:text-[var(--bg)]'}`}>
                  {shortSym.slice(0, 3)}
                </span>
                <span className={`font-bold text-[12px] tracking-wide ${isLight ? 'text-zinc-900' : 'text-zinc-100'}`}>{symbol}</span>
                <span className={`mono font-bold ${isLight ? 'text-zinc-900' : 'text-white'} group-hover:text-[var(--accent)] transition-colors`}>
                  ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}
                </span>
                <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-black border transition-all group-hover:scale-105 ${
                  isPositive 
                    ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 group-hover:bg-emerald-500 group-hover:text-black' 
                    : 'bg-red-500/10 text-red-500 border-red-500/20 group-hover:bg-red-500 group-hover:text-white'
                }`}>
                  {isPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                  {Math.abs(change).toFixed(2)}%
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right fade + stats */}
      <div className={`absolute right-0 top-0 bottom-0 flex items-center gap-3 px-4 z-10 backdrop-blur-xl ${isLight ? 'bg-gradient-to-l from-white via-white to-transparent' : 'bg-gradient-to-l from-[var(--bg)] via-[var(--bg)] to-transparent'} border-l border-[var(--border)]`}>
        <div className={`hidden lg:flex items-center gap-2 text-[10px] font-bold px-2.5 py-1 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          {items.length} MARKETS
        </div>
      </div>
    </div>
  )
}
