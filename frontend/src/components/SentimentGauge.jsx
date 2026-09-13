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
    <div className="rounded-xl border bg-[var(--card)] border-[var(--border)] overflow-hidden gpu-accelerated hover-lift">
      <div className="p-5">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center text-[12px] font-bold shadow-[var(--glow)]">S</div>
            <div>
              <div className="font-medium text-[13px] text-[var(--text)]">Sentiment</div>
              <div className="text-[11px] text-[var(--text-muted)]">{symbol} • {daily.length}d</div>
            </div>
          </div>
          <div className={`px-2.5 py-1 rounded-full text-[11px] font-medium border ${isPositive ? 'bg-[var(--buy)] text-white border-[var(--buy)] shadow-sm' : avg < -0.1 ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'}`}>
            {label}
          </div>
        </div>

        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wide">Bearish</span>
            <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wide">Bullish</span>
          </div>
          <div className="relative h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden border border-[var(--border)]">
            <div className="absolute inset-0 bg-gradient-to-r from-[var(--sell)]/30 via-[var(--text-faint)] to-[var(--buy)]/30"></div>
            <div className="absolute top-0 bottom-0 w-0.5 bg-[var(--text)] rounded-full transition-all duration-700 ease-out gpu-accelerated shadow-sm" style={{ left: `${score}%`, transform: 'translateX(-50%) translateZ(0)', willChange: 'left' }}>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-[var(--text)] rounded-full border-2 border-[var(--card)] shadow-md"></div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-5">
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-center">
            <div className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">Score</div>
            <div className="text-[14px] font-semibold mono mt-1 text-[var(--text)]">{avg.toFixed(2)}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-center">
            <div className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">Sentiment</div>
            <div className="text-[14px] font-semibold mt-1 text-[var(--text)]">{score.toFixed(0)}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-center">
            <div className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">Days</div>
            <div className="text-[14px] font-semibold mt-1 text-[var(--text)]">{daily.length}</div>
          </div>
        </div>

        {daily.length > 0 && (
          <div className="mt-5">
            <div className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)] mb-2">14-Day Trend</div>
            <div className="flex items-end gap-0.5 h-12">
              {daily.slice(-14).map((d, i) => {
                const h = ((d.compound + 1) / 2) * 100
                const isPos = d.compound > 0
                return (
                  <div key={i} className="flex-1 h-full flex items-end">
                    <div className={`w-full rounded-full transition-all duration-500 gpu-accelerated ${isPos ? 'bg-[var(--buy)]' : 'bg-[var(--sell)]'} opacity-60 hover:opacity-100`} style={{ height: `${Math.max(6, h)}%`, willChange: 'height' }} />
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
