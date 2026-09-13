import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Sentiment from './pages/Sentiment'
import Realtime from './pages/Realtime'
import Backtest from './pages/Backtest'
import Models from './pages/Models'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-crypto-bg text-white selection:bg-crypto-accent/20 selection:text-crypto-accent">
        <MarketTicker />
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/realtime" element={<Realtime />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/models" element={<Models />} />
        </Routes>
        <footer className="border-t border-crypto-border/30 mt-12 py-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-crypto-accent/5 via-transparent to-crypto-accent2/5 pointer-events-none"></div>
          <div className="relative max-w-[1600px] mx-auto px-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-crypto-accent to-crypto-accent3 flex items-center justify-center font-black text-black">₿</div>
                  <span className="font-bold">CryptoPred v2 • Pro</span>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-crypto-muted">
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">LSTM</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">Transformer TFT</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">XGBoost</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-card border border-crypto-border">ARIMA</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-accent/10 border border-crypto-accent/20 text-crypto-accent">Real-time Binance</span>
                </div>
              </div>
              <div className="flex items-center gap-6 text-xs text-crypto-muted">
                <span>987 rows • 2023-2025 • 10 assets</span>
                <span className="hidden md:block">•</span>
                <span>Built with FastAPI + React + Lightweight Charts</span>
                <span className="flex items-center gap-1.5">
                  <span className="live-dot !w-1.5 !h-1.5"></span>
                  LIVE
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
