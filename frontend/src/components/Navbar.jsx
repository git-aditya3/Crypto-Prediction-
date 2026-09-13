import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, Sun, Moon, AlertTriangle, ChevronDown } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore, THEMES, THEME_CATEGORIES } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [themeOpen, setThemeOpen] = useState(false)
  const [themeCategory, setThemeCategory] = useState('All')
  const { isLive } = useMarketStore()
  const { theme, toggleTheme, updateTheme } = useSettingsStore()
  const currentTheme = THEMES[theme] || THEMES.dark
  const themeRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (themeRef.current && !themeRef.current.contains(e.target)) {
        setThemeOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [loc.pathname])

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
  const secondaryNav = nav.slice(6, 12)

  const filteredThemes = themeCategory === 'All' ? Object.values(THEMES) : Object.values(THEMES).filter(t => t.category === themeCategory)

  return (
    <nav className="sticky top-0 z-50 border-b backdrop-blur-xl gpu-accelerated bg-[var(--card)]/80 border-[var(--border)]" style={{ transform: 'translateZ(0)' }}>
      <div className="max-w-[1600px] mx-auto px-4 md:px-5 h-[56px] flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group gpu-accelerated">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-[14px] bg-[var(--accent)] text-white shadow-[var(--glow)] transition-transform duration-200 ease-out group-hover:scale-110 group-hover:rotate-3">
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[14px] tracking-tight text-[var(--text)]">CryptoPred</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-[var(--accent)] text-white">V8</span>
            </div>
          </div>
        </Link>

        <div className="hidden lg:flex items-center gap-1">
          {primaryNav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium gpu-accelerated navbar-link transition-all duration-200 ${
                  active
                    ? 'bg-[var(--accent)] text-white shadow-[var(--glow)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-secondary)]'
                }`}
              >
                <item.icon size={14} className="transition-transform duration-200 group-hover:scale-110" />
                <span>{item.label}</span>
                {item.dot && !active && <span className="w-1 h-1 rounded-full bg-[var(--accent)] ml-1 animate-pulse" />}
              </Link>
            )
          })}
          
          <div className="w-px h-4 mx-2 bg-[var(--border)]" />
          
          <div className="flex items-center gap-1">
            {secondaryNav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link 
                  key={item.path} 
                  to={item.path} 
                  className={`p-2 rounded-full transition-all duration-200 gpu-accelerated navbar-link ${active ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-secondary)]'}`}
                  title={item.label}
                >
                  <item.icon size={14} />
                </Link>
              )
            })}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="relative" ref={themeRef}>
            <button
              onClick={() => setThemeOpen(!themeOpen)}
              className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border text-[12px] font-medium gpu-accelerated transition-all duration-200 hover:scale-[1.02] bg-[var(--card)] border-[var(--border)] text-[var(--text-sec)] hover:border-[var(--border-strong)]"
            >
              <span className="text-[14px]">{currentTheme.icon}</span>
              <span className="hidden xl:inline">{currentTheme.name}</span>
              <ChevronDown size={12} className={`transition-transform duration-200 ${themeOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {themeOpen && (
              <div className="absolute top-full right-0 mt-2 w-[320px] rounded-xl border shadow-[var(--shadow-lg)] z-50 overflow-hidden animate-scaleIn gpu-accelerated bg-[var(--card)] border-[var(--border)] max-h-[70vh] flex flex-col">
                <div className="p-3 border-b border-[var(--border)] bg-[var(--bg-secondary)]">
                  <div className="font-medium text-[12px] text-[var(--text)] flex items-center justify-between">
                    <span>Themes • {Object.keys(THEMES).length}</span>
                    <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px]">{currentTheme.category}</span>
                  </div>
                  <div className="flex gap-1 mt-2">
                    {THEME_CATEGORIES.map(cat => (
                      <button
                        key={cat}
                        onClick={() => setThemeCategory(cat)}
                        className={`px-2 py-1 rounded-full text-[10px] font-medium transition-all ${themeCategory === cat ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:bg-[var(--border)]'}`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="p-2 grid grid-cols-1 gap-1 overflow-y-auto no-scrollbar flex-1">
                  {filteredThemes.map(t => (
                    <button
                      key={t.id}
                      onClick={() => { updateTheme(t.id); setThemeOpen(false) }}
                      className={`w-full text-left p-2.5 rounded-lg flex items-center gap-2.5 transition-all duration-200 hover:scale-[1.01] gpu-accelerated border ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-secondary)] text-[var(--text-sec)]'}`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[16px] border ${theme === t.id ? 'bg-white/20 border-white/20' : 'bg-[var(--bg-secondary)] border-[var(--border)]'}`}>
                        {t.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-[12px] flex items-center gap-1.5">
                          {t.name}
                          {theme === t.id && <span className="w-1 h-1 rounded-full bg-white animate-pulse" />}
                        </div>
                        <div className={`text-[10px] truncate ${theme === t.id ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{t.desc} • {t.category}</div>
                      </div>
                      <div className="flex gap-1">
                        {Object.values(t.colors).slice(0, 3).map((c, i) => (
                          <div key={i} className="w-3 h-3 rounded-full border border-white/20 shadow-sm" style={{ background: c }} />
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-full flex items-center justify-center border transition-all duration-200 hover:scale-110 gpu-accelerated bg-[var(--card)] border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text)] hover:border-[var(--border-strong)]"
            title="Toggle theme"
          >
            <Sun size={14} className="dark:hidden" />
            <Moon size={14} className="hidden dark:block" />
            <span className="hidden dark:hidden light:block"><Moon size={14} /></span>
          </button>

          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-muted)]">
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-[var(--buy)] animate-pulse' : 'bg-[var(--text-faint)]'}`} />
            <span className="hidden xl:inline">{isLive ? 'Live' : 'Offline'}</span>
          </div>

          <Link to="/trading" className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-200 hover:scale-[1.02] gpu-accelerated bg-[var(--accent)] text-white shadow-[var(--glow)] hover:shadow-[var(--shadow-md)]">
            <Target size={12} />
            <span>Trade</span>
          </Link>

          <button 
            onClick={() => setMobileOpen(!mobileOpen)} 
            className={`lg:hidden w-8 h-8 rounded-full flex items-center justify-center border transition-all duration-200 gpu-accelerated bg-[var(--card)] border-[var(--border)] text-[var(--text-muted)] ${mobileOpen ? 'rotate-90 bg-[var(--accent)] text-white border-[var(--accent)]' : ''}`}
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t backdrop-blur-xl animate-slideIn gpu-accelerated max-h-[80vh] overflow-y-auto no-scrollbar bg-[var(--card)]/95 border-[var(--border)]">
          <div className="p-3 grid grid-cols-2 gap-2">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`p-3 rounded-xl flex items-center gap-2.5 text-[13px] font-medium transition-all duration-200 gpu-accelerated border ${
                    active 
                      ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' 
                      : 'bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-sec)] hover:bg-[var(--card)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
          <div className="p-3 border-t border-[var(--border)]">
            <div className="text-[11px] font-medium text-[var(--text-muted)] mb-2">Themes</div>
            <div className="grid grid-cols-4 gap-2">
              {Object.values(THEMES).map(t => (
                <button
                  key={t.id}
                  onClick={() => { updateTheme(t.id); setMobileOpen(false) }}
                  className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)]' : 'bg-[var(--card)] border-[var(--border)] text-[var(--text-sec)]'}`}
                >
                  <span className="text-[18px]">{t.icon}</span>
                  <span className="text-[9px] font-medium">{t.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
