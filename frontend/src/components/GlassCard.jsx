import { useSettingsStore } from '../store/useSettingsStore'

export default function GlassCard({ children, className = '', hover = true, ...props }) {
  return (
    <div className={`ui-card ${hover ? '' : ''} ${className}`} {...props}>
      <div className="relative z-10">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon: Icon }) {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  const isPositive = trend && (trend.includes('+') || parseFloat(trend) > 0)

  return (
    <GlassCard className="p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`text-[10px] font-bold tracking-widest uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{label}</div>
        {Icon && (
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}>
            <Icon size={14} />
          </div>
        )}
      </div>
      <div className="space-y-1">
        <div className={`text-xl font-bold tracking-tight mono ${isDark ? 'text-white' : 'text-black'}`}>{value}</div>
        {subValue && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[12px] ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{subValue}</span>
            {trend && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${isPositive ? 'ui-pill-buy' : 'ui-pill-sell'}`}>{trend}</span>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  )
}
