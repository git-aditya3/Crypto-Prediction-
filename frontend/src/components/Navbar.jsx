import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, Brain, Radio, BarChart3, Home, Sparkles, Activity, Zap, Menu, X, Target, Settings, GraduationCap } from 'lucide-react'
import { useState } from 'react'
import { useMarketStore } from '../store/useMarketStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home, desc: 'Overview & live market' },
    { path: '/trading', label: 'Real Trading', icon: Target, desc: 'Live calls for actual trades', badge: 'REAL', highlight: true },
    { path: '/training', label: 'Training', icon: GraduationCap, desc: 'Endless self-learning', badge: 'LIVE', highlight: true, accent: 'violet' },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp, desc: 'AI predictions' },
    { path: '/realtime', label: 'Live', icon: Radio, desc: 'Real-time Binance', badge: 'LIVE' },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles, desc: 'News & social' },
    { path: '/backtest', label: 'Validate', icon: BarChart3, desc: 'Model validation' },
    { path: '/models', label: 'Models', icon: Brain, desc: 'Model zoo' },
    { path: '/settings', label: 'Settings', icon: Settings, desc: 'Config & risk' },
  ]

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-2xl bg-crypto-bg/70 border-b border-crypto-border/50">
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-violet-500/5 pointer-events-none"></div>
      
      <div className="relative max-w-[1600px] mx-auto px-6 py-3.5 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center font-black text-black text-lg shadow-lg shadow-emerald-500/20 group-hover:shadow-emerald-500/30 transition-all duration-300 group-hover:scale-105">
              ₿
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-crypto-bg flex items-center justify-center">
              <div className="w-1 h-1 bg-white rounded-full animate-pulse"></div>
            </div>
          </div>
          <div className="hidden sm:block">
            <div className="font-bold text-[17px] tracking-tight leading-none flex items-center gap-2">
              CryptoPred
              <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-emerald-500/20 to-violet-500/20 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold tracking-widest">V4 • REAL TRADING</span>
            </div>
            <div className="text-[11px] text-crypto-muted font-medium tracking-wide mt-0.5 flex items-center gap-2">
              <span>REAL TRADES • ENDLESS LEARNING • LIVE DATA</span>
              {isLive && (
                <span className="flex items-center gap-1 text-emerald-400">
                  <span className="live-dot !w-1.5 !h-1.5"></span> LIVE
                </span>
              )}
            </div>
          </div>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-1 p-1 rounded-2xl bg-crypto-card/50 border border-crypto-border/50 backdrop-blur">
          {nav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link 
                key={item.path} 
                to={item.path} 
                className={`relative flex items-center gap-2 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-300 group ${
                  active 
                    ? 'bg-white text-black shadow-lg shadow-white/10' 
                    : item.highlight
                      ? item.accent === 'violet'
                        ? 'text-violet-400 hover:text-white hover:bg-violet-500/10 border border-violet-500/20'
                        : 'text-emerald-400 hover:text-white hover:bg-emerald-500/10 border border-emerald-500/20'
                      : 'text-crypto-muted hover:text-white hover:bg-crypto-cardHover'
                }`}
              >
                <item.icon size={14} className={`${active ? 'text-black' : item.highlight ? (item.accent === 'violet' ? 'text-violet-400 group-hover:text-white' : 'text-emerald-400 group-hover:text-white') : 'group-hover:text-white'} transition-colors`} />
                <span className="hidden xl:inline">{item.label}</span>
                {item.badge && (
                  <span className={`text-[8px] font-black px-1.5 py-0.5 rounded-full tracking-widest ${
                    active ? 'bg-black text-emerald-400' : 
                    item.accent === 'violet' ? 'bg-violet-500 text-white' :
                    item.highlight ? 'bg-emerald-500 text-black' :
                    'bg-crypto-accent text-black'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-xl bg-crypto-card border border-crypto-border/50">
            <Activity size={14} className="text-emerald-400" />
            <span className="text-xs font-medium text-crypto-muted">
              {lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : 'Syncing real data...'}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-2">
            <Link to="/trading" className="px-3 py-2 rounded-xl bg-gradient-to-r from-emerald-500/10 to-violet-500/10 border border-emerald-500/20 hover:border-emerald-500/40 transition">
              <div className="flex items-center gap-2 text-xs">
                <Target size={12} className="text-emerald-400" />
                <span className="font-semibold text-emerald-400">REAL TRADING • No Simulation</span>
              </div>
            </Link>
          </div>

          {/* Mobile */}
          <button 
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden w-10 h-10 rounded-xl bg-crypto-card border border-crypto-border flex items-center justify-center text-crypto-muted hover:text-white transition"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-crypto-border/50 bg-crypto-card/90 backdrop-blur-2xl">
          <div className="p-4 grid grid-cols-2 gap-2">
            {nav.map(item => {
              const active = loc.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`p-4 rounded-xl border transition ${
                    active ? 'bg-white text-black border-white' : 
                    item.highlight ? (item.accent === 'violet' ? 'bg-violet-500/10 border-violet-500/20 text-violet-400 hover:bg-violet-500/20' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20') :
                    'bg-crypto-bg border-crypto-border text-crypto-muted hover:text-white hover:border-crypto-borderLight'
                  }`}
                >
                  <item.icon size={18} className="mb-2" />
                  <div className="font-semibold text-sm flex items-center gap-2">
                    {item.label}
                    {item.badge && <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-black ${item.accent === 'violet' ? 'bg-violet-500 text-white' : 'bg-emerald-500 text-black'}`}>{item.badge}</span>}
                  </div>
                  <div className="text-xs opacity-70 mt-1">{item.desc}</div>
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}
