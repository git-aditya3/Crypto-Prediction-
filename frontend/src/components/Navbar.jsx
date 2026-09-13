import { Link, useLocation } from 'react-router-dom'
import { Home, Target, Cpu, Wallet, Bot, Search, LineChart, Bell, BookOpen, GraduationCap, TrendingUp, Radio, Sparkles, BarChart3, Brain, Settings, Menu, X, AlertTriangle, ChevronDown, Palette } from 'lucide-react'
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

  return (
    <nav className="sticky top-0 z-50 gpu-accelerated" style={{ 
      transform: 'translateZ(0)',
      background: 'var(--glass-bg-strong)',
      backdropFilter: 'blur(60px) saturate(200%)',
      WebkitBackdropFilter: 'blur(60px) saturate(200%)',
      borderBottom: '0.5px solid var(--separator)',
      boxShadow: '0 1px 0 0 var(--glass-border), 0 8px 32px rgba(0,0,0,0.08)'
    }}>
      {/* iOS 26 Liquid Glass highlight edge */}
      <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-[var(--glass-border-strong)] to-transparent opacity-60 pointer-events-none" />
      
      <div className="max-w-[1600px] mx-auto px-4 md:px-5 h-[60px] flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group gpu-accelerated">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-[14px] bg-[var(--accent)] text-white shadow-[var(--glow)] transition-transform duration-200 ease-out group-hover:scale-110 group-hover:rotate-3" style={{ borderRadius: '12px', fontFamily: "-apple-system, 'SF Pro Display', sans-serif" }}>
            ₿
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[15px] tracking-tight text-[var(--text)]" style={{ letterSpacing: '-0.23px', fontFamily: "-apple-system, 'SF Pro Display', sans-serif" }}>CryptoPred</span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-[var(--accent)] text-white shadow-[var(--glow)] tracking-wide">iOS 26</span>
              <span className="hidden lg:inline-flex px-2.5 py-1 rounded-full text-[10px] font-medium bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] text-[var(--text-sec)]" style={{ letterSpacing: '-0.08px' }}>{currentVisual.icon} {currentVisual.name}</span>
            </div>
          </div>
        </Link>

        <div className="hidden lg:flex items-center gap-1 p-1 rounded-full" style={{ background: 'var(--bg-secondary)', border: '0.5px solid var(--separator)', boxShadow: 'inset 0 0 0 0.5px var(--separator)' }}>
          {primaryNav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center gap-1.5 px-3.5 py-2 rounded-full text-[13px] font-medium gpu-accelerated navbar-link transition-all duration-200 ${
                  active
                    ? 'bg-[var(--accent)] text-white shadow-[var(--glow)] font-semibold'
                    : 'text-[var(--text-sec)] hover:text-[var(--text)] hover:bg-[var(--glass-bg)]'
                }`}
                style={{ minHeight: '32px', letterSpacing: '-0.08px', fontFamily: "-apple-system, 'SF Pro Text', sans-serif" }}
              >
                <item.icon size={14} className="transition-transform duration-200 group-hover:scale-110" />
                <span>{item.label}</span>
                {item.dot && !active && <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] ml-1 animate-pulse shadow-[var(--glow)]" />}
              </Link>
            )
          })}
          
          <div className="w-px h-4 mx-1 bg-[var(--separator)]" />
          
          <div className="flex items-center gap-0.5">
            {secondaryNav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link 
                  key={item.path} 
                  to={item.path} 
                  className={`p-2 rounded-full transition-all duration-200 gpu-accelerated navbar-link ${active ? 'bg-[var(--accent)] text-white shadow-[var(--glow)]' : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--glass-bg)]'}`}
                  title={item.label}
                  style={{ minWidth: '32px', minHeight: '32px' }}
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
              className="hidden md:flex items-center gap-1.5 px-3 py-2 rounded-full border text-[13px] font-medium gpu-accelerated transition-all duration-200 hover:scale-[1.02]"
              style={{ 
                background: 'var(--glass-bg)', 
                backdropFilter: 'blur(20px) saturate(180%)',
                WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                border: '0.5px solid var(--glass-border)',
                color: 'var(--text-sec)',
                minHeight: '36px',
                letterSpacing: '-0.08px',
                boxShadow: 'var(--shadow-sm)'
              }}
            >
              <span className="text-[14px]">{currentTheme.icon}</span>
              <span className="hidden xl:inline font-medium">{currentTheme.name}</span>
              <Palette size={12} className="text-[var(--accent)]" />
              <ChevronDown size={12} className={`transition-transform duration-200 ${themeOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {themeOpen && (
              <div className="absolute top-full right-0 mt-2 w-[380px] rounded-[20px] border shadow-[var(--shadow-lg)] z-50 overflow-hidden animate-scaleIn gpu-accelerated max-h-[75vh] flex flex-col" style={{
                background: 'var(--glass-bg-strong)',
                backdropFilter: 'blur(60px) saturate(200%)',
                WebkitBackdropFilter: 'blur(60px) saturate(200%)',
                border: '0.5px solid var(--glass-border-strong)',
                boxShadow: 'var(--shadow-lg), var(--glass-highlight)'
              }}>
                <div className="p-4 border-b" style={{ background: 'var(--bg-secondary)', borderBottom: '0.5px solid var(--separator)' }}>
                  <div className="font-semibold text-[13px] text-[var(--text)] flex items-center justify-between" style={{ letterSpacing: '-0.08px' }}>
                    <span className="flex items-center gap-1.5"><Palette size={14} className="text-[var(--accent)]" /> iOS 26 Themes • {Object.keys(THEMES).length} Liquid Glass</span>
                    <span className="px-2.5 py-1 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-[var(--glow)]">{currentTheme.category}</span>
                  </div>
                  <div className="mt-4">
                    <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)] mb-2" style={{ letterSpacing: '0.06em' }}>Visual Style • iOS 26 Material</div>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.values(VISUAL_STYLES).map(v => (
                        <button
                          key={v.id}
                          onClick={() => updateVisualStyle(v.id)}
                          className={`p-2.5 rounded-[12px] border text-center transition-all duration-200 hover:scale-[1.02] ${visualStyle === v.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--glass-border-strong)] text-[var(--text-sec)] backdrop-blur-xl'}`}
                          style={{ minHeight: '60px' }}
                        >
                          <div className="text-[16px]">{v.icon}</div>
                          <div className="text-[11px] font-semibold mt-1" style={{ letterSpacing: '-0.08px' }}>{v.name}</div>
                          <div className="text-[9px] opacity-70 mt-0.5">{v.id === 'liquid' ? '40px blur' : v.id === 'clay' ? '60px blur' : 'Liquid'}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-1 mt-4 p-1 rounded-full" style={{ background: 'var(--bg-tertiary)', border: '0.5px solid var(--separator)' }}>
                    {THEME_CATEGORIES.map(cat => (
                      <button
                        key={cat}
                        onClick={() => setThemeCategory(cat)}
                        className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all ${themeCategory === cat ? 'bg-[var(--accent)] text-white shadow-sm font-semibold' : 'text-[var(--text-muted)] hover:text-[var(--text)]'}`}
                        style={{ letterSpacing: '-0.08px' }}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="p-2 grid grid-cols-1 gap-1.5 overflow-y-auto no-scrollbar flex-1">
                  {filteredThemes.map(t => (
                    <button
                      key={t.id}
                      onClick={() => { updateTheme(t.id); }}
                      className={`w-full text-left p-3 rounded-[12px] flex items-center gap-3 transition-all duration-200 hover:scale-[1.01] gpu-accelerated border ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--glass-border-strong)] hover:bg-[var(--glass-bg-strong)] text-[var(--text-sec)] backdrop-blur-xl'}`}
                    >
                      <div className={`w-9 h-9 rounded-[10px] flex items-center justify-center text-[18px] border ${theme === t.id ? 'bg-white/20 border-white/20' : 'bg-[var(--bg-secondary)] border-[var(--separator)]'}`}>
                        {t.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-[13px] flex items-center gap-1.5" style={{ letterSpacing: '-0.08px' }}>
                          {t.name}
                          {theme === t.id && <span className="w-1 h-1 rounded-full bg-white animate-pulse" />}
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] ml-1">iOS 26</span>
                        </div>
                        <div className={`text-[11px] truncate ${theme === t.id ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{t.desc} • {t.ios?.accent || t.category}</div>
                      </div>
                      <div className="flex gap-1">
                        {Object.values(t.colors).slice(0, 3).map((c, i) => (
                          <div key={i} className="w-3.5 h-3.5 rounded-full border border-white/20 shadow-sm" style={{ background: c }} />
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
                <div className="p-3 border-t text-[10px] text-[var(--text-muted)]" style={{ borderTop: '0.5px solid var(--separator)', background: 'var(--bg-secondary)' }}>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-[var(--accent)] animate-pulse" />
                    iOS 26 Liquid Glass • blur 40px saturate 180% • continuous corners • SF Pro • 44pt tap target
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[11px] font-medium" style={{ 
            background: 'var(--glass-bg)', 
            backdropFilter: 'blur(20px) saturate(180%)',
            border: '0.5px solid var(--glass-border)',
            color: 'var(--text-muted)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-[var(--buy)] animate-pulse shadow-[0_0_8px_var(--buy)]' : 'bg-[var(--text-faint)]'}`} />
            <span className="hidden xl:inline font-medium" style={{ letterSpacing: '-0.08px' }}>{isLive ? 'Live' : 'Offline'} • iOS 26</span>
          </div>

          <Link to="/trading" className="hidden md:flex items-center gap-1.5 px-4 py-2 rounded-full text-[13px] font-semibold transition-all duration-200 hover:scale-[1.02] gpu-accelerated" style={{
            background: 'var(--accent)',
            color: 'white',
            boxShadow: 'var(--glow), var(--shadow-sm)',
            minHeight: '36px',
            letterSpacing: '-0.08px',
            fontFamily: "-apple-system, 'SF Pro Text', sans-serif"
          }}>
            <Target size={14} />
            <span>Trade</span>
          </Link>

          <button 
            onClick={() => setMobileOpen(!mobileOpen)} 
            className={`lg:hidden w-9 h-9 rounded-full flex items-center justify-center border transition-all duration-200 gpu-accelerated ${mobileOpen ? 'rotate-90 bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--glass-bg)] border-[var(--glass-border)] text-[var(--text-muted)] backdrop-blur-xl'}`}
            style={{ minWidth: '44px', minHeight: '44px' }}
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t backdrop-blur-[60px] animate-slideIn gpu-accelerated max-h-[80vh] overflow-y-auto no-scrollbar" style={{
          background: 'var(--glass-bg-strong)',
          borderTop: '0.5px solid var(--separator)',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <div className="p-3 grid grid-cols-2 gap-2">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`p-3 rounded-[12px] flex items-center gap-2.5 text-[13px] font-medium transition-all duration-200 gpu-accelerated border ${
                    active 
                      ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)] font-semibold' 
                      : 'bg-[var(--glass-bg)] border-[var(--glass-border)] text-[var(--text-sec)] hover:bg-[var(--glass-bg-strong)] backdrop-blur-xl'
                  }`}
                  style={{ minHeight: '44px', letterSpacing: '-0.08px' }}
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
          <div className="p-4 border-t" style={{ borderTop: '0.5px solid var(--separator)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)] mb-2 flex items-center gap-1" style={{ letterSpacing: '0.06em' }}><Palette size={12} /> iOS 26 Visual Materials</div>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {Object.values(VISUAL_STYLES).map(v => (
                <button
                  key={v.id}
                  onClick={() => updateVisualStyle(v.id)}
                  className={`p-3 rounded-[12px] border flex flex-col items-center gap-1 transition-all ${visualStyle === v.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--glass-bg)] border-[var(--glass-border)] text-[var(--text-sec)] backdrop-blur-xl'}`}
                  style={{ minHeight: '60px' }}
                >
                  <span className="text-[18px]">{v.icon}</span>
                  <span className="text-[10px] font-semibold">{v.name}</span>
                </button>
              ))}
            </div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)] mb-2" style={{ letterSpacing: '0.06em' }}>iOS 26 Themes • Liquid Glass</div>
            <div className="grid grid-cols-3 gap-2">
              {Object.values(THEMES).map(t => (
                <button
                  key={t.id}
                  onClick={() => { updateTheme(t.id); }}
                  className={`p-3 rounded-[12px] border flex flex-col items-center gap-1.5 transition-all ${theme === t.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--glass-bg)] border-[var(--glass-border)] text-[var(--text-sec)] backdrop-blur-xl'}`}
                >
                  <span className="text-[20px]">{t.icon}</span>
                  <span className="text-[10px] font-semibold">{t.name}</span>
                  <span className="text-[8px] opacity-60">{t.ios?.accent?.split(' ')[0] || 'iOS 26'}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
