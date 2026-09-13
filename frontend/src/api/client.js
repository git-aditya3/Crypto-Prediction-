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
  // Market endpoints - real data
  getMarketTickers: () => client.get('/market/tickers').then(r => r.data).catch(() => ({ tickers: {} })),
  getMarketKlines: (symbol, interval='1d', limit=200) => client.get(`/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`).then(r => r.data),
  // Trading calls - REAL TRADING
  getTradingCalls: (params={}) => {
    const qs = new URLSearchParams()
    if (params.symbols) qs.append('symbols', params.symbols.join ? params.symbols.join(',') : params.symbols)
    if (params.timeframe) qs.append('timeframe', params.timeframe)
    if (params.accountBalance) qs.append('account_balance', params.accountBalance)
    if (params.riskPerTrade) qs.append('risk_per_trade', params.riskPerTrade)
    if (params.useCache === false) qs.append('use_cache', 'false')
    return client.get(`/trading/calls?${qs.toString()}`).then(r => r.data)
  },
  getTradingCall: (symbol, timeframe='1d', accountBalance=10000, riskPerTrade=0.02) => 
    client.get(`/trading/call/${symbol}?timeframe=${timeframe}&account_balance=${accountBalance}&risk_per_trade=${riskPerTrade}`).then(r => r.data),
  getTradingSummary: () => client.get('/trading/summary').then(r => r.data),
  getTradingGuide: () => client.get('/trading/real/guide').then(r => r.data),
  getSettings: () => client.get('/settings').then(r => r.data),
  // Continuous training
  getTrainingStatus: () => client.get('/training/status').then(r => r.data),
  startTraining: (payload) => client.post('/training/start', payload).then(r => r.data),
  stopTraining: () => client.post('/training/stop').then(r => r.data),
  retrainSymbol: (symbol, epochs=80) => client.post(`/training/retrain/${symbol}?epochs=${epochs}`).then(r => r.data),
  retrainAll: (payload) => client.post('/training/retrain', payload).then(r => r.data),
  getModels: () => client.get('/models').then(r => r.data),
  // Portfolio - Real holdings
  getPortfolio: () => client.get('/portfolio').then(r => r.data),
  openPosition: (payload) => client.post('/portfolio/open', payload).then(r => r.data),
  closePosition: (symbol, currentPrice) => client.post(`/portfolio/close/${symbol}${currentPrice ? `?current_price=${currentPrice}` : ''}`).then(r => r.data),
  getPortfolioPerformance: () => client.get('/portfolio/performance').then(r => r.data),
  // Strategies - DCA, Grid, Breakout
  createDCABot: (payload) => client.post('/strategies/dca', payload).then(r => r.data),
  createGridBot: (payload) => client.post('/strategies/grid', payload).then(r => r.data),
  scanBreakouts: (symbols) => client.get(`/strategies/breakout/scan${symbols ? `?symbols=${symbols}` : ''}`).then(r => r.data),
  getAllStrategies: () => client.get('/strategies/all').then(r => r.data),
  // Alerts
  getAlerts: () => client.get('/alerts').then(r => r.data),
  createAlert: (payload) => client.post('/alerts/create', payload).then(r => r.data),
  getActiveAlerts: () => client.get('/alerts/active').then(r => r.data),
  checkAlerts: () => client.get('/alerts/check').then(r => r.data),
  cancelAlert: (id) => client.delete(`/alerts/${id}`).then(r => r.data),
  // Scanner - Real opportunities
  getScanner: () => client.get('/scanner').then(r => r.data),
  getVolumeSpikes: () => client.get('/scanner/volume').then(r => r.data),
  getMomentum: () => client.get('/scanner/momentum').then(r => r.data),
  getRsiSignals: () => client.get('/scanner/rsi').then(r => r.data),
  // Analytics - Real P&L
  getAnalytics: () => client.get('/analytics').then(r => r.data),
  getAnalyticsMetrics: () => client.get('/analytics/metrics').then(r => r.data),
  getEquityCurve: () => client.get('/analytics/equity').then(r => r.data),
  getSymbolPerformance: () => client.get('/analytics/symbols').then(r => r.data),
  // Journal
  getJournal: (symbol, tag) => {
    const qs = new URLSearchParams()
    if (symbol) qs.append('symbol', symbol)
    if (tag) qs.append('tag', tag)
    return client.get(`/journal?${qs.toString()}`).then(r => r.data)
  },
  addJournalEntry: (payload) => client.post('/journal/add', payload).then(r => r.data),
  getJournalStats: () => client.get('/journal/stats').then(r => r.data),
  // Brokers - CoinDCX REAL MONEY, no paper simulation
  getBrokers: () => client.get('/brokers').then(r => r.data),
  connectBroker: (payload) => client.post('/brokers/connect', payload).then(r => r.data),
  getBrokerBalance: (brokerId) => client.get(`/brokers/${brokerId}/balance`).then(r => r.data),
  testBroker: (brokerId) => client.get(`/brokers/${brokerId}/test`).then(r => r.data),
  removeBroker: (brokerId) => client.delete(`/brokers/${brokerId}/remove`).then(r => r.data),
  getBrokerOrders: (brokerId, symbol) => client.get(`/brokers/${brokerId}/orders${symbol ? `?symbol=${symbol}` : ''}`).then(r => r.data),
  // Auto Trading - CoinDCX REAL MONEY, extensive controls, no paper simulation
  getAutoTradeConfig: () => client.get('/autotrade/config').then(r => r.data),
  updateAutoTradeConfig: (config) => client.post('/autotrade/config', { config }).then(r => r.data),
  getAutoTradeStatus: () => client.get('/autotrade/status').then(r => r.data),
  startAutoTrade: () => client.post('/autotrade/start').then(r => r.data),
  stopAutoTrade: () => client.post('/autotrade/stop').then(r => r.data),
  emergencyStop: () => client.post('/autotrade/emergency/stop').then(r => r.data),
  disableEmergencyStop: () => client.post('/autotrade/emergency/disable').then(r => r.data),
  executeAutoTrade: (symbol, manual=true) => client.post('/autotrade/execute', { symbol, manual }).then(r => r.data),
  approveTrade: (approvalId) => client.post(`/autotrade/approve/${approvalId}`).then(r => r.data),
  rejectTrade: (approvalId) => client.post(`/autotrade/reject/${approvalId}`).then(r => r.data),
  getAutoTradeTrades: (limit=100) => client.get(`/autotrade/trades?limit=${limit}`).then(r => r.data),
  getPendingApprovals: () => client.get('/autotrade/pending').then(r => r.data),
  checkRisk: (params) => {
    const qs = new URLSearchParams(params)
    return client.post(`/autotrade/risk/check?${qs.toString()}`).then(r => r.data)
  }
}

export default client
