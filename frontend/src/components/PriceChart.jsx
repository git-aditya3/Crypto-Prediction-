import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'

export default function PriceChart({ data, forecast, height = 420, realtimePrice = null, symbol = 'BTC-USD' }) {
  const ref = useRef()
  const chartRef = useRef()
  const seriesRef = useRef({})
  const [interval, setInterval] = useState('1D')
  const [showForecast, setShowForecast] = useState(true)
  const [showVolume, setShowVolume] = useState(true)

  useEffect(() => {
    if (!ref.current || !data) return
    ref.current.innerHTML = ''

    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height,
      layout: { 
        background: { type: 'solid', color: 'transparent' }, 
        textColor: '#64748b',
        fontFamily: 'JetBrains Mono',
        fontSize: 11
      },
      grid: { 
        vertLines: { color: 'rgba(30,42,58,0.5)', style: 1 }, 
        horzLines: { color: 'rgba(30,42,58,0.5)', style: 1 } 
      },
      timeScale: { 
        borderColor: '#1e2a3a',
        timeVisible: true,
        secondsVisible: false,
        borderVisible: false,
      },
      rightPriceScale: { 
        borderColor: '#1e2a3a',
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: showVolume ? 0.2 : 0.05 }
      },
      crosshair: {
        mode: 1,
        vertLine: { color: 'rgba(0,211,149,0.3)', width: 1, style: 2 },
        horzLine: { color: 'rgba(0,211,149,0.3)', width: 1, style: 2 }
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true }
    })

    chartRef.current = chart

    // Candlestick
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00d395',
      downColor: '#ff4b4b',
      borderUpColor: '#00d395',
      borderDownColor: '#ff4b4b',
      wickUpColor: '#00d395',
      wickDownColor: '#ff4b4b',
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
    })

    const candles = data.dates.map((d, i) => ({
      time: d,
      open: data.open[i],
      high: data.high[i],
      low: data.low[i],
      close: data.close[i]
    }))

    candleSeries.setData(candles)
    seriesRef.current.candle = candleSeries

    // Volume
    if (showVolume && data.volume) {
      const volumeSeries = chart.addHistogramSeries({
        color: 'rgba(100,116,139,0.3)',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
        priceLineVisible: false,
      })
      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 }
      })
      const volData = data.dates.map((d, i) => ({
        time: d,
        value: data.volume[i],
        color: data.close[i] >= data.open[i] ? 'rgba(0,211,149,0.3)' : 'rgba(255,75,75,0.3)'
      }))
      volumeSeries.setData(volData)
      seriesRef.current.volume = volumeSeries
    }

    // Forecast lines
    if (forecast && showForecast && forecast.ensemble) {
      // Ensemble - main prediction
      const ensembleSeries = chart.addLineSeries({ 
        color: '#00d395', 
        lineWidth: 2.5,
        priceLineVisible: false,
        lastValueVisible: true,
        crosshairMarkerVisible: true,
        lineStyle: 0
      })
      const fcData = forecast.dates.map((d, i) => ({
        time: d,
        value: forecast.ensemble[i]
      })).filter(d => d.value != null)
      ensembleSeries.setData(fcData)
      seriesRef.current.ensemble = ensembleSeries

      // Transformer
      if (forecast.transformer) {
        const tSeries = chart.addLineSeries({ 
          color: '#6366f1', 
          lineWidth: 1.5, 
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        })
        tSeries.setData(forecast.dates.map((d, i) => ({ time: d, value: forecast.transformer[i] })).filter(d => d.value != null))
        seriesRef.current.transformer = tSeries
      }

      // LSTM
      if (forecast.lstm) {
        const lstmSeries = chart.addLineSeries({ 
          color: '#06b6d4', 
          lineWidth: 1, 
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        })
        lstmSeries.setData(forecast.dates.map((d, i) => ({ time: d, value: forecast.lstm[i] })).filter(d => d.value != null))
        seriesRef.current.lstm = lstmSeries
      }

      // Create forecast area
      const lastHistoricalTime = data.dates[data.dates.length - 1]
      const firstForecastTime = forecast.dates[0]
      
      // Add a vertical line at forecast start
      if (lastHistoricalTime && firstForecastTime) {
        candleSeries.createPriceLine({
          price: data.close[data.close.length - 1],
          color: 'rgba(0,211,149,0.3)',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: false,
          title: 'Forecast Start'
        })
      }
    }

    // Real-time price line
    if (realtimePrice) {
      const priceLine = candleSeries.createPriceLine({
        price: realtimePrice,
        color: '#00d395',
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'LIVE',
      })
      seriesRef.current.liveLine = priceLine
    }

    chart.timeScale().fitContent()

    const handleResize = () => {
      if (ref.current) {
        chart.applyOptions({ width: ref.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, forecast, height, showVolume, showForecast])

  // Update live price
  useEffect(() => {
    if (seriesRef.current.candle && realtimePrice && seriesRef.current.liveLine) {
      try {
        seriesRef.current.candle.removePriceLine(seriesRef.current.liveLine)
      } catch {}
      const line = seriesRef.current.candle.createPriceLine({
        price: realtimePrice,
        color: '#00d395',
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'LIVE',
      })
      seriesRef.current.liveLine = line
    }
  }, [realtimePrice])

  if (!data) {
    return (
      <div className="w-full rounded-2xl border border-crypto-border bg-crypto-card/50 p-8 flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-crypto-card border border-crypto-border flex items-center justify-center animate-pulse">
            <div className="w-6 h-6 rounded bg-crypto-border"></div>
          </div>
          <div className="text-sm text-crypto-muted">Loading chart data...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative rounded-2xl overflow-hidden border border-crypto-border/50 bg-crypto-card/30 backdrop-blur-xl">
      {/* Chart header */}
      <div className="absolute top-0 left-0 right-0 z-10 p-4 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-3 pointer-events-auto">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-crypto-bg/80 backdrop-blur border border-crypto-border/50">
            <div className="w-2 h-2 rounded-full bg-crypto-accent animate-pulse"></div>
            <span className="text-xs font-bold tracking-widest text-white">{symbol}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-crypto-accent/20 text-crypto-accent font-bold">BINANCE</span>
          </div>
          {realtimePrice && (
            <div className="px-3 py-1.5 rounded-full bg-crypto-accent/10 border border-crypto-accent/20 backdrop-blur">
              <span className="text-xs mono font-bold text-crypto-accent">${realtimePrice.toLocaleString()}</span>
              <span className="text-[10px] text-crypto-accent/70 ml-2">LIVE</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="flex items-center gap-1 p-1 rounded-xl bg-crypto-bg/80 backdrop-blur border border-crypto-border/50">
            {['1D', '1W', '1M', '1Y'].map(iv => (
              <button
                key={iv}
                onClick={() => setInterval(iv)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                  interval === iv ? 'bg-white text-black' : 'text-crypto-muted hover:text-white'
                }`}
              >
                {iv}
              </button>
            ))}
          </div>
          
          <div className="flex items-center gap-1 p-1 rounded-xl bg-crypto-bg/80 backdrop-blur border border-crypto-border/50">
            <button
              onClick={() => setShowForecast(!showForecast)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition ${showForecast ? 'bg-crypto-accent text-black' : 'text-crypto-muted hover:text-white'}`}
            >
              Forecast
            </button>
            <button
              onClick={() => setShowVolume(!showVolume)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition ${showVolume ? 'bg-crypto-cardHover text-white' : 'text-crypto-muted hover:text-white'}`}
            >
              Volume
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div ref={ref} className="w-full chart-container" style={{ paddingTop: '60px' }} />

      {/* Legend */}
      {forecast && showForecast && (
        <div className="absolute bottom-4 left-4 flex items-center gap-4 px-4 py-2 rounded-xl bg-crypto-bg/80 backdrop-blur border border-crypto-border/50">
          <div className="flex items-center gap-2 text-[11px]">
            <div className="w-3 h-0.5 bg-crypto-accent rounded"></div>
            <span className="text-crypto-muted font-medium">Ensemble</span>
          </div>
          {forecast.transformer && (
            <div className="flex items-center gap-2 text-[11px]">
              <div className="w-3 h-0.5 bg-[#6366f1] rounded border-dashed border-t border-[#6366f1]"></div>
              <span className="text-crypto-muted">Transformer</span>
            </div>
          )}
          {forecast.lstm && (
            <div className="flex items-center gap-2 text-[11px]">
              <div className="w-3 h-0.5 bg-[#06b6d4] rounded"></div>
              <span className="text-crypto-muted">LSTM</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
