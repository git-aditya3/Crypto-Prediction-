import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, Sun, Moon, AlertTriangle, ChevronDown, Palette } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore, THEMES, THEME_CATEGORIES, VISUAL_STYLES } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [themeOpen, setThemeOpen] = useState(false)
  const [themeCategory, setThemeCategory] = useState('All')
  const { isLive } = useMarketStore()
  const { theme, visualStyle, updateTheme, updateVisualStyle } = useSettingsStore()
  const currentTheme = THEMES[theme] || THEMES.dark
  const currentVisual = VISUAL_STYLES[visualStyle] || VISUAL_STYLES.liquid
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

  const isClay = visualStyle === 'clay'
  const isBrutal = visualStyle === 'brutal'
  const isLiquid = visualStyle === 'liquid'

  return (
    <nav className={`sticky top-0 z-50 border-b gpu-accelerated ${isLiquid ? 'liquid-glass' : isClay ? 'clay-card !rounded-none !p-0 !border-x-0 !border-t-0 !shadow-none' : isBrutal ? 'brutal-card !rounded-none !p-0 !border-x-0 !border-t-0 !border-b-[3px]' : 'bg-[var(--card)]/80 backdrop-blur-xl border-[var(--border)]'}`} style={{ transform: 'translateZ(0)' }}>
      <div className="max-w-[1600px] mx-auto px-4 md:px-5 h-[60px] flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group gpu-accelerated">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-[14px] bg-[var(--accent)] text-white shadow-[var(--glow)] transition-transform duration-200 ease-out group-hover:scale-110 group-hover:rotate-3 ${isClay ? 'clay-card !p-0 !w-10 !h-10 !rounded-2xl' : isBrutal ? 'brutal-card !p-0 !w-9 !h-9 !rounded-sm !shadow-[3px_3px_0px_var(--text)]' : 'rounded-xl'}`}>
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[14px] tracking-tight text-[var(--text)]">CryptoPred</span>
              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold bg-[var(--accent)] text-white shadow-sm ${isBrutal ? 'brutal-pill !py-0 !px-1.5 !text-[8px]' : ''}`}>V8</span>
              <span className={`hidden lg:inline-flex px-2 py-0.5 rounded-full text-[9px] font-medium border ${isClay ? 'clay-pill !text-[8px]' : 'bg-[var(--accent-soft)] border-[var(--border)] text-[var(--accent)]'}`}>{currentVisual.icon} {currentVisual.name}</span>
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
                    ? `bg-[var(--accent)] text-white shadow-[var(--glow)] ${isClay ? 'clay-btn !py-1.5 !px-4 !bg-[var(--accent)] !text-white' : isBrutal ? 'brutal-btn !py-1 !px-3 !text-[12px]' : ''}`
                    : `text-[var(--text-muted)] hover:text-[var(--text)] ${isClay ? 'hover:clay-card !py-1.5' : isLiquid ? 'hover:bg-[var(--glass-bg)] hover:backdrop-blur-xl' : 'hover:bg-[var(--bg-secondary)]'}`
                } ${isClay && active ? '!rounded-full' : ''}`}
              >
                <item.icon size={14} className="transition-transform duration-200 group-hover:scale-110" />
                <span>{item.label}</span>
                {item.dot && !active && <span className="w-1 h-1 rounded-full bg-[var(--accent)] ml-1 animate-pulse shadow-[var(--glow)]" />}
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
                  className={`p-2 rounded-full transition-all duration-200 gpu-accelerated navbar-link ${active ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-secondary)]'} ${isClay ? 'clay-card !p-2 !rounded-full' : isBrutal ? 'brutal-card !p-1.5 !rounded-sm' : ''}`}
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
              className={`hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border text-[12px] font-medium gpu-accelerated transition-all duration-200 hover:scale-[1.02] bg-[var(--card)] border-[var(--border)] text-[var(--text-sec)] hover:border-[var(--border-strong)] ${isClay ? 'clay-pill' : isLiquid ? 'liquid-glass !py-1.5' : isBrutal ? 'brutal-card !py-1 !rounded-sm' : ''}`}
            >
              <span className="text-[14px]">{currentTheme.icon}</span>
              <span className="hidden xl:inline">{currentTheme.name}</span>
              <Palette size={10} className="text-[var(--accent)]" />
              <ChevronDown size={12} className={`transition-transform duration-200 ${themeOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {themeOpen && (
              <div className={`absolute top-full right-0 mt-2 w-[360px] rounded-xl border shadow-[var(--shadow-lg)] z-50 overflow-hidden animate-scaleIn gpu-accelerated max-h-[75vh] flex flex-col ${isLiquid ? 'liquid-glass-card !p-0' : isClay ? 'clay-card !p-0 !rounded-2xl' : isBrutal ? 'brutal-card !p-0 !rounded-sm' : 'bg-[var(--card)] border-[var(--border)]'}`}>
                <div className={`p-3 border-b bg-[var(--bg-secondary)] ${isClay ? '!rounded-t-2xl' : ''}`}>
                  <div className="font-medium text-[12px] text-[var(--text)] flex items-center justify-between">
                    <span className="flex items-center gap-1.5"><Palette size={12} className="text-[var(--accent)]" /> Themes • {Object.keys(THEMES).length} + Styles</span>
                    <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-sm">{currentTheme.category}</span>
                  </div>
                  <div className="mt-3">
                    <div className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)] mb-1.5">Visual Style</div>
                    <div className="grid grid-cols-3 gap-1.5">
                      {Object.values(VISUAL_STYLES).map(v => (
                        <button
                          key={v.id}
                          onClick={() => updateVisualStyle(v.id)}
                          className={`p-2 rounded-lg border text-center transition-all duration-200 hover:scale-[1.02] ${visualStyle === v.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] text-[var(--text-sec)]'}`}
                        >
                          <div className="text-[14px]">{v.icon}</div>
                          <div className="text-[10px] font-medium mt-1">{v.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-1 mt-3 p-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">
                    {THEME_CATEGORIES.map(cat => (
                      <button
                        key={cat}
                        onClick={() => setThemeCategory(cat)}
                        className={`px-2.5 py-1 rounded-full text-[10px] font-medium transition-all ${themeCategory === cat ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text)]'}`}
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
                      onClick={() => { updateTheme(t.id); }}
                      className={`w-full text-left p-2.5 rounded-lg flex items-center gap-2.5 transition-all duration-200 hover:scale-[1.01] gpu-accelerated border ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-secondary)] text-[var(--text-sec)]'} ${isClay ? '!rounded-xl' : isBrutal ? '!rounded-sm' : ''}`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[16px] border ${theme === t.id ? 'bg-white/20 border-white/20' : 'bg-[var(--bg-secondary)] border-[var(--border)]'} ${isClay ? '!rounded-xl' : ''}`}>
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

          <div className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-muted)] ${isClay ? 'clay-pill' : isBrutal ? 'brutal-card !py-0.5 !rounded-sm !px-2' : ''}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-[var(--buy)] animate-pulse shadow-[0_0_8px_var(--buy)]' : 'bg-[var(--text-faint)]'}`} />
            <span className="hidden xl:inline">{isLive ? 'Live' : 'Offline'}</span>
          </div>

          <Link to="/trading" className={`hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-200 hover:scale-[1.02] gpu-accelerated bg-[var(--accent)] text-white shadow-[var(--glow)] hover:shadow-[var(--shadow-md)] ${isClay ? 'clay-btn !bg-[var(--accent)] !text-white' : isBrutal ? 'brutal-btn !py-1 !px-3 !text-[11px]' : ''}`}>
            <Target size={12} />
            <span>Trade</span>
          </Link>

          <button 
            onClick={() => setMobileOpen(!mobileOpen)} 
            className={`lg:hidden w-9 h-9 rounded-full flex items-center justify-center border transition-all duration-200 gpu-accelerated bg-[var(--card)] border-[var(--border)] text-[var(--text-muted)] ${mobileOpen ? 'rotate-90 bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : ''} ${isClay ? 'clay-card !w-10 !h-10 !rounded-2xl' : isBrutal ? 'brutal-card !w-9 !h-9 !rounded-sm' : ''}`}
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className={`lg:hidden border-t backdrop-blur-xl animate-slideIn gpu-accelerated max-h-[80vh] overflow-y-auto no-scrollbar ${isLiquid ? 'liquid-glass !border-t-0 !rounded-none' : isClay ? 'clay-card !rounded-none !border-x-0 !border-b-0' : isBrutal ? 'brutal-card !rounded-none !border-x-0 !border-t-0 !border-b-[3px]' : 'bg-[var(--card)]/95 border-[var(--border)]'}`}>
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
                  } ${isClay ? '!rounded-2xl' : isBrutal ? '!rounded-sm' : ''}`}
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
          <div className="p-3 border-t border-[var(--border)]">
            <div className="text-[11px] font-medium text-[var(--text-muted)] mb-2 flex items-center gap-1"><Palette size={10} /> Visual Styles</div>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {Object.values(VISUAL_STYLES).map(v => (
                <button
                  key={v.id}
                  onClick={() => updateVisualStyle(v.id)}
                  className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${visualStyle === v.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] text-[var(--text-sec)]'}`}
                >
                  <span className="text-[16px]">{v.icon}</span>
                  <span className="text-[9px] font-medium">{v.name}</span>
                </button>
              ))}
            </div>
            <div className="text-[11px] font-medium text-[var(--text-muted)] mb-2">Themes</div>
            <div className="grid grid-cols-4 gap-2">
              {Object.values(THEMES).map(t => (
                <button
                  key={t.id}
                  onClick={() => { updateTheme(t.id); }}
                  className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] text-[var(--text-sec)]'} ${isClay ? '!rounded-xl' : isBrutal ? '!rounded-sm' : ''}`}
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
