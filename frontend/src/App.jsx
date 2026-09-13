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
        <div className="min-h-screen flex items-center justify-center bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white p-8">
          <div className="max-w-md text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center mx-auto font-medium">!</div>
            <h1 className="text-[18px] font-semibold">Something went wrong</h1>
            <p className="text-[13px] text-zinc-500">{this.state.error?.message || 'Unknown'}</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-black text-[13px] font-medium">Reload</button>
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
        <div className="w-6 h-6 border border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin mx-auto" />
        <div className="text-[11px] text-zinc-500 font-medium uppercase tracking-wide">Loading</div>
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
    const isLight = themeId === 'light' || themeId === 'mono'
    html.classList.add(isLight ? 'light' : 'dark')
    html.setAttribute('data-theme', themeId)
    html.setAttribute('data-accent', 'zinc')
    html.setAttribute('data-font', font || 'geist')
    html.setAttribute('data-density', density || 'comfortable')
    html.setAttribute('data-animations', animations ? 'true' : 'false')
    html.setAttribute('data-blur', blur ? 'true' : 'false')
    document.body.style.fontFamily = "'Geist', system-ui, sans-serif"
  }, [theme, accent, font, density, animations, blur])

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <div className="min-h-screen theme-bg selection:bg-zinc-900 selection:text-white dark:selection:bg-white dark:selection:text-black">
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
        
        <footer className="mt-12 border-t bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800">
          <div className="max-w-[1600px] mx-auto px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] text-zinc-500">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center font-medium text-[11px]">₿</span>
                <span className="font-medium text-zinc-900 dark:text-white">CryptoPred</span>
                <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[9px] font-medium">MINIMAL</span>
                <span className="hidden md:inline-flex items-center gap-1.5"><span className="w-1 h-1 rounded-full bg-zinc-900 dark:bg-white animate-pulse" /> LIVE • REAL • NO SIMULATION • 120FPS</span>
              </div>
              <div className="flex items-center gap-2">
                <span>Monochrome • No colors • GPU accelerated</span>
                <span className="px-2 py-0.5 rounded-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px]">2026</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
