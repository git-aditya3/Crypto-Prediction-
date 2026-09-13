import { useSettingsStore } from '../store/useSettingsStore'

export default function GlassCard({ children, className = '', hover = true, glow = false, variant = 'default', ...props }) {
  const theme = useSettingsStore(s => s.theme)
  const blur = useSettingsStore(s => s.blur)
  
  const variantClasses = {
    default: 'ui-card',
    accent: 'ui-card border-2',
    ghost: 'bg-transparent border border-dashed',
    glow: 'ui-card shadow-lg',
  }
  
  return (
    <div 
      className={`${variantClasses[variant] || variantClasses.default} ${hover ? 'hover-lift' : ''} ${glow ? 'glow-effect' : ''} ${blur ? 'glass' : ''} ${className} animate-fadeInUp`}
      style={{
        ...(variant === 'accent' ? { borderColor: 'var(--accent)', boxShadow: 'var(--glow)' } : {}),
        ...(glow ? { boxShadow: 'var(--shadow), var(--glow)' } : {})
      }}
      {...props}
    >
      <div className="relative z-10">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon, accent = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isPositive = trend && (trend.includes('+') || parseFloat(trend) > 0)
  const isNegative = trend && (trend.includes('-') || parseFloat(trend) < 0)

  return (
    <GlassCard className={`p-5 group ${accent ? 'ring-1 ring-[var(--accent)]/20' : ''}`} glow={accent}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`text-[10px] font-bold tracking-widest uppercase px-2.5 py-1 rounded-full ${isLight ? 'bg-black/5 text-zinc-600' : 'bg-white/5 text-zinc-400'} group-hover:bg-[var(--accent-soft)] transition-colors`}>
            {label}
          </div>
          {accent && <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />}
        </div>
        {Icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 ${isLight ? 'bg-black text-white' : 'bg-white text-black'} ${accent ? 'bg-[var(--accent)] text-[var(--bg)]' : ''}`}>
            <Icon size={16} />
          </div>
        )}
      </div>
      <div className="space-y-2">
        <div className={`text-2xl font-bold tracking-tight mono transition-all group-hover:tracking-wide ${isLight ? 'text-black' : 'text-white'}`}>{value}</div>
        {subValue && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[12px] font-medium ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{subValue}</span>
            {trend && (
              <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1 ${isPositive ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : isNegative ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-[var(--accent-soft)] text-[var(--text-sec)] border border-[var(--border)]'}`}>
                <span className={`w-1 h-1 rounded-full ${isPositive ? 'bg-emerald-500' : isNegative ? 'bg-red-500' : 'bg-[var(--accent)]'}`} />
                {trend}
              </span>
            )}
          </div>
        )}
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </GlassCard>
  )
}

export function FeatureCard({ icon: Icon, title, desc, badge, children, className = '' }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  
  return (
    <GlassCard className={`p-6 group ${className}`}>
      <div className="flex items-start gap-4">
        {Icon && (
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-all group-hover:scale-110 ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
            <Icon size={20} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className={`font-bold text-[14px] ${isLight ? 'text-black' : 'text-white'}`}>{title}</h3>
            {badge && <span className="ui-pill-accent text-[9px] px-2 py-0.5">{badge}</span>}
          </div>
          {desc && <p className={`text-[12px] mt-1 ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{desc}</p>}
          {children && <div className="mt-4">{children}</div>}
        </div>
      </div>
    </GlassCard>
  )
}

export function MetricCard({ label, value, change, icon: Icon, className = '' }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  
  return (
    <div className={`p-4 rounded-xl border bg-[var(--card)] border-[var(--border)] hover:border-[var(--accent)]/30 transition-all hover:shadow-lg group ${className}`}>
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{label}</span>
        {Icon && <Icon size={12} className={`${isLight ? 'text-zinc-400' : 'text-zinc-500'} group-hover:text-[var(--accent)] transition-colors`} />}
      </div>
      <div className={`text-lg font-bold mono mt-2 ${isLight ? 'text-black' : 'text-white'}`}>{value}</div>
      {change && (
        <div className={`text-[11px] mt-1 flex items-center gap-1 ${parseFloat(change) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
          <span>{parseFloat(change) >= 0 ? '↗' : '↘'}</span> {change}
        </div>
      )}
    </div>
  )
}
