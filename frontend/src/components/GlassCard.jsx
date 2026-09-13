import { useSettingsStore } from '../store/useSettingsStore'

export default function GlassCard({ children, className = '', hover = true, glow = false, variant = 'default', style = {}, ...props }) {
  const blur = useSettingsStore(s => s.blur)
  const visualStyle = useSettingsStore(s => s.visualStyle) || 'liquid'
  
  const variantClasses = {
    default: 'ui-card',
    accent: 'ui-card',
    ghost: 'bg-transparent border border-dashed border-[var(--border)] rounded-xl',
    minimal: 'bg-[var(--card)] border border-[var(--border)] rounded-xl p-5',
    clay: 'clay-card',
    liquid: 'liquid-glass-card',
    neo: 'neo-card',
    brutal: 'brutal-card',
    flat: 'flat-card',
  }
  
  const visualMap = {
    clay: 'clay-card',
    liquid: 'liquid-glass-card',
    neo: 'neo-card',
    brutal: 'brutal-card',
    flat: 'flat-card',
  }

  const resolvedVariant = variant === 'default' ? (visualMap[visualStyle] || 'ui-card') : (variantClasses[variant] || variantClasses.default)
  
  return (
    <div 
      className={`${resolvedVariant} ${hover ? 'hover-lift' : ''} ${blur && visualStyle === 'liquid' ? 'glass' : ''} ${glow ? 'shadow-[var(--glow)]' : ''} ${className} gpu-accelerated`}
      style={{ ...style }}
      {...props}
    >
      {visualStyle === 'liquid' && (
        <>
          <div className="glass-blob w-32 h-32 bg-[var(--accent-soft)] top-0 right-0 opacity-30" />
          <div className="glass-blob w-24 h-24 bg-[var(--buy-soft)] bottom-0 left-0 opacity-20" style={{ animationDelay: '2s' }} />
        </>
      )}
      <div className="relative z-10">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon, accent = false }) {
  const visualStyle = useSettingsStore(s => s.visualStyle) || 'liquid'
  const isPositive = trend && (trend.includes('+') || parseFloat(trend) > 0)
  const isNegative = trend && (trend.includes('-') || parseFloat(trend) < 0)

  const isClay = visualStyle === 'clay'
  const isBrutal = visualStyle === 'brutal'
  const isLiquid = visualStyle === 'liquid'

  return (
    <GlassCard className={`p-5 group ${accent ? 'border-[var(--accent)]' : ''}`} hover={true} glow={accent}>
      <div className="flex items-start justify-between mb-4 gpu-accelerated">
        <div className="flex items-center gap-2">
          <div className={`text-[10px] font-medium tracking-wide uppercase px-2.5 py-1 rounded-full ${isClay ? 'clay-pill' : isBrutal ? 'brutal-pill !text-[9px] !py-1' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border border-[var(--border)]'}`}>
            {label}
          </div>
          {accent && <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse shadow-[var(--glow)]" />}
        </div>
        {Icon && (
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-transform duration-200 ease-out group-hover:scale-110 gpu-accelerated ${
            isClay ? 'clay-card !p-0 !w-10 !h-10 bg-[var(--accent)] text-white' :
            isBrutal ? 'brutal-card !p-0 !w-9 !h-9 !rounded-sm bg-[var(--accent)] text-white !shadow-[3px_3px_0px_var(--text)]' :
            isLiquid ? 'liquid-glass !w-9 !h-9 bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--glass-border)]' :
            accent ? 'bg-[var(--accent)] text-white shadow-[var(--glow)]' : 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--border)]'
          } ${isClay ? '!rounded-2xl' : 'rounded-lg'}`}>
            <Icon size={14} />
          </div>
        )}
      </div>
      <div className="space-y-2">
        <div className="text-[22px] font-semibold tracking-tight mono leading-none text-[var(--text)]">{value}</div>
        {subValue && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[12px] font-normal text-[var(--text-sec)]">{subValue}</span>
            {trend && (
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold flex items-center gap-1 border gpu-accelerated transition-all duration-200 shadow-sm ${
                isClay ? 'clay-pill !px-3 !py-1' :
                isBrutal ? 'brutal-pill !bg-[var(--buy)] !text-white' :
                isPositive ? 'bg-[var(--buy)] text-white border-[var(--buy)]' : 
                isNegative ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' : 
                'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'
              }`}>
                <span className="text-[10px]">{isPositive ? '↗' : isNegative ? '↘' : '→'}</span>
                {trend}
              </span>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  )
}

export function FeatureCard({ icon: Icon, title, desc, badge, children, className = '' }) {
  const visualStyle = useSettingsStore(s => s.visualStyle) || 'liquid'
  const isClay = visualStyle === 'clay'
  const isBrutal = visualStyle === 'brutal'

  return (
    <GlassCard className={`p-5 group ${className}`} hover={true}>
      <div className="flex items-start gap-3.5">
        {Icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-[var(--accent)] text-white shadow-[var(--glow)] transition-transform duration-200 ease-out group-hover:scale-110 group-hover:rotate-3 gpu-accelerated ${isClay ? 'clay-card !p-0 !rounded-2xl !w-11 !h-11' : isBrutal ? 'brutal-card !p-0 !w-10 !h-10 !rounded-sm !shadow-[3px_3px_0px_var(--text)]' : 'rounded-xl'}`}>
            <Icon size={16} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-medium text-[13px] tracking-tight text-[var(--text)]">{title}</h3>
            {badge && <span className={`${isBrutal ? 'brutal-pill' : isClay ? 'clay-pill' : 'ui-pill-accent'} text-[9px] px-2 py-0.5`}>{badge}</span>}
          </div>
          {desc && <p className="text-[12px] mt-1 leading-relaxed text-[var(--text-sec)]">{desc}</p>}
          {children && <div className="mt-3">{children}</div>}
        </div>
      </div>
    </GlassCard>
  )
}

export function MetricCard({ label, value, change, icon: Icon, className = '' }) {
  const visualStyle = useSettingsStore(s => s.visualStyle) || 'liquid'
  const isPositive = change && parseFloat(change) >= 0
  const isClay = visualStyle === 'clay'
  const isBrutal = visualStyle === 'brutal'

  return (
    <div className={`p-4 rounded-xl border bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] transition-all duration-200 ease-out group gpu-accelerated ${isClay ? 'clay-card !rounded-2xl' : isBrutal ? 'brutal-card !rounded-sm' : 'hover:translate-y-[-1px] hover:shadow-[var(--shadow-md)]'} ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</span>
        {Icon && <Icon size={12} className="text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors duration-200" />}
      </div>
      <div className="text-[18px] font-semibold mono mt-2 tracking-tight text-[var(--text)]">{value}</div>
      {change && (
        <div className={`text-[11px] mt-1.5 flex items-center gap-1 font-bold px-2 py-0.5 rounded-full w-fit border ${isPositive ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'}`}>
          <span className="text-[10px]">{isPositive ? '↗' : '↘'}</span> {change}
        </div>
      )}
    </div>
  )
}
