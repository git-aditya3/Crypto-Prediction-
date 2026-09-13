import { useEffect } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function MarketTicker() {
  const { tickers, fetchAllTickers, isLive, startLive } = useMarketStore()

  useEffect(() => {
    fetchAllTickers()
    const interval = setInterval(fetchAllTickers, 30000) // refresh every 30s
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Auto-start live after first fetch
    if (Object.keys(tickers || {}).length > 0 && !isLive) {
      startLive()
    }
  }, [tickers])

  const items = Object.values(tickers || {})
  // Duplicate for seamless loop
  const loopItems = [...items, ...items]

  if (items.length === 0) {
    return (
      <div className="h-10 bg-crypto-card border-b border-crypto-border flex items-center px-6 text-sm text-crypto-muted">
        <div className="flex items-center gap-2">
          <div className="live-dot"></div>
          <span>Connecting to Binance live feed...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="h-11 bg-gradient-to-r from-crypto-card via-crypto-card to-crypto-bg border-b border-crypto-border/50 overflow-hidden relative">
      {/* Live indicator */}
      <div className="absolute left-0 top-0 bottom-0 z-10 flex items-center gap-3 px-6 bg-gradient-to-r from-crypto-card to-transparent backdrop-blur-sm border-r border-crypto-border/30">
        <div className="flex items-center gap-2">
          <div className="live-dot"></div>
          <span className="text-xs font-bold tracking-widest text-crypto-accent">LIVE</span>
        </div>
        <div className="h-4 w-px bg-crypto-border"></div>
        <span className="text-[11px] text-crypto-muted font-medium hidden md:block">BINANCE REAL-TIME</span>
      </div>

      <div className="ticker-wrap h-full flex items-center ml-[160px]">
        <div className="ticker flex items-center gap-8">
          {loopItems.map((t, i) => {
            const isPositive = (t.priceChangePercent ?? 0) >= 0
            const price = t.price ?? 0
            return (
              <div key={`${t.symbol}-${i}`} className="flex items-center gap-3 shrink-0 group cursor-pointer hover:opacity-80 transition">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-crypto-cardHover to-crypto-border flex items-center justify-center text-[10px] font-bold border border-crypto-border group-hover:border-crypto-accent/30 transition">
                    {(t.symbol || 'BTC').split('-')[0].slice(0, 3)}
                  </div>
                  <span className="font-semibold text-sm text-white tracking-tight">{t.symbol || 'Unknown'}</span>
                </div>
                <span className="mono text-sm font-medium text-white">${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}</span>
                <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${isPositive ? 'bg-crypto-bull/10 text-crypto-bull' : 'bg-crypto-bear/10 text-crypto-bear'}`}>
                  {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {Math.abs(t.priceChangePercent ?? 0).toFixed(2)}%
                </div>
                <div className="h-3 w-px bg-crypto-border/50 hidden lg:block"></div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Fade edges */}
      <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-crypto-bg to-transparent pointer-events-none"></div>
    </div>
  )
}
