import { BrowserRouter, Routes, Route } from 'react-router-dom'
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

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-crypto-bg text-white selection:bg-emerald-500/20 selection:text-emerald-400">
        <MarketTicker />
        <Navbar />
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
        <footer className="border-t border-crypto-border/30 mt-12 py-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-violet-500/5 pointer-events-none"></div>
          <div className="relative max-w-[1600px] mx-auto px-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center font-black text-black">₿</div>
                  <span className="font-bold">CryptoPred v6 • Automated Real Trading • Extensive Control • Endless Learning</span>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-crypto-muted">
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">LSTM v3 Bidir+Attn</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">Transformer v3 Learnable PE</span>
                  <span className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">ARIMA 2.57% • Real Data</span>
                  <span className="px-2 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400">Auto Trading • Brokers • Risk Guard</span>
                </div>
              </div>
              <div className="flex items-center gap-6 text-xs text-crypto-muted">
                <span>Automated Real Trading • Extensive User Control • Live Binance</span>
                <span className="hidden md:block">•</span>
                <span>Paper/Semi/Full Auto • Broker Integration</span>
                <span className="flex items-center gap-1.5">
                  <span className="live-dot !w-1.5 !h-1.5 bg-emerald-500"></span>
                  V6 AUTO TRADING
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
