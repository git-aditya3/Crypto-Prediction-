import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, Sun, Moon, Activity } from 'lucide-react'
import { useState } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()
  const { theme, toggleTheme } = useSettingsStore()
  const isDark = theme === 'dark'

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/trading', label: 'Trading', icon: Target, badge: 'REAL' },
    { path: '/autotrade', label: 'Auto', icon: Cpu, badge: 'NEW' },
    { path: '/portfolio', label: 'Portfolio', icon: Wallet },
    { path: '/strategies', label: 'Bots', icon: Bot },
    { path: '/scanner', label: 'Scanner', icon: Search },
    { path: '/analytics', label: 'Analytics', icon: LineChart },
    { path: '/alerts', label: 'Alerts', icon: Bell },
    { path: '/journal', label: 'Journal', icon: BookOpen },
    { path: '/training', label: 'Training', icon: GraduationCap, badge: 'LIVE' },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp },
    { path: '/realtime', label: 'Live', icon: Radio, badge: 'LIVE' },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles },
    { path: '/backtest', label: 'Backtest', icon: BarChart3 },
    { path: '/models', label: 'Models', icon: Brain },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  const primaryNav = nav.slice(0, 7)
  const secondaryNav = nav.slice(7)

  return (
    <nav className={`sticky top-11 z-40 border-b backdrop-blur-xl ${isDark ? 'bg-black/90 border-white/[0.06]' : 'bg-white/80 border-black/[0.06]'}`}>
      <div className="max-w-[1600px] mx-auto px-4 md:px-6 h-[56px] flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 shrink-0">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-[14px] ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}>
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className={`font-bold text-[15px] tracking-tight ${isDark ? 'text-white' : 'text-black'}`}>CryptoPred</span>
              <span className="clay-pill px-2 py-0.5 text-[9px]">V7</span>
            </div>
            <div className={`text-[10px] font-medium flex items-center gap-1.5 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
              {isLive && <span className="live-dot !w-1 !h-1"></span>}
              REAL MONEY • COINDCX
            </div>
          </div>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-1 overflow-x-auto">
          {primaryNav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-all whitespace-nowrap ${
                  active
                    ? isDark ? 'bg-white text-black' : 'bg-black text-white'
                    : isDark ? 'text-zinc-400 hover:text-white hover:bg-white/10' : 'text-zinc-500 hover:text-black hover:bg-black/5'
                }`}
              >
                <item.icon size={14} />
                {item.label}
                {item.badge && <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[8px] font-bold ${active ? 'bg-black text-white dark:bg-black dark:text-white' : 'clay-pill-live'}`}>{item.badge}</span>}
              </Link>
            )
          })}
          <div className={`w-px h-5 mx-1 ${isDark ? 'bg-white/10' : 'bg-black/10'}`} />
          {secondaryNav.slice(0, 4).map(item => {
            const active = loc.pathname === item.path
            return (
              <Link key={item.path} to={item.path} className={`p-2 rounded-xl transition-colors ${active ? (isDark ? 'bg-white text-black' : 'bg-black text-white') : (isDark ? 'text-zinc-500 hover:text-white hover:bg-white/10' : 'text-zinc-400 hover:text-black hover:bg-black/5')}`}>
                <item.icon size={16} />
              </Link>
            )
          })}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-colors ${isDark ? 'bg-zinc-900 border-white/10 text-zinc-400 hover:text-white' : 'bg-zinc-50 border-black/5 text-zinc-500 hover:text-black'}`}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <div className={`hidden md:flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] ${isDark ? 'bg-zinc-900/50 border-white/5 text-zinc-500' : 'bg-zinc-50 border-black/5 text-zinc-500'}`}>
            <Activity size={12} className="text-emerald-500" />
            {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Syncing'}
          </div>

          <Link to="/trading" className={`hidden md:flex items-center gap-1.5 px-4 py-2 rounded-xl text-[12px] font-bold transition-colors ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-black text-white hover:bg-zinc-800'}`}>
            <Target size={14} /> Trading
          </Link>

          <button onClick={() => setMobileOpen(!mobileOpen)} className={`lg:hidden w-9 h-9 rounded-xl flex items-center justify-center border ${isDark ? 'bg-zinc-900 border-white/10 text-zinc-400' : 'bg-zinc-50 border-black/5 text-zinc-500'}`}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile */}
      {mobileOpen && (
        <div className={`lg:hidden border-t max-h-[75vh] overflow-auto ${isDark ? 'bg-black border-white/10' : 'bg-white border-black/5'}`}>
          <div className="p-3 grid grid-cols-2 gap-2">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`p-3 rounded-xl flex items-center gap-2.5 text-[13px] font-medium transition-colors ${
                    active ? (isDark ? 'bg-white text-black' : 'bg-black text-white') : (isDark ? 'bg-zinc-900 border border-white/5 text-zinc-400' : 'bg-zinc-50 border border-black/5 text-zinc-600')
                  }`}
                >
                  <item.icon size={16} />
                  {item.label}
                  {item.badge && <span className="ml-auto clay-pill-live px-1.5 py-0.5 text-[8px]">{item.badge}</span>}
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}
