import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import { useSettingsStore, THEMES, VISUAL_STYLES } from './store/useSettingsStore'

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

import React from 'react'
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null } }
  static getDerivedStateFromError(error) { return { hasError: true, error } }
  componentDidCatch(error, info) { console.error('ErrorBoundary:', error, info) }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] text-[var(--text)] p-8">
          <div className="max-w-md text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center mx-auto font-bold shadow-[var(--glow)]">!</div>
            <h1 className="text-[18px] font-semibold">Something went wrong</h1>
            <p className="text-[13px] text-[var(--text-muted)]">{this.state.error?.message || 'Unknown'}</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 rounded-full bg-[var(--accent)] text-white text-[13px] font-medium shadow-[var(--glow)]">Reload</button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function LoadingFallback() {
  const visualStyle = useSettingsStore.getState().visualStyle || 'liquid'
  return (
    <div className="min-h-[50vh] flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className={`w-10 h-10 mx-auto flex items-center justify-center ${visualStyle === 'clay' ? 'clay-card !w-12 !h-12 !rounded-2xl' : visualStyle === 'liquid' ? 'liquid-glass-card !w-12 !h-12' : visualStyle === 'brutal' ? 'brutal-card !w-10 !h-10 !rounded-sm' : 'rounded-xl bg-[var(--card)] border border-[var(--border)]'}`}>
          <div className="w-6 h-6 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
        </div>
        <div className="text-[11px] text-[var(--text-muted)] font-medium uppercase tracking-wide">Loading {visualStyle}...</div>
      </div>
    </div>
  )
}

export default function App() {
  const { theme, visualStyle, accent, font, density, animations, blur, showMarketTicker } = useSettingsStore()

  useEffect(() => {
    const html = document.documentElement
    Object.keys(THEMES).forEach(t => html.classList.remove(t))
    Object.keys(VISUAL_STYLES).forEach(v => html.classList.remove(`visual-${v}`))
    html.classList.remove('light', 'dark')
    const themeId = THEMES[theme] ? theme : 'dark'
    const visualId = VISUAL_STYLES[visualStyle] ? visualStyle : 'liquid'
    html.classList.add(themeId)
    html.classList.add(`visual-${visualId}`)
    const isLight = ['light', 'sakura', 'mono'].includes(themeId)
    html.classList.add(isLight ? 'light' : 'dark')
    html.setAttribute('data-theme', themeId)
    html.setAttribute('data-visual', visualId)
    html.setAttribute('data-accent', accent || 'emerald')
    html.setAttribute('data-font', font || 'geist')
    html.setAttribute('data-density', density || 'comfortable')
    html.setAttribute('data-animations', animations ? 'true' : 'false')
    html.setAttribute('data-blur', blur ? 'true' : 'false')
    document.body.style.fontFamily = "'Geist', system-ui, sans-serif"
  }, [theme, visualStyle, accent, font, density, animations, blur])

  const currentVisual = VISUAL_STYLES[visualStyle] || VISUAL_STYLES.liquid
  const currentTheme = THEMES[theme] || THEMES.dark

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <div className="min-h-screen theme-bg selection:bg-[var(--accent)] selection:text-white">
        {showMarketTicker && <MarketTicker />}
        <Navbar />
        <main className="min-h-[calc(100vh-120px)] relative">
          {/* Liquid glass vibrant blobs background */}
          {visualStyle === 'liquid' && (
            <>
              <div className="glass-blob w-[400px] h-[400px] bg-[var(--accent)]/10 top-[10%] left-[5%] blur-[80px]" />
              <div className="glass-blob w-[300px] h-[300px] bg-[var(--buy)]/10 top-[40%] right-[10%] blur-[60px]" style={{ animationDelay: '2s' }} />
              <div className="glass-blob w-[500px] h-[500px] bg-[var(--accent-soft)] bottom-[10%] left-[20%] blur-[100px]" style={{ animationDelay: '4s' }} />
            </>
          )}
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
        
        <footer className={`mt-12 border-t ${visualStyle === 'liquid' ? 'liquid-glass !border-t-0 !rounded-none' : visualStyle === 'clay' ? 'clay-card !rounded-none !border-x-0 !border-b-0 !mt-8' : visualStyle === 'brutal' ? 'brutal-card !rounded-none !border-x-0 !border-b-0 !border-t-[3px]' : 'bg-[var(--card)] border-[var(--border)]'}`}>
          <div className="max-w-[1600px] mx-auto px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] text-[var(--text-muted)]">
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`w-7 h-7 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center font-bold text-[11px] shadow-[var(--glow)] ${visualStyle === 'clay' ? 'clay-card !w-8 !h-8 !p-0 !rounded-xl' : visualStyle === 'brutal' ? 'brutal-card !w-7 !h-7 !p-0 !rounded-sm' : ''}`}>₿</span>
                <span className="font-medium text-[var(--text)]">CryptoPred</span>
                <span className={`px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[9px] font-bold shadow-sm ${visualStyle === 'clay' ? 'clay-pill !text-[9px]' : visualStyle === 'brutal' ? 'brutal-pill !text-[8px]' : ''}`}>V8 {currentVisual.name}</span>
                <span className="hidden md:inline-flex items-center gap-1.5"><span className="w-1 h-1 rounded-full bg-[var(--accent)] animate-pulse shadow-[var(--glow)]" /> {currentTheme.name} • {currentVisual.vibe} • 120FPS</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[var(--buy)] shadow-[0_0_8px_var(--buy-soft)]" /> Buy
                  <span className="w-2 h-2 rounded-full bg-[var(--sell)] ml-2 shadow-[0_0_8px_var(--sell-soft)]" /> Sell
                  <span className="w-2 h-2 rounded-full bg-[var(--accent)] ml-2 shadow-[var(--glow)]" /> {currentTheme.name}
                </span>
                <span className={`px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[10px] ${visualStyle === 'clay' ? 'clay-pill' : visualStyle === 'brutal' ? 'brutal-card !py-0 !px-2 !text-[9px] !rounded-sm' : ''}`}>{new Date().getFullYear()}</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
