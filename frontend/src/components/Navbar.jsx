import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, Sun, Moon, Activity, AlertTriangle, Palette, ChevronDown } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore, THEMES } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [themeOpen, setThemeOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()
  const { theme, toggleTheme, updateTheme } = useSettingsStore()
  const currentTheme = THEMES[theme] || THEMES.dark
  const isLight = theme === 'light' || theme === 'mono'
  const themeRef = useRef(null)

  // Close theme dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (themeRef.current && !themeRef.current.contains(e.target)) {
        setThemeOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/crash', label: 'Crash', icon: AlertTriangle, dot: true },
    { path: '/trading', label: 'Trading', icon: Target },
    { path: '/autotrade', label: 'Auto', icon: Cpu },
    { path: '/portfolio', label: 'Portfolio', icon: Wallet },
    { path: '/strategies', label: 'Bots', icon: Bot },
    { path: '/scanner', label: 'Scanner', icon: Search },
    { path: '/analytics', label: 'Analytics', icon: LineChart },
    { path: '/alerts', label: 'Alerts', icon: Bell },
    { path: '/journal', label: 'Journal', icon: BookOpen },
    { path: '/training', label: 'Training', icon: GraduationCap },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp },
    { path: '/realtime', label: 'Live', icon: Radio },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles },
    { path: '/backtest', label: 'Backtest', icon: BarChart3 },
    { path: '/models', label: 'Models', icon: Brain },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  const primaryNav = nav.slice(0, 6)
  const secondaryNav = nav.slice(6, 10)

  return (
    <nav className={`sticky top-0 z-50 border-b backdrop-blur-xl gpu-accelerated ${isLight ? 'bg-white/80 border-zinc-200' : 'bg-[#09090b]/80 border-zinc-800'} `} style={{ transform: 'translateZ(0)' }}>
      <div className="max-w-[1600px] mx-auto px-4 md:px-5 h-[56px] flex items-center justify-between gap-4">
        {/* Logo - minimal */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group gpu-accelerated">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-semibold text-[13px] transition-transform duration-200 ease-out group-hover:scale-105 ${isLight ? 'bg-zinc-900 text-white' : 'bg-white text-black'}`}>
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className={`font-semibold text-[14px] tracking-tight ${isLight ? 'text-zinc-900' : 'text-white'}`}>CryptoPred</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-zinc-900 text-white dark:bg-white dark:text-black">V8</span>
            </div>
          </div>
        </Link>

        {/* Desktop nav - minimal pill style, 120fps */}
        <div className="hidden lg:flex items-center gap-1">
          {primaryNav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium gpu-accelerated navbar-link ${
                  active
                    ? 'bg-zinc-900 text-white dark:bg-white dark:text-black shadow-sm'
                    : isLight ? 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                }`}
              >
                <item.icon size={14} className="transition-transform duration-200 group-hover:scale-105" />
                <span>{item.label}</span>
                {item.dot && !active && <span className="w-1 h-1 rounded-full bg-zinc-900 dark:bg-white ml-1" />}
              </Link>
            )
          })}
          
          <div className={`w-px h-4 mx-2 ${isLight ? 'bg-zinc-200' : 'bg-zinc-800'}`} />
          
          <div className="flex items-center gap-1">
            {secondaryNav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link 
                  key={item.path} 
                  to={item.path} 
                  className={`p-2 rounded-full transition-all duration-200 gpu-accelerated navbar-link ${active ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : isLight ? 'text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100' : 'text-zinc-500 hover:text-white hover:bg-zinc-800'}`}
                  title={item.label}
                >
                  <item.icon size={14} />
                </Link>
              )
            })}
          </div>
        </div>

        {/* Right actions - minimal */}
        <div className="flex items-center gap-1.5">
          {/* Theme selector - minimal */}
          <div className="relative" ref={themeRef}>
            <button
              onClick={() => setThemeOpen(!themeOpen)}
              className={`hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border text-[12px] font-medium gpu-accelerated transition-all duration-200 hover:scale-[1.02] ${isLight ? 'bg-white border-zinc-200 text-zinc-600 hover:border-zinc-300' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700'}`}
            >
              <span className="text-[12px]">{currentTheme.icon}</span>
              <ChevronDown size={12} className={`transition-transform duration-200 ${themeOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {themeOpen && (
              <div className={`absolute top-full right-0 mt-2 w-64 rounded-xl border shadow-lg z-50 overflow-hidden animate-scaleIn gpu-accelerated ${isLight ? 'bg-white border-zinc-200' : 'bg-zinc-900 border-zinc-800'} max-h-[60vh] overflow-y-auto no-scrollbar`}>
                <div className={`p-3 border-b ${isLight ? 'border-zinc-100 bg-zinc-50' : 'border-zinc-800 bg-zinc-900'}`}>
                  <div className={`font-medium text-[12px] ${isLight ? 'text-zinc-900' : 'text-white'}`}>Themes</div>
                  <div className={`text-[11px] ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Minimal monochrome</div>
                </div>
                <div className="p-2 grid grid-cols-1 gap-1">
                  {Object.values(THEMES).slice(0, 6).map(t => (
                    <button
                      key={t.id}
                      onClick={() => { updateTheme(t.id); setThemeOpen(false) }}
                      className={`w-full text-left p-2.5 rounded-lg flex items-center gap-2.5 transition-all duration-200 hover:scale-[1.01] gpu-accelerated ${theme === t.id ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : isLight ? 'hover:bg-zinc-50 text-zinc-600' : 'hover:bg-zinc-800 text-zinc-400'}`}
                    >
                      <div className={`w-7 h-7 rounded-md flex items-center justify-center text-[14px] border ${isLight ? 'bg-zinc-50 border-zinc-200' : 'bg-zinc-800 border-zinc-700'}`}>
                        {t.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-[12px]">{t.name}</div>
                        <div className={`text-[10px] ${theme === t.id ? 'text-white/60 dark:text-black/60' : 'text-zinc-500'}`}>{t.desc}</div>
                      </div>
                      {theme === t.id && <div className="w-1.5 h-1.5 rounded-full bg-white dark:bg-black" />}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={toggleTheme}
            className={`w-8 h-8 rounded-full flex items-center justify-center border transition-all duration-200 hover:scale-105 gpu-accelerated ${isLight ? 'bg-white border-zinc-200 text-zinc-500 hover:text-zinc-900' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white'}`}
            title="Toggle theme"
          >
            {isLight ? <Moon size={14} /> : <Sun size={14} />}
          </button>

          <div className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium ${isLight ? 'bg-zinc-50 border-zinc-200 text-zinc-500' : 'bg-zinc-900 border-zinc-800 text-zinc-400'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-zinc-900 dark:bg-white animate-pulse' : 'bg-zinc-400'}`} />
            <span className="hidden xl:inline">{isLive ? 'Live' : 'Offline'}</span>
          </div>

          <Link to="/trading" className={`hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-200 hover:scale-[1.02] gpu-accelerated ${isLight ? 'bg-zinc-900 text-white hover:bg-zinc-800' : 'bg-white text-black hover:bg-zinc-100'}`}>
            <Target size={12} />
            <span>Trade</span>
          </Link>

          <button 
            onClick={() => setMobileOpen(!mobileOpen)} 
            className={`lg:hidden w-8 h-8 rounded-full flex items-center justify-center border transition-all duration-200 gpu-accelerated ${isLight ? 'bg-white border-zinc-200 text-zinc-600' : 'bg-zinc-900 border-zinc-800 text-zinc-400'} ${mobileOpen ? 'rotate-90' : ''}`}
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {/* Mobile menu - minimal 120fps */}
      {mobileOpen && (
        <div className={`lg:hidden border-t backdrop-blur-xl animate-slideIn gpu-accelerated max-h-[80vh] overflow-y-auto no-scrollbar ${isLight ? 'bg-white/95 border-zinc-200' : 'bg-zinc-900/95 border-zinc-800'}`}>
          <div className="p-3 grid grid-cols-2 gap-2">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`p-3 rounded-xl flex items-center gap-2.5 text-[13px] font-medium transition-all duration-200 gpu-accelerated ${
                    active 
                      ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' 
                      : isLight ? 'bg-zinc-50 border border-zinc-200 text-zinc-600 hover:bg-white' : 'bg-zinc-800 border border-zinc-700 text-zinc-300 hover:bg-zinc-700'
                  }`}
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}
