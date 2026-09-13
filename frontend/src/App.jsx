import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Sentiment from './pages/Sentiment'
import Realtime from './pages/Realtime'
import Backtest from './pages/Backtest'
import Models from './pages/Models'
import TradingCalls from './pages/TradingCalls'
import Settings from './pages/Settings'
import Training from './pages/Training'
import Portfolio from './pages/Portfolio'
import Strategies from './pages/Strategies'
import Scanner from './pages/Scanner'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import Journal from './pages/Journal'
import AutoTrading from './pages/AutoTrading'
import { useSettingsStore } from './store/useSettingsStore'

export default function App() {
  const theme = useSettingsStore(s => s.theme)

  useEffect(() => {
    // Apply claymorphism theme to html
    const html = document.documentElement
    html.classList.remove('light', 'dark')
    html.classList.add(theme || 'dark')
    html.setAttribute('data-theme', theme || 'dark')
  }, [theme])

  return (
    <BrowserRouter>
      <div className={`min-h-screen font-poppins selection:bg-emerald-500/20 selection:text-emerald-400 transition-colors duration-500 ${
        theme === 'light' 
          ? 'bg-gradient-to-br from-[#FFCFDF] to-[#BBE1FA] text-[#1e293b]' 
          : 'bg-[#000000] text-[#F3F4F6]'
      }`}>
        <MarketTicker />
        <Navbar />
        <main className={theme === 'light' ? 'bg-transparent' : 'bg-[#000000]'}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trading" element={<TradingCalls />} />
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
        </main>
        <footer className={`mt-12 py-8 relative overflow-hidden transition-colors duration-500 ${
          theme === 'light'
            ? 'bg-white/70 backdrop-blur-xl border-t border-white/40'
            : 'bg-[#000000] border-t border-white/10'
        }`}>
          <div className="absolute inset-0 pointer-events-none">
            {theme === 'light' ? (
              <div className="absolute inset-0 bg-gradient-to-r from-[#FFCFDF]/20 via-transparent to-[#BBE1FA]/20"></div>
            ) : (
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-violet-500/5"></div>
            )}
          </div>
          <div className="relative max-w-[1600px] mx-auto px-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-6 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-[16px] bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center font-black text-black text-lg shadow-lg"
                    style={theme === 'dark' ? {
                      boxShadow: '0px 12px 24px rgba(0,0,0,0.5), inset 3px 3px 6px rgba(255,255,255,0.2), inset -3px -3px 6px rgba(0,0,0,0.2)'
                    } : {
                      boxShadow: '0px 12px 24px rgba(31,38,135,0.08), inset 4px 4px 8px rgba(255,255,255,0.9), inset -4px -4px 8px rgba(0,0,0,0.08)'
                    }}>
                    ₿
                  </div>
                  <span className="font-bold font-poppins">CryptoPred v7 • Claymorphism • CoinDCX Real Money • Endless Learning</span>
                </div>
                <div className="hidden lg:flex items-center gap-2 text-xs">
                  <span className="clay-pill px-3 py-1">LSTM v3 Bidir+Attn</span>
                  <span className="clay-pill px-3 py-1">Transformer v3</span>
                  <span className="clay-pill px-3 py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">ARIMA 2.57% • Real Data</span>
                  <span className="clay-pill px-3 py-1">Claymorphism UI</span>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs font-medium">
                <span className={theme === 'light' ? 'text-[#64748b]' : 'text-[#9CA3AF]'}>True Dark #000000 • Light #FFCFDF→#BBE1FA • Puffy 3D Clay</span>
                <span className="flex items-center gap-1.5">
                  <span className="live-dot !w-1.5 !h-1.5 bg-emerald-500"></span>
                  V7 CLAYMORPHISM
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
