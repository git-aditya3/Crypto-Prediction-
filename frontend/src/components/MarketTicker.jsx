import { useEffect } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function MarketTicker() {
  const { tickers, fetchAllTickers, isLive, startLive } = useMarketStore()
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

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
      <div className={`sticky top-0 z-[100] h-10 flex items-center px-4 text-[12px] font-medium border-b ${
        isDark ? 'bg-black border-white/10 text-zinc-400' : 'bg-white border-black/5 text-zinc-500'
      }`}>
        <div className="flex items-center gap-2">
          <div className="live-dot"></div>
          <span className="font-semibold">Connecting to live market feed...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`sticky top-0 z-[100] h-11 overflow-hidden flex items-center border-b ${
      isDark ? 'bg-black border-white/[0.06]' : 'bg-white border-black/[0.06]'
    }`}>
      {/* Left LIVE badge - fixed */}
      <div className={`absolute left-0 top-0 bottom-0 z-20 flex items-center gap-2.5 px-4 border-r backdrop-blur-xl ${
        isDark ? 'bg-black border-white/[0.06]' : 'bg-white border-black/[0.06]'
      }`}>
        <div className="live-dot"></div>
        <span className="ui-pill-live px-2.5 py-1 text-[10px] rounded-full">LIVE</span>
        <span className={`hidden md:inline text-[10px] font-semibold tracking-wide ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
          BINANCE
        </span>
      </div>

      {/* Ticker track */}
      <div className="ticker-wrap h-full flex items-center" style={{ paddingLeft: '128px' }}>
        <div className="ticker flex items-center gap-3">
          {loopItems.map((t, i) => {
            const isPositive = (t.priceChangePercent ?? 0) >= 0
            const price = t.price ?? 0
            const symbol = t.symbol || 'BTC-USD'
            const shortSym = symbol.split('-')[0].slice(0, 4)
            return (
              <div
                key={`${t.symbol}-${i}`}
                className={`flex items-center gap-2.5 shrink-0 px-3 py-1.5 rounded-full border text-[12px] font-medium transition-colors ${
                  isDark
                    ? 'bg-zinc-900/60 border-white/[0.06] hover:bg-zinc-900 hover:border-white/10'
                    : 'bg-zinc-50 border-black/[0.04] hover:bg-white hover:border-black/10 hover:shadow-sm'
                }`}
              >
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold ${
                  isDark ? 'bg-white text-black' : 'bg-black text-white'
                }`}>
                  {shortSym.slice(0, 3)}
                </span>
                <span className={`font-semibold text-[12px] ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{symbol}</span>
                <span className={`mono font-semibold ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>
                  ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}
                </span>
                <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  isPositive ? 'ui-pill-buy' : 'ui-pill-sell'
                }`}>
                  {isPositive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {Math.abs(t.priceChangePercent ?? 0).toFixed(2)}%
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right fade */}
      <div className={`absolute right-0 top-0 bottom-0 w-16 pointer-events-none z-10 ${
        isDark ? 'bg-gradient-to-l from-black to-transparent' : 'bg-gradient-to-l from-white to-transparent'
      }`} />
    </div>
  )
}
