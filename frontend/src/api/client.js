import axios from 'axios'

// In production preview (e2b.app), use relative /api which is proxied by Vite to backend
// In local dev, use localhost:8000 or VITE_API_URL env
function getApiBase() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // If we're in a preview environment (e2b.app) or production, use /api proxy
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host.includes('e2b.app') || host.includes('arena')) {
      return '/api'
    }
  }
  return 'http://localhost:8000'
}

const API_BASE = getApiBase()

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

export const api = {
  getHealth: () => client.get('/health').then(r => r.data),
  getSymbols: () => client.get('/symbols').then(r => r.data),
  getHistory: (symbol, period='1y') => client.get(`/history?symbol=${symbol}&period=${period}`).then(r => r.data),
  getPredict: (symbol) => client.get(`/predict?symbol=${symbol}`).then(r => r.data),
  getForecast: (symbol, steps=7) => client.get(`/forecast?symbol=${symbol}&steps=${steps}`).then(r => r.data),
  getSignal: (symbol) => client.get(`/signal?symbol=${symbol}`).then(r => r.data),
  getSentiment: (symbol, days=14) => client.get(`/sentiment?symbol=${symbol}&days=${days}`).then(r => r.data),
  analyzeSentiment: (text) => client.get(`/sentiment/analyze?text=${encodeURIComponent(text)}`).then(r => r.data),
  getRealtimePrice: (symbol) => client.get(`/realtime/price?symbol=${symbol}`).then(r => r.data),
  startRealtime: (symbols) => client.post(`/realtime/start?${symbols.map(s=>`symbols=${s}`).join('&')}`).then(r => r.data),
  getRealtimePrices: () => client.get('/realtime/prices').then(r => r.data),
  backtest: (payload) => client.post('/backtest', payload).then(r => r.data),
  backtestCompare: (symbol) => client.get(`/backtest/compare?symbol=${symbol}`).then(r => r.data),
  // New market endpoints
  getMarketTickers: () => client.get('/market/tickers').then(r => r.data).catch(() => ({ tickers: {} })),
  getMarketKlines: (symbol, interval='1d', limit=200) => client.get(`/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`).then(r => r.data),
}

export default client
