import { useMarketStore } from '../store/useMarketStore'

const ASSET_META = {
  'BTC-USD': { name: 'Bitcoin', icon: '₿' },
  'ETH-USD': { name: 'Ethereum', icon: 'Ξ' },
  'BNB-USD': { name: 'BNB', icon: 'B' },
  'SOL-USD': { name: 'Solana', icon: 'S' },
  'XRP-USD': { name: 'XRP', icon: 'X' },
  'ADA-USD': { name: 'Cardano', icon: 'A' },
  'DOGE-USD': { name: 'Dogecoin', icon: 'D' },
  'AVAX-USD': { name: 'Avalanche', icon: 'A' },
  'DOT-USD': { name: 'Polkadot', icon: 'P' },
  'MATIC-USD': { name: 'Polygon', icon: 'M' },
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
                ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white shadow-sm scale-[1.02]'
                : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
            style={{ willChange: 'transform, border-color' }}
          >
            <div className="flex items-start justify-between mb-2.5">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-medium text-[11px] transition-transform duration-200 group-hover:scale-105 gpu-accelerated ${
                isSelected ? 'bg-white/20 text-white dark:bg-black/10 dark:text-black' : 'bg-zinc-900 text-white dark:bg-white dark:text-black'
              }`}>
                {meta.icon}
              </div>
              <div className={`flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full mono ${
                isSelected
                  ? 'bg-white/20 text-white dark:bg-black/10 dark:text-black'
                  : isPositive ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700'
              }`}>
                <span className="text-[9px]">{isPositive ? '↗' : '↘'}</span>
                {Math.abs(change).toFixed(1)}%
              </div>
            </div>

            <div className="space-y-0.5">
              <div className={`font-medium text-[12px] tracking-tight ${isSelected ? 'text-white dark:text-black' : 'text-zinc-900 dark:text-white'}`}>
                {meta.name}
              </div>
              <div className={`text-[10px] ${isSelected ? 'text-white/60 dark:text-black/60' : 'text-zinc-500'}`}>
                {sym}
              </div>
              <div className={`mono font-semibold text-[13px] mt-1.5 tracking-tight ${isSelected ? 'text-white dark:text-black' : 'text-zinc-900 dark:text-white'}`}>
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
                        ? 'bg-white/30 dark:bg-black/20'
                        : 'bg-zinc-200 dark:bg-zinc-700 group-hover:bg-zinc-300 dark:group-hover:bg-zinc-600'
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
    <div className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center font-medium text-[11px]">
          {meta.icon}
        </div>
        <div>
          <div className="font-medium text-[13px] text-zinc-900 dark:text-white">{symbol}</div>
          <div className="text-[11px] text-zinc-500">{meta.name}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="mono font-semibold text-[13px] text-zinc-900 dark:text-white">${ticker.price?.toFixed(2)}</div>
        <div className={`text-[11px] font-medium mono ${ticker.priceChangePercent >= 0 ? 'text-zinc-900 dark:text-white' : 'text-zinc-500'}`}>
          {ticker.priceChangePercent >= 0 ? '↗' : '↘'} {ticker.priceChangePercent?.toFixed(1)}%
        </div>
      </div>
    </div>
  )
}
