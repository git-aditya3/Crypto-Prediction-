import { useEffect, useMemo } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'

export default function MarketTicker() {
  const { tickers, fetchAllTickers, isLive, startLive } = useMarketStore()
  const theme = useSettingsStore(s => s.theme)
  const isLight = theme === 'light' || theme === 'mono'

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
      <div className={`sticky top-0 z-[100] h-10 flex items-center px-4 text-[12px] font-medium border-b gpu-accelerated ${isLight ? 'bg-white/90 border-zinc-200 text-zinc-500' : 'bg-[#09090b]/90 border-zinc-800 text-zinc-400'} backdrop-blur-xl`}>
        <div className="flex items-center gap-2.5">
          <div className="live-dot"></div>
          <span className="font-medium tracking-tight">Connecting</span>
          <span className="flex gap-1">
            <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`sticky top-0 z-[100] h-10 overflow-hidden flex items-center border-b gpu-accelerated ${isLight ? 'bg-white/90 border-zinc-200' : 'bg-[#09090b]/90 border-zinc-800'} backdrop-blur-xl`} style={{ transform: 'translateZ(0)' }}>
      <div className={`absolute left-0 top-0 bottom-0 z-20 flex items-center gap-2.5 px-4 border-r ${isLight ? 'bg-white border-zinc-200' : 'bg-[#09090b] border-zinc-800'}`}>
        <div className="live-dot"></div>
        <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold tracking-wide bg-zinc-900 text-white dark:bg-white dark:text-black">LIVE</span>
        <span className={`hidden md:inline text-[10px] font-medium tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
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
                className={`group flex items-center gap-2 shrink-0 px-3 py-1 rounded-full border text-[11px] font-medium gpu-accelerated hover-lift cursor-pointer ${
                  isLight
                    ? 'bg-zinc-50 border-zinc-200 hover:bg-white hover:border-zinc-300'
                    : 'bg-zinc-900 border-zinc-800 hover:bg-zinc-800 hover:border-zinc-700'
                }`}
                style={{ willChange: 'transform' }}
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-semibold ${isLight ? 'bg-zinc-900 text-white' : 'bg-white text-black'}`}>
                  {shortSym}
                </span>
                <span className={`font-medium tracking-tight text-[11px] ${isLight ? 'text-zinc-700' : 'text-zinc-200'}`}>{symbol}</span>
                <span className={`mono font-medium text-[11px] ${isLight ? 'text-zinc-900' : 'text-white'}`}>
                  ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 3 })}
                </span>
                <span className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium mono ${
                  isPositive 
                    ? isLight ? 'bg-zinc-900 text-white' : 'bg-white text-black'
                    : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700'
                }`}>
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
