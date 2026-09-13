import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function PriceChart({ data, forecast, height=400 }) {
  const ref = useRef()

  useEffect(() => {
    if (!ref.current || !data) return
    ref.current.innerHTML = ''
    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height,
      layout: { background: { color: '#151a21' }, textColor: '#9ca3af' },
      grid: { vertLines: { color: '#232a34' }, horzLines: { color: '#232a34' } },
      timeScale: { borderColor: '#232a34' },
      rightPriceScale: { borderColor: '#232a34' }
    })

    const candleSeries = chart.addCandlestickSeries()
    const candles = data.dates.map((d,i) => ({
      time: d,
      open: data.open[i],
      high: data.high[i],
      low: data.low[i],
      close: data.close[i]
    }))
    candleSeries.setData(candles)

    if (forecast && forecast.ensemble) {
      const lineSeries = chart.addLineSeries({ color: '#00d395', lineWidth: 2 })
      const fcData = forecast.dates.map((d,i) => ({
        time: d,
        value: forecast.ensemble[i]
      }))
      lineSeries.setData(fcData)

      if (forecast.lstm) {
        const lstmSeries = chart.addLineSeries({ color: '#00b7eb', lineWidth: 1, lineStyle: 2 })
        lstmSeries.setData(forecast.dates.map((d,i) => ({ time: d, value: forecast.lstm[i] })))
      }
      if (forecast.transformer) {
        const tSeries = chart.addLineSeries({ color: '#f59e0b', lineWidth: 1, lineStyle: 2 })
        tSeries.setData(forecast.dates.map((d,i) => ({ time: d, value: forecast.transformer[i] })))
      }
    }

    chart.timeScale().fitContent()
    const handleResize = () => chart.applyOptions({ width: ref.current.clientWidth })
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, forecast, height])

  return <div ref={ref} className="w-full rounded-xl overflow-hidden border border-crypto-border" />
}
