import axios from 'axios'

// v5 MAX: Improved API client with pooling, retry, metrics, security, caching

function getApiBase() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // Same-origin by default: the API server serves both the built app and
  // the REST API (it strips the /api prefix; Vite's dev proxy does the same).
  // Set VITE_API_URL to point at a different server if needed.
  return '/api'
}

const API_BASE = getApiBase()

// v5 MAX: Metrics tracking
const metrics = {
  requests: 0,
  cache_hits: 0,
  errors: 0,
  avg_latency_ms: 0,
  version: "v5_max"
}

// Simple cache v5
const cache = new Map()
const CACHE_TTL = 10000 // 10s
function cacheGet(key) {
  const entry = cache.get(key)
  if (entry && Date.now() - entry.ts < CACHE_TTL) {
    metrics.cache_hits++
    return entry.data
  }
  return null
}
function cacheSet(key, data) {
  cache.set(key, { data, ts: Date.now() })
  // Limit size
  if (cache.size > 100) {
    const firstKey = cache.keys().next().value
    cache.delete(firstKey)
  }
}

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

// v5 MAX: Request interceptor with metrics, retry
client.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: Date.now() }
    config.headers['X-Client-Version'] = 'v8_max'
    config.headers['X-Request-ID'] = Math.random().toString(36).substr(2, 9)
    return config
  },
  (error) => Promise.reject(error)
)

client.interceptors.response.use(
  (response) => {
    const latency = Date.now() - (response.config.metadata?.startTime || Date.now())
    metrics.requests++
    const prev = metrics.avg_latency_ms
    const total = metrics.requests
    metrics.avg_latency_ms = total > 1 ? (prev * (total-1) + latency) / total : latency
    return response
  },
  (error) => {
    metrics.errors++
    // v5 MAX: Retry logic for 429 and 5xx
    const config = error.config
    if (!config) return Promise.reject(error)
    
    config._retryCount = config._retryCount || 0
    if (config._retryCount >= 2) {
      return Promise.reject(error)
    }
    
    if (error.response && (error.response.status === 429 || error.response.status >= 500)) {
      config._retryCount++
      const delay = Math.pow(2, config._retryCount) * 500 + Math.random() * 200 // jitter
      return new Promise(resolve => setTimeout(() => resolve(client(config)), delay))
    }
    
    return Promise.reject(error)
  }
)

