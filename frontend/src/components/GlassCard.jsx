import { useSettingsStore } from '../store/useSettingsStore'

export default function GlassCard({ children, className = '', hover = true, glow = false, variant = 'default', style = {}, ...props }) {
  const blur = useSettingsStore(s => s.blur)
  
  const variantClasses = {
    default: 'ui-card',
    accent: 'ui-card',
    ghost: 'bg-transparent border border-dashed border-[var(--border)] rounded-xl',
    minimal: 'bg-[var(--card)] border border-[var(--border)] rounded-xl p-5',
  }
  
  return (
    <div 
      className={`${variantClasses[variant] || variantClasses.default} ${hover ? 'hover-lift' : ''} ${blur ? 'glass' : ''} ${className} gpu-accelerated`}
      style={{
        ...style,
      }}
      {...props}
    >
      <div className="relative z-10">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon, accent = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'mono'].includes(theme) || theme.includes('light')
  const isPositive = trend && (trend.includes('+') || parseFloat(trend) > 0)
  const isNegative = trend && (trend.includes('-') || parseFloat(trend) < 0)

  return (
    <GlassCard className={`p-5 group ${accent ? 'border-[var(--text)]' : ''}`} hover={true}>
      <div className="flex items-start justify-between mb-4 gpu-accelerated">
        <div className="flex items-center gap-2">
          <div className={`text-[10px] font-medium tracking-wide uppercase px-2.5 py-1 rounded-full bg-[var(--bg-secondary)] text-[var(--text-sec)] border border-[var(--border)]`}>
            {label}
          </div>
          {accent && <div className="w-1.5 h-1.5 rounded-full bg-[var(--text)] animate-pulse" />}
        </div>
        {Icon && (
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-200 ease-out group-hover:scale-105 gpu-accelerated ${isLight ? 'bg-[var(--text)] text-[var(--bg)]' : 'bg-[var(--text)] text-[var(--bg)]'}`}>
            <Icon size={14} />
          </div>
        )}
      </div>
      <div className="space-y-2">
        <div className={`text-[22px] font-semibold tracking-tight mono leading-none ${isLight ? 'text-[var(--text)]' : 'text-[var(--text)]'}`}>{value}</div>
        {subValue && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[12px] font-normal text-[var(--text-sec)]`}>{subValue}</span>
            {trend && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center gap-1 border gpu-accelerated ${isPositive ? 'bg-[var(--text)] text-[var(--bg)] border-[var(--text)]' : isNegative ? 'bg-transparent text-[var(--text-sec)] border-[var(--border-strong)]' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'}`}>
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
  return (
    <GlassCard className={`p-5 group ${className}`} hover={true}>
      <div className="flex items-start gap-3.5">
        {Icon && (
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 bg-[var(--text)] text-[var(--bg)] transition-transform duration-200 ease-out group-hover:scale-105 gpu-accelerated`}>
            <Icon size={16} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className={`font-medium text-[13px] tracking-tight text-[var(--text)]`}>{title}</h3>
            {badge && <span className="ui-pill text-[9px] px-2 py-0.5">{badge}</span>}
          </div>
          {desc && <p className={`text-[12px] mt-1 leading-relaxed text-[var(--text-sec)]`}>{desc}</p>}
          {children && <div className="mt-3">{children}</div>}
        </div>
      </div>
    </GlassCard>
  )
}

export function MetricCard({ label, value, change, icon: Icon, className = '' }) {
  return (
    <div className={`p-3.5 rounded-xl border bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] transition-all duration-200 ease-out hover:translate-y-[-1px] group gpu-accelerated ${className}`}>
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)]`}>{label}</span>
        {Icon && <Icon size={12} className={`text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors duration-200`} />}
      </div>
      <div className={`text-[16px] font-semibold mono mt-2 tracking-tight text-[var(--text)]`}>{value}</div>
      {change && (
        <div className={`text-[11px] mt-1 flex items-center gap-1 font-medium ${parseFloat(change) >= 0 ? 'text-[var(--text)]' : 'text-[var(--text-sec)]'}`}>
          <span className="text-[10px]">{parseFloat(change) >= 0 ? '↗' : '↘'}</span> {change}
        </div>
      )}
    </div>
  )
}
