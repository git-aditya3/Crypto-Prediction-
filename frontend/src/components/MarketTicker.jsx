import { useEffect, useMemo } from 'react'
import { useMarketStore } from '../store/useMarketStore'

export default function MarketTicker() {
  const { tickers, fetchAllTickers, isLive, startLive } = useMarketStore()

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

  const items = useMemo(() => Object.values(tickers || {}), [tickers])
  const loopItems = useMemo(() => items.length > 0 ? [...items, ...items, ...items] : [], [items])

  if (items.length === 0) {
    return (
      <div className="sticky top-0 z-[100] h-10 flex items-center px-4 text-[12px] font-medium border-b gpu-accelerated bg-[var(--card)]/90 border-[var(--border)] text-[var(--text-muted)] backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <div className="live-dot"></div>
          <span className="font-medium tracking-tight">Connecting to live market</span>
          <span className="flex gap-1">
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="sticky top-0 z-[100] h-10 overflow-hidden flex items-center border-b gpu-accelerated bg-[var(--card)]/90 border-[var(--border)] backdrop-blur-xl" style={{ transform: 'translateZ(0)' }}>
      <div className="absolute left-0 top-0 bottom-0 z-20 flex items-center gap-2.5 px-4 border-r bg-[var(--card)] border-[var(--border)] backdrop-blur-xl">
        <div className="live-dot"></div>
        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wide bg-[var(--accent)] text-white shadow-sm">LIVE</span>
        <span className="hidden md:inline text-[10px] font-medium tracking-wide text-[var(--text-muted)]">
          {items.length} MARKETS
        </span>
      </div>

      <div className="ticker-wrap h-full flex items-center" style={{ paddingLeft: '160px' }}>
        <div className="ticker flex items-center gap-2">
          {loopItems.map((t, i) => {
            const isPositive = (t.priceChangePercent ?? 0) >= 0
            const price = t.price ?? 0
            const symbol = t.symbol || 'BTC-USD'
            const shortSym = symbol.split('-')[0].slice(0, 3)
            const change = t.priceChangePercent ?? 0
            
            return (
              <div
                key={`${t.symbol}-${i}`}
                className="group flex items-center gap-2 shrink-0 px-3 py-1 rounded-full border text-[11px] font-medium gpu-accelerated hover-lift cursor-pointer bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-sm)]"
                style={{ willChange: 'transform' }}
              >
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold bg-[var(--accent)] text-white shadow-sm">
                  {shortSym}
                </span>
                <span className="font-medium tracking-tight text-[11px] text-[var(--text-sec)]">{symbol}</span>
                <span className="mono font-medium text-[11px] text-[var(--text)]">
                  ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 3 })}
                </span>
                <span className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium mono border ${isPositive ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'}`}>
                  <span className="text-[9px]">{isPositive ? '↗' : '↘'}</span>
                  {Math.abs(change).toFixed(1)}%
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
