import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, Sun, Moon, Activity, AlertTriangle, Palette, ChevronDown, Command } from 'lucide-react'
import { useState } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore, THEMES } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [themeOpen, setThemeOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()
  const { theme, toggleTheme, updateTheme } = useSettingsStore()
  const currentTheme = THEMES[theme] || THEMES.dark
  const isLight = ['light', 'sakura', 'mono'].includes(theme)

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home, desc: 'Overview' },
    { path: '/crash', label: 'Crash', icon: AlertTriangle, badge: 'NEW', desc: 'Early warning', accent: true },
    { path: '/trading', label: 'Trading', icon: Target, badge: 'REAL', desc: 'Live calls' },
    { path: '/autotrade', label: 'Auto', icon: Cpu, badge: 'BOT', desc: 'Automated' },
    { path: '/portfolio', label: 'Portfolio', icon: Wallet, desc: 'Holdings' },
    { path: '/strategies', label: 'Bots', icon: Bot, desc: 'Strategies' },
    { path: '/scanner', label: 'Scanner', icon: Search, desc: 'Market scan' },
    { path: '/analytics', label: 'Analytics', icon: LineChart, desc: 'Performance' },
    { path: '/alerts', label: 'Alerts', icon: Bell, desc: 'Notifications' },
    { path: '/journal', label: 'Journal', icon: BookOpen, desc: 'Trading log' },
    { path: '/training', label: 'Training', icon: GraduationCap, badge: 'LIVE', desc: 'AI models' },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp, desc: 'Predictions' },
    { path: '/realtime', label: 'Live', icon: Radio, badge: 'LIVE', desc: 'Realtime' },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles, desc: 'News & mood' },
    { path: '/backtest', label: 'Backtest', icon: BarChart3, desc: 'Validation' },
    { path: '/models', label: 'Models', icon: Brain, desc: 'AI status' },
    { path: '/settings', label: 'Settings', icon: Settings, desc: 'Preferences' },
  ]

  const primaryNav = nav.slice(0, 7)
  const secondaryNav = nav.slice(7, 11)
  const tertiaryNav = nav.slice(11)

  return (
    <nav className={`sticky top-0 z-50 border-b backdrop-blur-xl transition-all ${isLight ? 'bg-white/90 border-black/5' : 'bg-[var(--bg)]/90 border-[var(--border)]'} glass`}>
      {/* Top accent bar */}
      <div className="h-px w-full bg-gradient-to-r from-transparent via-[var(--accent)]/30 to-transparent" />
      
      <div className="max-w-[1600px] mx-auto px-4 md:px-6 h-[64px] flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 shrink-0 group">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-[15px] transition-all group-hover:scale-110 group-hover:rotate-3 shadow-lg ${isLight ? 'bg-black text-white' : 'bg-white text-black'} group-hover:shadow-[var(--glow)]`}>
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className={`font-bold text-[16px] tracking-tight ${isLight ? 'text-black' : 'text-white'} group-hover:tracking-wide transition-all`}>CryptoPred</span>
              <span className="ui-pill-accent px-2 py-0.5 text-[9px] font-black">V7</span>
              <span className={`hidden md:inline-flex text-[9px] px-2 py-0.5 rounded-full font-bold ${currentTheme.preview} border`}>{currentTheme.icon} {currentTheme.name}</span>
            </div>
            <div className={`text-[11px] font-medium flex items-center gap-2 ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
              <span className="flex items-center gap-1.5">
                {isLive && <span className="live-dot !w-1.5 !h-1.5"></span>}
                REAL MONEY
              </span>
              <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
              <span className="text-[var(--accent)] font-bold">COINDCX • {Object.keys(THEMES).length} THEMES</span>
            </div>
          </div>
        </Link>

        {/* Desktop nav - Primary */}
        <div className="hidden xl:flex items-center gap-1">
          {primaryNav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-[13px] font-medium transition-all whitespace-nowrap relative overflow-hidden ${
                  active
                    ? 'bg-[var(--accent)] text-[var(--bg)] shadow-lg shadow-[var(--accent)]/20 scale-[1.02]'
                    : isLight ? 'text-zinc-600 hover:text-black hover:bg-black/5' : 'text-zinc-400 hover:text-white hover:bg-white/10'
                } ${item.accent && !active ? 'ring-1 ring-orange-500/20' : ''}`}
                title={item.desc}
              >
                <item.icon size={15} className={`transition-transform group-hover:scale-110 ${active ? '' : 'group-hover:rotate-3'}`} />
                <span className="hidden 2xl:inline">{item.label}</span>
                {item.badge && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[8px] font-black tracking-wide ${active ? 'bg-black/20 text-white' : item.badge === 'NEW' ? 'bg-orange-500 text-white animate-pulse' : item.badge === 'REAL' ? 'bg-emerald-500 text-black' : 'bg-[var(--accent)] text-[var(--bg)]'}`}>
                    {item.badge}
                  </span>
                )}
                {active && <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent pointer-events-none" />}
              </Link>
            )
          })}
          
          <div className={`w-px h-6 mx-2 ${isLight ? 'bg-black/10' : 'bg-white/10'}`} />
          
          {/* Secondary icons */}
          <div className="flex items-center gap-1">
            {secondaryNav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link 
                  key={item.path} 
                  to={item.path} 
                  className={`group p-2.5 rounded-xl transition-all relative ${active ? 'bg-[var(--accent)] text-[var(--bg)] shadow-md' : isLight ? 'text-zinc-500 hover:text-black hover:bg-black/5 hover:scale-110' : 'text-zinc-500 hover:text-white hover:bg-white/10 hover:scale-110'}`}
                  title={`${item.label} - ${item.desc}`}
                >
                  <item.icon size={16} className="transition-transform group-hover:rotate-6" />
                  {item.badge && <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />}
                </Link>
              )
            })}
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-2">
          {/* Theme selector */}
          <div className="relative">
            <button
              onClick={() => setThemeOpen(!themeOpen)}
              className={`hidden md:flex items-center gap-2 px-3 py-2.5 rounded-xl border transition-all hover:scale-105 ${isLight ? 'bg-zinc-50 border-black/5 text-zinc-700 hover:border-black/10 hover:bg-white' : 'bg-white/5 border-white/10 text-zinc-300 hover:text-white hover:bg-white/10 hover:border-white/20'} backdrop-blur`}
            >
              <span className="text-[14px]">{currentTheme.icon}</span>
              <span className="text-[12px] font-semibold hidden lg:inline">{currentTheme.name}</span>
              <ChevronDown size={12} className={`transition-transform ${themeOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {themeOpen && (
              <div className={`absolute top-full right-0 mt-2 w-72 rounded-2xl border shadow-2xl z-50 overflow-hidden animate-scaleIn ${isLight ? 'bg-white border-black/10' : 'bg-zinc-900 border-white/10'} glass max-h-[70vh] overflow-y-auto`}>
                <div className={`p-3 border-b ${isLight ? 'border-black/5 bg-zinc-50' : 'border-white/5 bg-white/5'}`}>
                  <div className={`font-bold text-[13px] flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
                    <Palette size={14} /> {Object.keys(THEMES).length} Themes
                  </div>
                  <div className={`text-[11px] ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Choose your trading vibe</div>
                </div>
                <div className="p-2 grid grid-cols-1 gap-1">
                  {Object.values(THEMES).map(t => (
                    <button
                      key={t.id}
                      onClick={() => { updateTheme(t.id); setThemeOpen(false) }}
                      className={`w-full text-left p-3 rounded-xl flex items-center gap-3 transition-all hover:scale-[1.02] ${theme === t.id ? 'bg-[var(--accent)] text-[var(--bg)] shadow-lg' : isLight ? 'hover:bg-black/5 text-zinc-700' : 'hover:bg-white/5 text-zinc-300'}`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[16px] border ${t.preview} shrink-0`}>
                        {t.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-[13px] flex items-center gap-2">
                          {t.name}
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${theme === t.id ? 'bg-black/20 text-white' : 'bg-[var(--accent-soft)] text-[var(--text-muted)]'}`}>{t.category}</span>
                        </div>
                        <div className={`text-[11px] truncate ${theme === t.id ? 'text-white/70' : isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{t.desc}</div>
                      </div>
                      {theme === t.id && <div className="w-2 h-2 rounded-full bg-white animate-pulse" />}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick theme toggle */}
          <button
            onClick={toggleTheme}
            className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all hover:scale-110 hover:rotate-12 ${isLight ? 'bg-zinc-50 border-black/5 text-zinc-600 hover:text-black hover:bg-white hover:shadow-md' : 'bg-white/5 border-white/10 text-zinc-400 hover:text-white hover:bg-white/10'}`}
            title="Quick theme toggle"
          >
            {isLight ? <Moon size={16} /> : <Sun size={16} />}
          </button>

          {/* Status */}
          <div className={`hidden lg:flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] font-medium ${isLight ? 'bg-zinc-50 border-black/5 text-zinc-600' : 'bg-white/5 border-white/10 text-zinc-400'}`}>
            <Activity size={14} className={`${isLive ? 'text-emerald-500' : 'text-zinc-500'} ${isLive ? 'animate-pulse' : ''}`} />
            <span className="hidden xl:inline">{lastUpdate ? lastUpdate.toLocaleTimeString() : 'Syncing'}</span>
            {isLive && <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse hidden xl:inline-block" />}
          </div>

          {/* CTA */}
          <Link to="/trading" className={`hidden md:flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-bold transition-all hover:scale-105 hover:shadow-lg group ${isLight ? 'bg-black text-white hover:bg-zinc-800' : 'bg-white text-black hover:bg-zinc-100'}`}>
            <Target size={14} className="group-hover:rotate-12 transition-transform" />
            <span className="hidden lg:inline">Trading</span>
            <span className="px-1.5 py-0.5 rounded-full bg-emerald-500 text-black text-[9px] font-black">REAL</span>
          </Link>

          {/* Mobile menu */}
          <button 
            onClick={() => setMobileOpen(!mobileOpen)} 
            className={`xl:hidden w-10 h-10 rounded-xl flex items-center justify-center border transition-all hover:scale-110 ${isLight ? 'bg-zinc-50 border-black/5 text-zinc-600' : 'bg-white/5 border-white/10 text-zinc-400'} ${mobileOpen ? 'rotate-90' : ''}`}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className={`xl:hidden border-t backdrop-blur-xl animate-slideIn max-h-[80vh] overflow-y-auto ${isLight ? 'bg-white/95 border-black/5' : 'bg-black/95 border-white/10'} glass`}>
          <div className="p-4 space-y-4">
            {/* Mobile theme grid */}
            <div>
              <div className={`text-[11px] font-bold uppercase tracking-wide mb-2 flex items-center gap-2 ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
                <Palette size={12} /> Themes • {Object.keys(THEMES).length} available
              </div>
              <div className="grid grid-cols-3 gap-2">
                {Object.values(THEMES).slice(0, 9).map(t => (
                  <button
                    key={t.id}
                    onClick={() => updateTheme(t.id)}
                    className={`p-2.5 rounded-xl border text-center transition-all hover:scale-105 ${theme === t.id ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-lg' : isLight ? 'bg-zinc-50 border-black/5 hover:bg-white hover:border-black/10' : 'bg-white/5 border-white/10 hover:bg-white/10'}`}
                  >
                    <div className="text-[18px]">{t.icon}</div>
                    <div className="text-[10px] font-bold mt-1">{t.name}</div>
                  </button>
                ))}
              </div>
              <Link to="/settings" onClick={() => setMobileOpen(false)} className={`mt-2 w-full p-2 rounded-xl border text-center text-[11px] font-medium flex items-center justify-center gap-1 ${isLight ? 'border-black/5 text-zinc-600 hover:bg-black/5' : 'border-white/10 text-zinc-400 hover:bg-white/5'}`}>
                <Settings size={12} /> All themes in Settings
              </Link>
            </div>

            {/* Nav grid */}
            <div>
              <div className={`text-[11px] font-bold uppercase tracking-wide mb-2 ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Navigation</div>
              <div className="grid grid-cols-2 gap-2">
                {nav.map(item => {
                  const active = loc.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      className={`p-3.5 rounded-xl flex items-center gap-3 text-[13px] font-medium transition-all hover:scale-[1.02] ${
                        active 
                          ? 'bg-[var(--accent)] text-[var(--bg)] shadow-lg' 
                          : isLight ? 'bg-zinc-50 border border-black/5 text-zinc-700 hover:bg-white hover:border-black/10' : 'bg-white/5 border border-white/10 text-zinc-300 hover:bg-white/10 hover:text-white'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${active ? 'bg-black/20' : isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
                        <item.icon size={16} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold">{item.label}</div>
                        <div className={`text-[10px] ${active ? 'text-white/70' : isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{item.desc}</div>
                      </div>
                      {item.badge && <span className={`px-1.5 py-0.5 rounded-full text-[8px] font-black ${active ? 'bg-white text-black' : 'bg-[var(--accent)] text-[var(--bg)]'}`}>{item.badge}</span>}
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
