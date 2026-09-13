import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import { useSettingsStore, THEMES } from './store/useSettingsStore'

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
  return (
    <div className="min-h-[50vh] flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-6 h-6 border border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin mx-auto" />
        <div className="text-[11px] text-[var(--text-muted)] font-medium uppercase tracking-wide">Loading</div>
      </div>
    </div>
  )
}

export default function App() {
  const { theme, accent, font, density, animations, blur, showMarketTicker } = useSettingsStore()

  useEffect(() => {
    const html = document.documentElement
    Object.keys(THEMES).forEach(t => html.classList.remove(t))
    html.classList.remove('light', 'dark')
    const themeId = THEMES[theme] ? theme : 'dark'
    html.classList.add(themeId)
    const isLight = ['light', 'sakura', 'mono'].includes(themeId)
    html.classList.add(isLight ? 'light' : 'dark')
    html.setAttribute('data-theme', themeId)
    html.setAttribute('data-accent', accent || 'emerald')
    html.setAttribute('data-font', font || 'geist')
    html.setAttribute('data-density', density || 'comfortable')
    html.setAttribute('data-animations', animations ? 'true' : 'false')
    html.setAttribute('data-blur', blur ? 'true' : 'false')
    document.body.style.fontFamily = "'Geist', system-ui, sans-serif"
  }, [theme, accent, font, density, animations, blur])

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <div className="min-h-screen theme-bg selection:bg-[var(--accent)] selection:text-white">
        {showMarketTicker && <MarketTicker />}
        <Navbar />
        <main className="min-h-[calc(100vh-120px)]">
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
        </main>
        
        <footer className="mt-12 border-t bg-[var(--card)] border-[var(--border)]">
          <div className="max-w-[1600px] mx-auto px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] text-[var(--text-muted)]">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center font-bold text-[11px] shadow-[var(--glow)]">₿</span>
                <span className="font-medium text-[var(--text)]">CryptoPred</span>
                <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[9px] font-bold shadow-sm">V8 THEMED</span>
                <span className="hidden md:inline-flex items-center gap-1.5"><span className="w-1 h-1 rounded-full bg-[var(--accent)] animate-pulse" /> LIVE • THEMED • REAL • 120FPS</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[var(--buy)]" /> Buy
                  <span className="w-2 h-2 rounded-full bg-[var(--sell)] ml-2" /> Sell
                  <span className="w-2 h-2 rounded-full bg-[var(--accent)] ml-2" /> Accent
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[10px]">{new Date().getFullYear()}</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
