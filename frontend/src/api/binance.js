// Direct Binance API - works from browser, no backend needed
const BINANCE_REST = 'https://api.binance.com'
const BINANCE_WS = 'wss://stream.binance.com:9443'

// Map our symbols to Binance
export const SYMBOL_MAP = {
  'BTC-USD': 'BTCUSDT',
  'ETH-USD': 'ETHUSDT',
  'BNB-USD': 'BNBUSDT',
  'SOL-USD': 'SOLUSDT',
  'XRP-USD': 'XRPUSDT',
  'ADA-USD': 'ADAUSDT',
  'DOGE-USD': 'DOGEUSDT',
  'AVAX-USD': 'AVAXUSDT',
  'DOT-USD': 'DOTUSDT',
  'MATIC-USD': 'MATICUSDT',
  'POL-USD': 'POLUSDT',
}

export const REVERSE_MAP = Object.fromEntries(
  Object.entries(SYMBOL_MAP).map(([k,v]) => [v,k])
)

export const SUPPORTED = Object.keys(SYMBOL_MAP)

// Direct REST fetch - ticker 24hr for single or all
export async function fetchTicker24h(symbol = null) {
  try {
    if (symbol) {
      const binanceSym = SYMBOL_MAP[symbol] || symbol.replace('-','')
      const res = await fetch(`${BINANCE_REST}/api/v3/ticker/24hr?symbol=${binanceSym}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json()
    } else {
      // all tickers
      const res = await fetch(`${BINANCE_REST}/api/v3/ticker/24hr`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const all = await res.json()
      // filter to our symbols
      const wanted = new Set(Object.values(SYMBOL_MAP))
      return all.filter(t => wanted.has(t.symbol))
    }
  } catch (e) {
    console.warn('Binance ticker fetch failed', e)
    throw e
  }
}

// Klines / candles
export async function fetchKlines(symbol, interval='1d', limit=300) {
  const binanceSym = SYMBOL_MAP[symbol] || symbol.replace('-','')
  const res = await fetch(`${BINANCE_REST}/api/v3/klines?symbol=${binanceSym}&interval=${interval}&limit=${limit}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  // data: [openTime, open, high, low, close, volume, closeTime, quoteVol, trades, ...]
  return data.map(d => ({
    time: new Date(d[0]).toISOString().split('T')[0],
    openTime: d[0],
    open: parseFloat(d[1]),
    high: parseFloat(d[2]),
    low: parseFloat(d[3]),
    close: parseFloat(d[4]),
    volume: parseFloat(d[5]),
    closeTime: d[6],
  }))
}

// Order book
export async function fetchOrderBook(symbol, limit=20) {
  const binanceSym = SYMBOL_MAP[symbol] || symbol.replace('-','')
  const res = await fetch(`${BINANCE_REST}/api/v3/depth?symbol=${binanceSym}&limit=${limit}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return await res.json()
}

// Recent trades
export async function fetchRecentTrades(symbol, limit=50) {
  const binanceSym = SYMBOL_MAP[symbol] || symbol.replace('-','')
  const res = await fetch(`${BINANCE_REST}/api/v3/trades?symbol=${binanceSym}&limit=${limit}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return await res.json()
}

// WebSocket manager for live ticker
export class BinanceTickerWS {
  constructor(symbols, onUpdate) {
    this.symbols = symbols.map(s => (SYMBOL_MAP[s] || s.replace('-','')).toLowerCase() + '@ticker')
    this.onUpdate = onUpdate
    this.ws = null
    this.reconnectTimer = null
    this.shouldReconnect = true
  }

  connect() {
    this.shouldReconnect = true
    const streams = this.symbols.join('/')
    const url = `${BINANCE_WS}/stream?streams=${streams}`
    console.log('Connecting Binance WS:', url)
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('Binance WS connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.data) {
          const ticker = msg.data
          const originalSymbol = REVERSE_MAP[ticker.s] || ticker.s
          this.onUpdate({
            symbol: originalSymbol,
            binanceSymbol: ticker.s,
            price: parseFloat(ticker.c),
            priceChange: parseFloat(ticker.P),
            priceChangePercent: parseFloat(ticker.P),
            high: parseFloat(ticker.h),
            low: parseFloat(ticker.l),
            volume: parseFloat(ticker.v),
            quoteVolume: parseFloat(ticker.q),
            open: parseFloat(ticker.o),
            lastPrice: parseFloat(ticker.c),
            ...ticker
          })
        }
      } catch (e) {
        console.warn('WS parse error', e)
      }
    }

    this.ws.onclose = () => {
      console.log('Binance WS closed')
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000)
      }
    }

    this.ws.onerror = (e) => {
      console.warn('Binance WS error', e)
      this.ws.close()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// WebSocket for trades
export class BinanceTradeWS {
  constructor(symbol, onTrade) {
    this.symbol = (SYMBOL_MAP[symbol] || symbol.replace('-','')).toLowerCase()
    this.onTrade = onTrade
    this.ws = null
    this.shouldReconnect = true
  }

  connect() {
    this.shouldReconnect = true
    const url = `${BINANCE_WS}/ws/${this.symbol}@trade`
    this.ws = new WebSocket(url)

    this.ws.onmessage = (event) => {
      try {
        const trade = JSON.parse(event.data)
        this.onTrade({
          price: parseFloat(trade.p),
          qty: parseFloat(trade.q),
          time: trade.T,
          isBuyerMaker: trade.m,
          symbol: trade.s
        })
      } catch {}
    }

    this.ws.onclose = () => {
      if (this.shouldReconnect) {
        setTimeout(() => this.connect(), 2000)
      }
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.ws) this.ws.close()
  }
}