export const api = {
  getMetrics: () => ({ ...metrics }),
  clearCache: () => cache.clear(),
  getHealth: () => client.get('/health').then(r => r.data),
  getApiMetrics: () => client.get('/metrics').then(r => r.data).catch(() => metrics),
  getSymbols: () => {
    const key = 'symbols'
    const cached = cacheGet(key)
    if (cached) return Promise.resolve(cached)
    return client.get('/symbols').then(r => {
      cacheSet(key, r.data)
      return r.data
    })
  },
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
  getMarketTickers: () => {
    const key = 'market_tickers'
    const cached = cacheGet(key)
    if (cached) return Promise.resolve(cached)
    return client.get('/market/tickers').then(r => {
      cacheSet(key, r.data)
      return r.data
    }).catch(() => ({ tickers: {} }))
  },
  getMarketKlines: (symbol, interval='1d', limit=200) => client.get(`/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`).then(r => r.data),
  getMarketAll: () => client.get('/market/all').then(r => r.data).catch(() => ({ tickers: {} })),
  getCoinDCXTickers: () => client.get('/market/coindcx/tickers').then(r => r.data).catch(() => ({ tickers: {} })),
  getCoinDCXPrice: (symbol) => client.get(`/market/coindcx/price?symbol=${symbol}`).then(r => r.data),
  getCoinDCXOrderbook: (symbol, limit=20) => client.get(`/market/coindcx/orderbook?symbol=${symbol}&limit=${limit}`).then(r => r.data),
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
  getTrainingStatus: () => client.get('/training/status').then(r => r.data),
  startTraining: (payload) => client.post('/training/start', payload).then(r => r.data),
  stopTraining: () => client.post('/training/stop').then(r => r.data),
  retrainSymbol: (symbol, epochs=80) => client.post(`/training/retrain/${symbol}?epochs=${epochs}`).then(r => r.data),
  retrainAll: (payload) => client.post('/training/retrain', payload).then(r => r.data),
  getModels: () => client.get('/models').then(r => r.data),
  getPortfolio: () => client.get('/portfolio').then(r => r.data),
  openPosition: (payload) => client.post('/portfolio/open', payload).then(r => r.data),
  closePosition: (symbol, currentPrice) => client.post(`/portfolio/close/${symbol}${currentPrice ? `?current_price=${currentPrice}` : ''}`).then(r => r.data),
  getPortfolioPerformance: () => client.get('/portfolio/performance').then(r => r.data),
  createDCABot: (payload) => client.post('/strategies/dca', payload).then(r => r.data),
  createGridBot: (payload) => client.post('/strategies/grid', payload).then(r => r.data),
  scanBreakouts: (symbols) => client.get(`/strategies/breakout/scan${symbols ? `?symbols=${symbols}` : ''}`).then(r => r.data),
  getAllStrategies: () => client.get('/strategies/all').then(r => r.data),
  createMMBot: (payload) => client.post('/strategies/market_making', payload).then(r => r.data),
  getMMQuote: (symbol) => client.get(`/strategies/market_making/${symbol}`).then(r => r.data),
  createExecution: (payload) => client.post('/strategies/execution', payload).then(r => r.data),
  createStatArb: (payload) => client.post('/strategies/stat_arb', payload).then(r => r.data),
  getStatArb: (a,b) => client.get(`/strategies/stat_arb/${a}/${b}`).then(r => r.data),
  createOFI: (payload) => client.post('/strategies/orderbook_imbalance', payload).then(r => r.data),
  getOFI: (symbol) => client.get(`/strategies/orderbook_imbalance/${symbol}`).then(r => r.data),
  createFundingArb: (payload) => client.post('/strategies/funding_arb', payload).then(r => r.data),
  getFundingArb: (symbol) => client.get(`/strategies/funding_arb/${symbol}`).then(r => r.data),
  getPositionSize: (payload) => client.post('/strategies/risk/position_size', payload).then(r => r.data),
  getPortfolioRisk: (symbols) => client.get(`/strategies/risk/portfolio${symbols ? `?symbols=${symbols}` : ''}`).then(r => r.data),
  scanInstitutional: (symbols) => client.get(`/strategies/institutional/scan${symbols ? `?symbols=${symbols}` : ''}`).then(r => r.data),
  getCrashStatus: () => client.get('/crash/status').then(r => r.data),
  scanCrash: (symbols, force=false) => client.get(`/crash/scan${symbols ? `?symbols=${symbols}` : ''}${force ? (symbols ? '&force=true' : '?force=true') : ''}`).then(r => r.data),
  getCrashHistory: (limit=50) => client.get(`/crash/history?limit=${limit}`).then(r => r.data),
  getCrashAlerts: (limit=20) => client.get(`/crash/alerts?limit=${limit}`).then(r => r.data),
  getCrashSignals: () => client.get('/crash/signals').then(r => r.data),
  getCrashRaw: (symbols) => client.get(`/crash/raw${symbols ? `?symbols=${symbols}` : ''}`).then(r => r.data),
  getCrashCoinDCX: () => client.get('/crash/coindcx').then(r => r.data),
  getAlerts: () => client.get('/alerts').then(r => r.data),
  createAlert: (payload) => client.post('/alerts/create', payload).then(r => r.data),
  getActiveAlerts: () => client.get('/alerts/active').then(r => r.data),
  checkAlerts: () => client.get('/alerts/check').then(r => r.data),
  cancelAlert: (id) => client.delete(`/alerts/${id}`).then(r => r.data),
  getScanner: () => client.get('/scanner').then(r => r.data),
  getVolumeSpikes: () => client.get('/scanner/volume').then(r => r.data),
  getMomentum: () => client.get('/scanner/momentum').then(r => r.data),
  getRsiSignals: () => client.get('/scanner/rsi').then(r => r.data),
  getAnalytics: () => client.get('/analytics').then(r => r.data),
  getAnalyticsMetrics: () => client.get('/analytics/metrics').then(r => r.data),
  getEquityCurve: () => client.get('/analytics/equity').then(r => r.data),
  getSymbolPerformance: () => client.get('/analytics/symbols').then(r => r.data),
  getJournal: (symbol, tag) => {
    const qs = new URLSearchParams()
    if (symbol) qs.append('symbol', symbol)
    if (tag) qs.append('tag', tag)
    return client.get(`/journal?${qs.toString()}`).then(r => r.data)
  },
  addJournalEntry: (payload) => client.post('/journal/add', payload).then(r => r.data),
  getJournalStats: () => client.get('/journal/stats').then(r => r.data),
  getBrokers: () => client.get('/brokers').then(r => r.data),
  connectBroker: (payload) => client.post('/brokers/connect', payload).then(r => r.data),
  getBrokerBalance: (brokerId) => client.get(`/brokers/${brokerId}/balance`).then(r => r.data),
  testBroker: (brokerId) => client.get(`/brokers/${brokerId}/test`).then(r => r.data),
  removeBroker: (brokerId) => client.delete(`/brokers/${brokerId}/remove`).then(r => r.data),
  getBrokerOrders: (brokerId, symbol) => client.get(`/brokers/${brokerId}/orders${symbol ? `?symbol=${symbol}` : ''}`).then(r => r.data),
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
