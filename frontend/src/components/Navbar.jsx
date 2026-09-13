import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, Brain, Radio, BarChart3, Home, Sparkles, Activity, Zap, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { useMarketStore } from '../store/useMarketStore'

export default function Navbar() {
  const loc = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isLive, lastUpdate } = useMarketStore()

  const nav = [
    { path: '/', label: 'Dashboard', icon: Home, desc: 'Overview & live market' },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp, desc: 'AI predictions' },
    { path: '/realtime', label: 'Live Trading', icon: Radio, desc: 'Real-time feed', badge: 'LIVE' },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles, desc: 'News & social' },
    { path: '/backtest', label: 'Backtest', icon: BarChart3, desc: 'Strategy test' },
    { path: '/models', label: 'Models', icon: Brain, desc: 'Model zoo' },
  ]

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-2xl bg-crypto-bg/70 border-b border-crypto-border/50">
      <div className="absolute inset-0 bg-gradient-to-r from-crypto-accent/5 via-transparent to-crypto-accent2/5 pointer-events-none"></div>
      
      <div className="relative max-w-[1600px] mx-auto px-6 py-3.5 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-crypto-accent to-crypto-accent3 flex items-center justify-center font-black text-black text-lg shadow-lg shadow-crypto-accent/20 group-hover:shadow-crypto-accent/30 transition-all duration-300 group-hover:scale-105">
              ₿
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-crypto-accent2 rounded-full border-2 border-crypto-bg flex items-center justify-center">
              <div className="w-1 h-1 bg-white rounded-full animate-pulse"></div>
            </div>
          </div>
          <div className="hidden sm:block">
            <div className="font-bold text-[17px] tracking-tight leading-none flex items-center gap-2">
              CryptoPred
              <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-crypto-accent/20 to-crypto-accent3/20 border border-crypto-accent/20 text-crypto-accent text-[10px] font-bold tracking-widest">V2 • PRO</span>
            </div>
            <div className="text-[11px] text-crypto-muted font-medium tracking-wide mt-0.5 flex items-center gap-2">
              <span>AI • REAL-TIME • SENTIMENT</span>
              {isLive && (
                <span className="flex items-center gap-1 text-crypto-accent">
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
                className={`relative flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-300 group ${
                  active 
                    ? 'bg-white text-black shadow-lg shadow-white/10' 
                    : 'text-crypto-muted hover:text-white hover:bg-crypto-cardHover'
                }`}
              >
                <item.icon size={16} className={`${active ? 'text-black' : 'group-hover:text-white'} transition-colors`} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full tracking-widest ${active ? 'bg-black text-crypto-accent' : 'bg-crypto-accent text-black'}`}>
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
            <Activity size={14} className="text-crypto-accent" />
            <span className="text-xs font-medium text-crypto-muted">
              {lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : 'Syncing...'}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-2">
            <div className="px-3 py-2 rounded-xl bg-gradient-to-r from-crypto-accent/10 to-crypto-accent3/10 border border-crypto-accent/20">
              <div className="flex items-center gap-2 text-xs">
                <Zap size={12} className="text-crypto-accent" />
                <span className="font-semibold text-crypto-accent">Transformer + LSTM Ensemble</span>
              </div>
            </div>
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
                    active ? 'bg-white text-black border-white' : 'bg-crypto-bg border-crypto-border text-crypto-muted hover:text-white hover:border-crypto-borderLight'
                  }`}
                >
                  <item.icon size={18} className="mb-2" />
                  <div className="font-semibold text-sm">{item.label}</div>
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
