export default function SentimentGauge({ sentiment, symbol }) {
  const avg = sentiment?.average_compound || 0
  const daily = sentiment?.daily || []
  const score = ((avg + 1) / 2) * 100
  const isPositive = avg > 0.1
  let label = 'Neutral'
  if (avg > 0.5) label = 'Very Bullish'
  else if (avg > 0.1) label = 'Bullish'
  else if (avg < -0.5) label = 'Very Bearish'
  else if (avg < -0.1) label = 'Bearish'

  return (
    <div className="rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 overflow-hidden gpu-accelerated">
      <div className="p-5">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center text-[12px] font-medium">S</div>
            <div>
              <div className="font-medium text-[13px] text-zinc-900 dark:text-white">Sentiment</div>
              <div className="text-[11px] text-zinc-500">{symbol} • {daily.length}d</div>
            </div>
          </div>
          <div className={`px-2.5 py-1 rounded-full text-[11px] font-medium border ${isPositive ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'}`}>
            {label}
          </div>
        </div>

        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Bearish</span>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Bullish</span>
          </div>
          <div className="relative h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-zinc-300 via-zinc-100 to-zinc-900 dark:from-zinc-700 dark:via-zinc-600 dark:to-white opacity-50"></div>
            <div className="absolute top-0 bottom-0 w-0.5 bg-zinc-900 dark:bg-white rounded-full transition-all duration-700 ease-out gpu-accelerated" style={{ left: `${score}%`, transform: 'translateX(-50%) translateZ(0)', willChange: 'left' }}>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-zinc-900 dark:bg-white rounded-full border-2 border-white dark:border-zinc-900 shadow-sm"></div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-5">
          <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 text-center">
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Score</div>
            <div className="text-[14px] font-semibold mono mt-1 text-zinc-900 dark:text-white">{avg.toFixed(2)}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 text-center">
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Sentiment</div>
            <div className="text-[14px] font-semibold mt-1 text-zinc-900 dark:text-white">{score.toFixed(0)}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 text-center">
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Days</div>
            <div className="text-[14px] font-semibold mt-1 text-zinc-900 dark:text-white">{daily.length}</div>
          </div>
        </div>

        {daily.length > 0 && (
          <div className="mt-5">
            <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500 mb-2">Trend</div>
            <div className="flex items-end gap-0.5 h-12">
              {daily.slice(-14).map((d, i) => {
                const h = ((d.compound + 1) / 2) * 100
                return (
                  <div key={i} className="flex-1 h-full flex items-end">
                    <div className="w-full rounded-full bg-zinc-200 dark:bg-zinc-700 transition-all duration-500 gpu-accelerated hover:bg-zinc-900 dark:hover:bg-white" style={{ height: `${Math.max(6, h)}%`, willChange: 'height' }} />
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
