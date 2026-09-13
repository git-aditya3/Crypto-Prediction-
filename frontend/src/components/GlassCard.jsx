import { useSettingsStore } from '../store/useSettingsStore'

export default function GlassCard({ children, className = '', hover = true, gradient = false, clay = true, ...props }) {
  const theme = useSettingsStore(s => s.theme)

  if (clay) {
    // Claymorphism card - high priority interactive elements
    return (
      <div 
        className={`
          clay-card relative overflow-hidden
          ${hover ? 'cursor-pointer' : ''}
          ${className}
        `}
        {...props}
      >
        {/* Subtle inner glow for depth */}
        <div className="absolute inset-0 rounded-[32px] pointer-events-none"
          style={{
            background: theme === 'light' 
              ? 'linear-gradient(135deg, rgba(255,255,255,0.8) 0%, transparent 50%)'
              : 'linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 50%)'
          }}
        ></div>
        <div className="relative z-10">
          {children}
        </div>
      </div>
    )
  }

  // Fallback flat for structural walls (Rule 3)
  return (
    <div 
      className={`
        relative rounded-[32px] overflow-hidden clay-flat
        ${className}
      `}
      {...props}
    >
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon, accent = 'accent' }) {
  const theme = useSettingsStore(s => s.theme)
  
  const accentColors = {
    accent: 'from-emerald-500 to-green-600',
    accent2: 'from-violet-500 to-purple-600',
    bear: 'from-red-500 to-red-600',
    bull: 'from-emerald-500 to-green-600',
    warning: 'from-amber-500 to-orange-500'
  }

  const isPositive = trend && (trend.includes('+') || parseFloat(trend) > 0)

  return (
    <GlassCard className="p-6" clay={true}>
      <div className="flex items-start justify-between mb-4">
        <div className="text-[11px] font-bold tracking-widest uppercase font-poppins"
          style={{ color: theme === 'light' ? '#64748b' : '#9CA3AF' }}>
          {label}
        </div>
        {Icon && (
          <div className={`w-10 h-10 rounded-[16px] bg-gradient-to-br ${accentColors[accent]} flex items-center justify-center shadow-lg clay-float`}
            style={theme === 'dark' ? {
              boxShadow: '0px 8px 16px rgba(0,0,0,0.4), inset 2px 2px 4px rgba(255,255,255,0.15), inset -2px -2px 4px rgba(0,0,0,0.3)'
            } : {
              boxShadow: '0px 8px 16px rgba(31,38,135,0.08), inset 3px 3px 6px rgba(255,255,255,0.9), inset -3px -3px 6px rgba(0,0,0,0.08)'
            }}>
            <Icon size={16} className="text-black" />
          </div>
        )}
      </div>
      <div className="space-y-2">
        <div className="text-2xl font-black tracking-tight mono"
          style={{ color: theme === 'light' ? '#1e293b' : '#F3F4F6' }}>
          {value}
        </div>
        {subValue && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm" style={{ color: theme === 'light' ? '#64748b' : '#9CA3AF' }}>{subValue}</span>
            {trend && (
              <span className={`clay-pill text-xs font-bold px-3 py-1 rounded-full ${
                isPositive 
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' 
                  : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
              }`}>
                {trend}
              </span>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  )
}

export function ClayButton({ children, variant = 'primary', className = '', ...props }) {
  const theme = useSettingsStore(s => s.theme)
  
  const base = "clay-btn font-poppins font-bold transition-all duration-300 active:scale-[0.98]"
  
  if (variant === 'accent') {
    return (
      <button className={`${base} clay-btn-accent px-6 py-3 ${className}`} {...props}>
        {children}
      </button>
    )
  }
  
  return (
    <button className={`${base} clay-btn-primary px-6 py-3 ${className}`} {...props}>
      {children}
    </button>
  )
}
