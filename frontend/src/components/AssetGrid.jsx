import { useMarketStore } from '../store/useMarketStore'

const ASSET_META = {
  'BTC-USD': { name: 'Bitcoin', icon: '₿', color: 'from-orange-500 to-amber-500' },
  'ETH-USD': { name: 'Ethereum', icon: 'Ξ', color: 'from-indigo-500 to-purple-500' },
  'BNB-USD': { name: 'BNB', icon: 'B', color: 'from-yellow-500 to-amber-500' },
  'SOL-USD': { name: 'Solana', icon: 'S', color: 'from-purple-500 to-pink-500' },
  'XRP-USD': { name: 'XRP', icon: 'X', color: 'from-zinc-500 to-zinc-700' },
  'ADA-USD': { name: 'Cardano', icon: 'A', color: 'from-blue-500 to-cyan-500' },
  'DOGE-USD': { name: 'Dogecoin', icon: 'D', color: 'from-yellow-400 to-orange-400' },
  'AVAX-USD': { name: 'Avalanche', icon: 'A', color: 'from-red-500 to-red-700' },
  'DOT-USD': { name: 'Polkadot', icon: 'P', color: 'from-pink-500 to-rose-500' },
  'MATIC-USD': { name: 'Polygon', icon: 'M', color: 'from-indigo-600 to-purple-700' },
}

export default function AssetGrid({ onSelect, selected }) {
  const { tickers } = useMarketStore()
  const assets = Object.keys(ASSET_META)

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 stagger-children">
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
            className={`group relative text-left p-3.5 rounded-xl border text-left gpu-accelerated transition-all duration-200 ease-out hover-lift ${
              isSelected
                ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)] scale-[1.02] ring-2 ring-[var(--accent-ring)]'
                : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:bg-[var(--card-hover)] hover:shadow-[var(--shadow-md)]'
            }`}
            style={{ willChange: 'transform, border-color' }}
          >
            <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${meta.color} opacity-60 group-hover:opacity-100 transition-opacity rounded-t-xl`} />

            <div className="flex items-start justify-between mb-2.5">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-[11px] transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 gpu-accelerated shadow-sm ${
                isSelected ? 'bg-white/20 text-white' : `bg-gradient-to-br ${meta.color} text-white`
              }`}>
                {meta.icon}
              </div>
              <div className={`flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full mono border ${
                isSelected
                  ? 'bg-white/20 text-white border-white/20'
                  : isPositive ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'
              }`}>
                <span className="text-[9px]">{isPositive ? '↗' : '↘'}</span>
                {Math.abs(change).toFixed(1)}%
              </div>
            </div>

            <div className="space-y-0.5">
              <div className={`font-medium text-[12px] tracking-tight ${isSelected ? 'text-white' : 'text-[var(--text)]'}`}>
                {meta.name}
              </div>
              <div className={`text-[10px] ${isSelected ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>
                {sym}
              </div>
              <div className={`mono font-semibold text-[13px] mt-1.5 tracking-tight ${isSelected ? 'text-white' : 'text-[var(--text)]'}`}>
                {price ? `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 3 })}` : '—'}
              </div>
            </div>

            <div className="mt-2.5 flex items-center gap-0.5 h-4">
              {[...Array(12)].map((_, i) => {
                const h = 30 + Math.sin(i + sym.charCodeAt(0)) * 20 + (isPositive ? i * 2 : -i)
                return (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-all duration-300 ${
                      isSelected
                        ? 'bg-white/30'
                        : isPositive ? 'bg-[var(--buy)]/40 group-hover:bg-[var(--buy)]/60' : 'bg-[var(--sell)]/40 group-hover:bg-[var(--sell)]/60'
                    }`}
                    style={{ height: `${Math.max(3, Math.min(16, h))}%`, transform: 'translateZ(0)', willChange: 'height' }}
                  />
                )
              })}
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
    <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--card)] border border-[var(--border)] hover:border-[var(--border-strong)] transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated">
      <div className="flex items-center gap-2.5">
        <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${meta.color} text-white flex items-center justify-center font-bold text-[11px] shadow-sm`}>
          {meta.icon}
        </div>
        <div>
          <div className="font-medium text-[13px] text-[var(--text)]">{symbol}</div>
          <div className="text-[11px] text-[var(--text-muted)]">{meta.name}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="mono font-semibold text-[13px] text-[var(--text)]">${ticker.price?.toFixed(2)}</div>
        <div className={`text-[11px] font-medium mono ${ticker.priceChangePercent >= 0 ? 'text-[var(--buy)]' : 'text-[var(--sell)]'}`}>
          {ticker.priceChangePercent >= 0 ? '↗' : '↘'} {ticker.priceChangePercent?.toFixed(1)}%
        </div>
      </div>
    </div>
  )
}
