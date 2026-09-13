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
  const loopItems = [...items, ...items]

  if (items.length === 0) {
    return (
      <div className={`h-12 flex items-center px-6 text-sm font-poppins font-medium transition-colors duration-500 ${
        isDark ? 'bg-[#000000] border-b border-white/10 text-[#9CA3AF]' : 'bg-white/60 backdrop-blur border-b border-white/40 text-[#64748b]'
      }`}>
        <div className="flex items-center gap-3">
          <div className="live-dot"></div>
          <span>Connecting to Binance live feed • Claymorphism • Puffy 3D</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`h-14 overflow-hidden relative transition-colors duration-500 ${
      isDark
        ? 'bg-[#000000] border-b border-white/10'
        : 'bg-white/60 backdrop-blur-xl border-b border-white/40'
    }`}>
      {/* Live indicator - Flat structural (Rule 3) */}
      <div className={`absolute left-0 top-0 bottom-0 z-10 flex items-center gap-3 px-6 backdrop-blur-sm transition-colors duration-500 ${
        isDark
          ? 'bg-[#000000] border-r border-white/10'
          : 'bg-white/70 border-r border-white/40'
      }`}>
        <div className="flex items-center gap-2">
          <div className="live-dot"></div>
          <span className="text-xs font-black tracking-widest clay-pill px-3 py-1 font-poppins"
            style={isDark ? { background: 'rgba(28,28,30,0.7)', color: '#00d395', border: '1px solid rgba(255,255,255,0.08)' } : { background: '#ffffff', color: '#059669' }}>
            LIVE
          </span>
        </div>
        <div className={`h-4 w-px ${isDark ? 'bg-white/10' : 'bg-black/10'}`}></div>
        <span className="text-[11px] font-bold tracking-widest font-poppins hidden md:block"
          style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
          BINANCE REAL-TIME • CLAY
        </span>
      </div>

      <div className="ticker-wrap h-full flex items-center ml-[180px]">
        <div className="ticker flex items-center gap-4">
          {loopItems.map((t, i) => {
            const isPositive = (t.priceChangePercent ?? 0) >= 0
            const price = t.price ?? 0
            return (
              <div key={`${t.symbol}-${i}`} 
                className="flex items-center gap-3 shrink-0 group cursor-pointer transition-all duration-300 hover:scale-105 clay-pill px-4 py-2 font-poppins"
                style={isDark ? {
                  background: 'rgba(28,28,30,0.6)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  boxShadow: '0px 4px 12px rgba(0,0,0,0.3), inset 2px 2px 4px rgba(255,255,255,0.05)'
                } : {
                  background: '#ffffff',
                  border: '1px solid rgba(255,255,255,0.4)',
                  boxShadow: '0px 4px 12px rgba(31,38,135,0.05), inset 2px 2px 4px rgba(255,255,255,0.9)'
                }}>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-black border transition-all font-poppins"
                    style={isDark ? {
                      background: 'rgba(38,38,40,0.8)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      color: '#F3F4F6',
                      boxShadow: 'inset 2px 2px 4px rgba(255,255,255,0.08), inset -2px -2px 4px rgba(0,0,0,0.3)'
                    } : {
                      background: '#f8fafc',
                      border: '1px solid rgba(255,255,255,0.4)',
                      color: '#1e293b',
                      boxShadow: 'inset 2px 2px 4px rgba(255,255,255,0.9), inset -2px -2px 4px rgba(0,0,0,0.05)'
                    }}>
                    {(t.symbol || 'BTC').split('-')[0].slice(0, 3)}
                  </div>
                  <span className="font-bold text-sm tracking-tight font-poppins"
                    style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>{t.symbol || 'Unknown'}</span>
                </div>
                <span className="mono text-sm font-bold"
                  style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}</span>
                <div className={`flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full clay-pill font-poppins ${
                  isPositive ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
                }`}>
                  {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {Math.abs(t.priceChangePercent ?? 0).toFixed(2)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Fade edges - flat */}
      <div className={`absolute right-0 top-0 bottom-0 w-20 pointer-events-none transition-colors duration-500 ${
        isDark ? 'bg-gradient-to-l from-[#000000] to-transparent' : 'bg-gradient-to-l from-white/60 to-transparent'
      }`}></div>
    </div>
  )
}
