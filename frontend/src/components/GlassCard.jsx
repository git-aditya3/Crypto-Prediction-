export default function GlassCard({ children, className = '', hover = true, gradient = false, ...props }) {
  return (
    <div 
      className={`
        relative rounded-2xl border backdrop-blur-xl overflow-hidden
        ${gradient 
          ? 'bg-gradient-to-br from-crypto-card/80 via-crypto-card/60 to-crypto-card/40 border-crypto-border/50' 
          : 'bg-crypto-card/60 border-crypto-border/50'
        }
        ${hover ? 'hover:border-crypto-borderLight hover:bg-crypto-cardHover/60 transition-all duration-300 hover:shadow-2xl hover:shadow-black/20 hover:-translate-y-[1px]' : ''}
        ${className}
      `}
      {...props}
    >
      {/* Subtle inner glow */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none"></div>
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon, accent = 'accent' }) {
  const accentColors = {
    accent: 'from-crypto-accent to-crypto-accent3',
    accent2: 'from-crypto-accent2 to-purple-500',
    bear: 'from-crypto-bear to-red-600',
    bull: 'from-crypto-bull to-emerald-600',
    warning: 'from-amber-500 to-orange-500'
  }

  const isPositive = trend && trend.includes('+') || parseFloat(trend) > 0

  return (
    <GlassCard className="p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="text-[11px] font-bold tracking-widest text-crypto-muted uppercase">{label}</div>
        {Icon && (
          <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${accentColors[accent]} flex items-center justify-center shadow-lg`}>
            <Icon size={14} className="text-black" />
          </div>
        )}
      </div>
      <div className="space-y-1">
        <div className="text-2xl font-bold tracking-tight text-white mono">{value}</div>
        {subValue && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-crypto-muted">{subValue}</span>
            {trend && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isPositive ? 'bg-crypto-bull/10 text-crypto-bull' : 'bg-crypto-bear/10 text-crypto-bear'}`}>
                {trend}
              </span>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  )
}
