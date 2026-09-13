import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, Brain, Radio, BarChart3, Home, Sparkles, Activity, Zap, Menu, X, Target, Settings, GraduationCap, Wallet, Bot, Search, LineChart, Bell, BookOpen, Cpu, Sun, Moon } from 'lucide-react'
import { useState } from 'react'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()
  const { theme, toggleTheme } = useSettingsStore()

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home, desc: 'Overview & live market' },
    { path: '/trading', label: 'Real Trading', icon: Target, desc: 'Live calls for actual trades', badge: 'REAL', highlight: true },
    { path: '/autotrade', label: 'Auto Trade', icon: Cpu, desc: 'Automated real trading', badge: 'NEW', highlight: true, accent: 'emerald' },
    { path: '/portfolio', label: 'Portfolio', icon: Wallet, desc: 'Real holdings & P&L', badge: 'NEW', highlight: true, accent: 'emerald' },
    { path: '/strategies', label: 'Bots', icon: Bot, desc: 'DCA, Grid, Breakout', badge: 'NEW', highlight: true, accent: 'violet' },
    { path: '/scanner', label: 'Scanner', icon: Search, desc: 'Market opportunities', badge: 'LIVE' },
    { path: '/analytics', label: 'Analytics', icon: LineChart, desc: 'Performance & equity' },
    { path: '/alerts', label: 'Alerts', icon: Bell, desc: 'Price & signal alerts' },
    { path: '/journal', label: 'Journal', icon: BookOpen, desc: 'Trading journal' },
    { path: '/training', label: 'Training', icon: GraduationCap, desc: 'Endless self-learning', badge: 'LIVE', accent: 'violet' },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp, desc: 'AI predictions' },
    { path: '/realtime', label: 'Live', icon: Radio, desc: 'Real-time Binance', badge: 'LIVE' },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles, desc: 'News & social' },
    { path: '/backtest', label: 'Validate', icon: BarChart3, desc: 'Model validation' },
    { path: '/models', label: 'Models', icon: Brain, desc: 'Model zoo' },
    { path: '/settings', label: 'Settings', icon: Settings, desc: 'Config & risk' },
  ]

  const isDark = theme === 'dark'

  return (
    <nav className={`sticky top-0 z-50 backdrop-blur-2xl transition-all duration-500 ${
      isDark 
        ? 'bg-[#000000] border-b border-white/10' 
        : 'bg-white/70 backdrop-blur-xl border-b border-white/40 shadow-[0px_8px_32px_rgba(31,38,135,0.06)]'
    }`}>
      {/* Claymorphism subtle gradient overlay for dark */}
      {isDark && (
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-violet-500/5 pointer-events-none"></div>
      )}
      {isDark === false && (
        <div className="absolute inset-0 bg-gradient-to-r from-[#FFCFDF]/10 via-transparent to-[#BBE1FA]/20 pointer-events-none"></div>
      )}
      
      <div className="relative max-w-[1600px] mx-auto px-6 py-3.5 flex items-center justify-between">
        {/* Logo - Claymorphic */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-12 h-12 rounded-[20px] bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center font-black text-black text-xl transition-all duration-300 group-hover:scale-105 clay-float"
              style={isDark ? {
                boxShadow: '0px 12px 24px rgba(0,0,0,0.5), inset 4px 4px 8px rgba(255,255,255,0.2), inset -4px -4px 8px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.08)'
              } : {
                boxShadow: '0px 12px 24px rgba(31,38,135,0.08), inset 4px 4px 8px rgba(255,255,255,0.9), inset -4px -4px 8px rgba(0,0,0,0.1)',
                border: '1px solid rgba(255,255,255,0.4)'
              }}>
              ₿
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-2 flex items-center justify-center"
              style={{ 
                borderColor: isDark ? '#000000' : '#ffffff',
                boxShadow: isDark 
                  ? 'inset 1px 1px 2px rgba(255,255,255,0.3), inset -1px -1px 2px rgba(0,0,0,0.2)'
                  : '0px 4px 8px rgba(31,38,135,0.1), inset 1px 1px 2px rgba(255,255,255,0.9)'
              }}>
              <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
            </div>
          </div>
          <div className="hidden sm:block">
            <div className="font-bold text-[18px] tracking-tight leading-none flex items-center gap-2 font-poppins">
              <span className={isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}>CryptoPred</span>
              <span className="px-3 py-1 rounded-full text-[10px] font-black tracking-widest clay-pill"
                style={isDark ? {
                  background: 'rgba(28,28,30,0.7)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#10b981'
                } : {
                  background: '#ffffff',
                  border: '1px solid rgba(255,255,255,0.4)',
                  color: '#059669'
                }}>
                V7 • CLAY • COINDCX REAL
              </span>
            </div>
            <div className="text-[11px] font-medium tracking-wide mt-1 flex items-center gap-2 font-poppins"
              style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
              <span>CLAYMORPHISM • PUFFY 3D • REAL INR</span>
              {isLive && (
                <span className="flex items-center gap-1 text-emerald-500">
                  <span className="live-dot !w-1.5 !h-1.5"></span> LIVE
                </span>
              )}
            </div>
          </div>
        </Link>

        {/* Desktop Nav - Clay Pills */}
        <div className={`hidden lg:flex items-center gap-1 p-2 rounded-[24px] backdrop-blur transition-all duration-500 ${
          isDark
            ? 'bg-[#000000] border border-white/10'
            : 'bg-white/60 border border-white/40 shadow-[0px_8px_24px_rgba(31,38,135,0.06)]'
        }`}>
          {nav.slice(0, 8).map(item => {
            const active = loc.pathname === item.path
            return (
              <Link 
                key={item.path} 
                to={item.path} 
                className={`relative flex items-center gap-2 px-4 py-2.5 rounded-[20px] text-[13px] font-semibold transition-all duration-300 group font-poppins ${
                  active 
                    ? isDark
                      ? 'bg-white text-black shadow-[0px_8px_16px_rgba(0,0,0,0.3),inset_3px_3px_6px_rgba(255,255,255,0.9),inset_-3px_-3px_6px_rgba(0,0,0,0.1)] scale-[1.02]'
                      : 'bg-white text-black shadow-[0px_8px_16px_rgba(31,38,135,0.08),inset_3px_3px_6px_rgba(255,255,255,0.9),inset_-3px_-3px_6px_rgba(0,0,0,0.08)] scale-[1.02]'
                    : isDark
                      ? item.highlight
                        ? 'text-emerald-400 hover:text-white hover:bg-white/5 border border-white/5 hover:border-white/10'
                        : 'text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/5'
                      : item.highlight
                        ? 'text-emerald-700 hover:text-emerald-800 bg-emerald-50/50 hover:bg-emerald-100/50 border border-emerald-200/30'
                        : 'text-[#64748b] hover:text-[#1e293b] hover:bg-white/80'
                }`}
              >
                <item.icon size={14} />
                <span className="hidden xl:inline">{item.label}</span>
                {item.badge && (
                  <span className={`text-[8px] font-black px-2 py-0.5 rounded-full tracking-widest clay-pill ${
                    active ? 'bg-black text-emerald-400' : 
                    item.accent === 'violet' ? 'bg-violet-500 text-white' :
                    'bg-emerald-500 text-black'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Right - Theme Toggle Clay + Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle - Claymorphic */}
          <button
            onClick={toggleTheme}
            className={`w-12 h-12 rounded-[20px] flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 clay-float`}
            style={isDark ? {
              background: 'rgba(28,28,30,0.7)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0px 12px 24px rgba(0,0,0,0.5), inset 3px 3px 6px rgba(255,255,255,0.12), inset -3px -3px 6px rgba(0,0,0,0.5)',
              color: '#F3F4F6'
            } : {
              background: '#ffffff',
              border: '1px solid rgba(255,255,255,0.4)',
              boxShadow: '0px 12px 24px rgba(31,38,135,0.08), inset 4px 4px 8px rgba(255,255,255,0.9), inset -4px -4px 8px rgba(0,0,0,0.08)',
              color: '#1e293b'
            }}
            title={`Switch to ${isDark ? 'light' : 'true dark'} mode`}
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          <div className={`hidden md:flex items-center gap-2 px-4 py-2.5 rounded-[20px] backdrop-blur ${
            isDark
              ? 'bg-[#000000] border border-white/10'
              : 'bg-white/60 border border-white/40 shadow-[0px_4px_12px_rgba(31,38,135,0.05)]'
          }`}>
            <Activity size={14} className="text-emerald-500" />
            <span className="text-xs font-semibold font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
              {lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : 'Syncing...'}
            </span>
          </div>

          <Link to="/trading" className={`hidden md:flex items-center gap-2 px-4 py-2.5 rounded-[20px] font-bold text-xs font-poppins transition-all hover:scale-105 active:scale-95 ${
            isDark
              ? 'bg-gradient-to-r from-emerald-500 to-green-600 text-black shadow-[0px_8px_16px_rgba(0,0,0,0.3),inset_2px_2px_4px_rgba(255,255,255,0.2)]'
              : 'bg-gradient-to-r from-emerald-500 to-green-600 text-black shadow-[0px_8px_16px_rgba(0,211,149,0.15),inset_2px_2px_4px_rgba(255,255,255,0.3)]'
          }`}>
            <Target size={14} />
            <span>REAL TRADING</span>
          </Link>

          {/* Mobile */}
          <button 
            onClick={() => setMobileOpen(!mobileOpen)}
            className={`lg:hidden w-12 h-12 rounded-[20px] flex items-center justify-center transition-all active:scale-95`}
            style={isDark ? {
              background: 'rgba(28,28,30,0.7)',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0px 8px 16px rgba(0,0,0,0.4), inset 2px 2px 4px rgba(255,255,255,0.08)',
              color: '#9CA3AF'
            } : {
              background: '#ffffff',
              border: '1px solid rgba(255,255,255,0.4)',
              boxShadow: '0px 8px 16px rgba(31,38,135,0.06), inset 3px 3px 6px rgba(255,255,255,0.9)',
              color: '#64748b'
            }}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu - Claymorphic Grid */}
      {mobileOpen && (
        <div className={`lg:hidden border-t backdrop-blur-2xl max-h-[80vh] overflow-auto transition-colors duration-500 ${
          isDark ? 'bg-[#000000] border-white/10' : 'bg-white/80 border-white/40'
        }`}>
          <div className="p-4 grid grid-cols-2 gap-3">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`p-5 rounded-[24px] transition-all duration-300 font-poppins ${
                    active 
                      ? isDark
                        ? 'bg-white text-black shadow-[0px_12px_24px_rgba(0,0,0,0.3),inset_4px_4px_8px_rgba(255,255,255,0.9),inset_-4px_-4px_8px_rgba(0,0,0,0.1)]'
                        : 'bg-white text-black shadow-[0px_12px_24px_rgba(31,38,135,0.08),inset_4px_4px_8px_rgba(255,255,255,0.9),inset_-4px_-4px_8px_rgba(0,0,0,0.08)]'
                      : isDark
                        ? item.highlight 
                          ? 'bg-white/5 border border-white/10 text-emerald-400 hover:bg-white/10 hover:border-white/20'
                          : 'bg-[#000000] border border-white/10 text-[#9CA3AF] hover:text-[#F3F4F6] hover:border-white/20'
                        : 'bg-white/70 border border-white/40 text-[#64748b] hover:text-[#1e293b] shadow-[0px_4px_12px_rgba(31,38,135,0.04)]'
                  }`}
                >
                  <item.icon size={20} className="mb-3" />
                  <div className="font-bold text-sm flex items-center gap-2">
                    {item.label}
                    {item.badge && <span className={`text-[9px] px-2 py-0.5 rounded-full font-black clay-pill ${item.accent === 'violet' ? 'bg-violet-500 text-white' : 'bg-emerald-500 text-black'}`}>{item.badge}</span>}
                  </div>
                  <div className="text-xs opacity-70 mt-1">{item.desc}</div>
                </Link>
              )
            })}
          </div>
          
          {/* Mobile theme toggle */}
          <div className="p-4 border-t border-white/10">
            <button
              onClick={toggleTheme}
              className={`w-full p-4 rounded-[24px] flex items-center justify-between font-bold font-poppins transition-all`}
              style={isDark ? {
                background: 'rgba(28,28,30,0.7)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: '#F3F4F6'
              } : {
                background: '#ffffff',
                border: '1px solid rgba(255,255,255,0.4)',
                color: '#1e293b',
                boxShadow: '0px 8px 16px rgba(31,38,135,0.06)'
              }}
            >
              <span className="flex items-center gap-3">
                {isDark ? <Moon size={18} /> : <Sun size={18} />}
                {isDark ? 'True Dark Mode • #000000' : 'Light Mode • Pastel Gradient'}
              </span>
              <span className="clay-pill text-xs">
                {isDark ? '→ Light' : '→ Dark'}
              </span>
            </button>
          </div>
        </div>
      )}
    </nav>
  )
}
