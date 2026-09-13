import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Sentiment from './pages/Sentiment'
import Realtime from './pages/Realtime'
import Backtest from './pages/Backtest'
import Models from './pages/Models'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-crypto-bg">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/realtime" element={<Realtime />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/models" element={<Models />} />
        </Routes>
        <footer className="border-t border-crypto-border mt-12 py-6 text-center text-xs text-gray-500">
          Crypto Prediction v2 • LSTM • Transformer • XGBoost • ARIMA • Sentiment • Realtime • Backtesting • React
        </footer>
      </div>
    </BrowserRouter>
  )
}
