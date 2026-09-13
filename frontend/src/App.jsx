import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import { useSettingsStore, THEMES } from './store/useSettingsStore'

// v5 MAX: Lazy loading for performance, code splitting, reliability
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Sentiment = lazy(() => import('./pages/Sentiment'))
const Realtime = lazy(() => import('./pages/Realtime'))
const Backtest = lazy(() => import('./pages/Backtest'))
const Models = lazy(() => import('./pages/Models'))
const TradingCalls = lazy(() => import('./pages/TradingCalls'))
const Settings = lazy(() => import('./pages/Settings'))
const Training = lazy(() => import('./pages/Training'))
const Portfolio = lazy(() => import('./pages/Portfolio'))
const Strategies = lazy(() => import('./pages/Strategies'))
const Scanner = lazy(() => import('./pages/Scanner'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Journal = lazy(() => import('./pages/Journal'))
const AutoTrading = lazy(() => import('./pages/AutoTrading'))
const CrashDetector = lazy(() => import('./pages/CrashDetector'))

// v5 MAX: Error Boundary for reliability
import React from 'react'
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, info) {
    console.error('v5 MAX ErrorBoundary:', error, info)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-black text-white p-8">
          <div className="max-w-md text-center space-y-4">
            <div className="text-6xl">⚠️</div>
            <h1 className="text-2xl font-black">Something went wrong v5</h1>
            <p className="text-sm text-zinc-400">{this.state.error?.message || 'Unknown error'}</p>
            <button onClick={() => window.location.reload()} className="px-6 py-3 bg-white text-black rounded-xl font-bold hover:bg-zinc-200 transition">
              Reload v5 MAX
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function LoadingFallback() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto" />
        <div className="text-[12px] text-zinc-500 font-bold uppercase tracking-wide">Loading v5 MAX...</div>
      </div>
    </div>
  )
}

export default function App() {
  const { theme, accent, font, density, animations, blur, showMarketTicker } = useSettingsStore()

  useEffect(() => {
    const html = document.documentElement
    // Remove all theme classes
    Object.keys(THEMES).forEach(t => html.classList.remove(t))
    html.classList.remove('light', 'dark')
    const themeId = THEMES[theme] ? theme : 'dark'
    html.classList.add(themeId)
    const isLight = ['light', 'sakura', 'mono'].includes(themeId)
    html.classList.add(isLight ? 'light' : 'dark')
    html.setAttribute('data-theme', themeId)
    html.setAttribute('data-accent', accent || 'emerald')
    html.setAttribute('data-font', font || 'poppins')
    html.setAttribute('data-density', density || 'comfortable')
    html.setAttribute('data-animations', animations ? 'true' : 'false')
    html.setAttribute('data-blur', blur ? 'true' : 'false')
    
    // Apply font
    const fontMap = {
      poppins: "'Poppins', sans-serif",
      inter: "'Inter', sans-serif",
      space: "'Space Grotesk', sans-serif",
      outfit: "'Outfit', sans-serif"
    }
    document.body.style.fontFamily = fontMap[font] || fontMap.poppins
  }, [theme, accent, font, density, animations, blur])

  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const currentTheme = THEMES[theme] || THEMES.dark

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <div className={`min-h-screen font-poppins selection:bg-[var(--accent)] selection:text-[var(--bg)] theme-bg ${isLight ? '' : ''}`} style={{ fontFamily: `var(--font, 'Poppins')` }}>
        {showMarketTicker && <MarketTicker />}
        <Navbar />
        <main className="min-h-[calc(100vh-200px)] relative">
          <div className="absolute inset-0 pointer-events-none opacity-[0.02]">
            <div className="absolute inset-0" style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, var(--text) 1px, transparent 0)`,
              backgroundSize: '40px 40px'
            }} />
          </div>
          <div className="relative z-10">
            <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trading" element={<TradingCalls />} />
              <Route path="/crash" element={<CrashDetector />} />
              <Route path="/autotrade" element={<AutoTrading />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/journal" element={<Journal />} />
              <Route path="/training" element={<Training />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/sentiment" element={<Sentiment />} />
              <Route path="/realtime" element={<Realtime />} />
              <Route path="/backtest" element={<Backtest />} />
              <Route path="/models" element={<Models />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
            </Suspense>
          </div>
        </main>
        
        {/* Enhanced Footer */}
        <footer className={`mt-16 border-t backdrop-blur-xl relative overflow-hidden ${isLight ? 'bg-white/80 border-black/5' : 'bg-[var(--card)]/80 border-[var(--border)]'} glass`}>
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent)]/5 via-transparent to-[var(--accent)]/5 pointer-events-none" />
          <div className="max-w-[1600px] mx-auto px-6 py-8 relative z-10">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-[14px] shadow-lg ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>₿</div>
                  <span className={`font-black text-[16px] ${isLight ? 'text-black' : 'text-white'}`}>CryptoPred</span>
                  <span className="ui-pill-accent text-[9px] font-black px-2 py-1">V8 MAX</span>
                </div>
                <p className={`text-[12px] leading-relaxed ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Real trading intelligence v5 MAX • CoinDCX real money • {Object.keys(THEMES).length} themes • Pooling metrics security • Endless learning</p>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-1 rounded-full border font-bold ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
                  <span className="ui-pill text-[10px]">{currentTheme.category}</span>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>Trading</div>
                <div className={`space-y-2 text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  <div>• Live Binance + CoinDCX</div>
                  <div>• Real entry/SL/TP</div>
                  <div>• No simulation</div>
                  <div>• Auto trading bots</div>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>AI Models</div>
                <div className={`space-y-2 text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violet-500" /> LSTM v3 + Attention</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-cyan-500" /> Transformer Learnable PE</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-emerald-500" /> XGBoost 1500 trees</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-orange-500" /> ARIMA 2.57% MAPE</div>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>Themes</div>
                <div className="grid grid-cols-4 gap-1.5">
                  {Object.values(THEMES).slice(0, 8).map(t => (
                    <div key={t.id} className={`w-8 h-8 rounded-lg border flex items-center justify-center text-[14px] hover:scale-110 transition-transform cursor-pointer ${t.preview}`} title={`${t.name} - ${t.desc}`}>
                      {t.icon}
                    </div>
                  ))}
                </div>
                <div className={`text-[10px] mt-2 ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{Object.keys(THEMES).length} themes • Minimal to Cyberpunk</div>
              </div>
            </div>
            
            <div className={`pt-6 border-t flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] ${isLight ? 'border-black/5 text-zinc-500' : 'border-white/5 text-zinc-500'}`}>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="flex items-center gap-2">
                  <span className="live-dot"></span> LIVE • REAL DATA • NO SIMULATION
                </span>
                <span className="hidden md:inline w-1 h-1 rounded-full bg-[var(--border)]" />
                <span className="hidden md:inline">182 features • RobustScaler • Dynamic ensemble</span>
              </div>
              <div className="flex items-center gap-2">
                <span>Built for real traders • CoinDCX INR • Endless learning</span>
                <span className="ui-pill-accent text-[9px]">V7 • {new Date().getFullYear()}</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
