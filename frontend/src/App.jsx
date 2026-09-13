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
    const html = document.documentElement
    html.classList.remove('light', 'dark')
    html.classList.add(theme || 'dark')
    html.setAttribute('data-theme', theme || 'dark')
  }, [theme])

  return (
    <BrowserRouter>
      <div className={`min-h-screen font-poppins selection:bg-black selection:text-white ${theme === 'light' ? 'bg-[#E3EDF7] text-zinc-900' : 'bg-black text-zinc-100'}`}>
        <MarketTicker />
        <Navbar />
        <main className={theme === 'light' ? 'bg-[#E3EDF7]' : 'bg-black'}>
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
        <footer className={`mt-12 py-6 border-t ${theme === 'light' ? 'bg-white border-black/5' : 'bg-black border-white/10'}`}>
          <div className="max-w-[1600px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-3 text-[11px]">
            <div className="flex items-center gap-3">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-black text-[12px] ${theme === 'dark' ? 'bg-white text-black' : 'bg-black text-white'}`}>₿</div>
              <span className={`font-semibold ${theme === 'dark' ? 'text-zinc-300' : 'text-zinc-700'}`}>CryptoPred v7 • CoinDCX Real Money • Endless Learning</span>
              <span className="hidden md:flex items-center gap-2">
                <span className="ui-pill">LSTM v3</span>
                <span className="ui-pill">Transformer v3</span>
                <span className="ui-pill-buy">ARIMA 2.57%</span>
              </span>
            </div>
            <div className="flex items-center gap-2 text-zinc-500">
              <span className="live-dot"></span> LIVE • REAL DATA • NO SIMULATION
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
