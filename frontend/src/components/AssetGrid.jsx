import { TrendingUp, TrendingDown, Activity, Zap } from 'lucide-react'
import { useMarketStore } from '../store/useMarketStore'

const ASSET_META = {
  'BTC-USD': { name: 'Bitcoin', color: 'from-orange-500 to-amber-500', icon: '₿', cap: '$1.2T' },
  'ETH-USD': { name: 'Ethereum', color: 'from-indigo-500 to-purple-500', icon: 'Ξ', cap: '$400B' },
  'BNB-USD': { name: 'BNB', color: 'from-yellow-500 to-amber-500', icon: 'B', cap: '$90B' },
  'SOL-USD': { name: 'Solana', color: 'from-purple-500 to-pink-500', icon: 'S', cap: '$70B' },
  'XRP-USD': { name: 'XRP', color: 'from-gray-400 to-gray-600', icon: 'X', cap: '$35B' },
  'ADA-USD': { name: 'Cardano', color: 'from-blue-500 to-cyan-500', icon: 'A', cap: '$30B' },
  'DOGE-USD': { name: 'Dogecoin', color: 'from-yellow-400 to-orange-400', icon: 'D', cap: '$20B' },
  'AVAX-USD': { name: 'Avalanche', color: 'from-red-500 to-red-700', icon: 'A', cap: '$15B' },
  'DOT-USD': { name: 'Polkadot', color: 'from-pink-500 to-rose-500', icon: 'P', cap: '$10B' },
  'MATIC-USD': { name: 'Polygon', color: 'from-indigo-600 to-purple-700', icon: 'M', cap: '$8B' },
}

export default function AssetGrid({ onSelect, selected }) {
  const { tickers } = useMarketStore()
  const assets = Object.keys(ASSET_META)

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {assets.map(sym => {
        const meta = ASSET_META[sym]
        const ticker = tickers[sym]
        const price = ticker?.price || 0
        const change = ticker?.priceChangePercent || 0
        const isPositive = change >= 0
        const isSelected = selected === sym

        return (
          <button
            key={sym}
            onClick={() => onSelect(sym)}
            className={`group relative text-left p-4 rounded-2xl border backdrop-blur-xl transition-all duration-300 overflow-hidden ${
              isSelected
                ? 'bg-white text-black border-white shadow-xl shadow-white/10 scale-[1.02]'
                : 'bg-crypto-card/60 border-crypto-border/50 hover:border-crypto-borderLight hover:bg-crypto-cardHover/80 hover:shadow-xl hover:shadow-black/20 hover:-translate-y-0.5'
            }`}
          >
            {/* Gradient accent */}
            <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${meta.color} opacity-60 group-hover:opacity-100 transition-opacity`}></div>
            
            {/* Selection glow */}
            {isSelected && (
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none"></div>
            )}

            <div className="relative">
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${meta.color} flex items-center justify-center font-black text-white shadow-lg text-sm`}>
                  {meta.icon}
                </div>
                <div className={`flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full ${
                  isSelected
                    ? (isPositive ? 'bg-black text-crypto-accent' : 'bg-black text-crypto-bear')
                    : (isPositive ? 'bg-crypto-bull/10 text-crypto-bull' : 'bg-crypto-bear/10 text-crypto-bear')
                }`}>
                  {isPositive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {Math.abs(change).toFixed(2)}%
                </div>
              </div>

              <div className="space-y-1">
                <div className={`font-bold text-[13px] tracking-tight ${isSelected ? 'text-black' : 'text-white'}`}>
                  {meta.name}
                </div>
                <div className={`text-[11px] font-medium ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>
                  {sym} • {meta.cap}
                </div>
                <div className={`mono font-bold text-[15px] mt-2 ${isSelected ? 'text-black' : 'text-white'}`}>
                  {price ? `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}` : '—'}
                </div>
              </div>

              {/* Mini sparkline placeholder */}
              <div className="mt-3 flex items-center gap-1">
                <div className="flex-1 flex gap-0.5 h-6 items-end">
                  {[...Array(12)].map((_, i) => {
                    const h = 20 + Math.sin(i + sym.charCodeAt(0)) * 10 + (isPositive ? i * 1.5 : -i * 0.5)
                    return (
                      <div
                        key={i}
                        className={`flex-1 rounded-full transition-all duration-500 ${
                          isSelected
                            ? 'bg-black/20'
                            : isPositive
                              ? 'bg-crypto-bull/40 group-hover:bg-crypto-bull/60'
                              : 'bg-crypto-bear/40 group-hover:bg-crypto-bear/60'
                        }`}
                        style={{ height: `${Math.max(4, Math.min(24, h))}%` }}
                      />
                    )
                  })}
                </div>
                <Activity size={12} className={isSelected ? 'text-black/40' : 'text-crypto-muted'} />
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}

export function LiveAssetRow({ symbol }) {
  const { tickers } = useMarketStore()
  const ticker = tickers[symbol]
  const meta = ASSET_META[symbol]

  if (!ticker || !meta) return null

  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-crypto-card/40 border border-crypto-border/30 hover:border-crypto-border/60 transition">
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${meta.color} flex items-center justify-center font-bold text-white text-xs`}>
          {meta.icon}
        </div>
        <div>
          <div className="font-semibold text-sm text-white">{symbol}</div>
          <div className="text-xs text-crypto-muted">{meta.name}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="mono font-bold text-sm text-white">${ticker.price?.toFixed(2)}</div>
        <div className={`text-xs font-medium ${ticker.priceChangePercent >= 0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>
          {ticker.priceChangePercent >= 0 ? '+' : ''}{ticker.priceChangePercent?.toFixed(2)}%
        </div>
      </div>
    </div>
  )
}
