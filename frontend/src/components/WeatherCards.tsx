import type { WeatherCurrent } from '../types'

function fmt(v: number | null, digits = 1): string {
  return v == null ? '—' : v.toFixed(digits)
}

export default function WeatherCards({ current }: { current: WeatherCurrent }) {
  const cards = [
    { label: 'Rainfall', unit: 'mm', value: fmt(current.rainfall_mm), icon: '🌧️' },
    { label: 'Temperature', unit: '°C', value: fmt(current.temperature_c), icon: '🌡️' },
    { label: 'Humidity', unit: '%', value: fmt(current.humidity_pct, 0), icon: '💧' },
    { label: 'Pressure', unit: 'hPa', value: fmt(current.pressure_hpa, 0), icon: '🌀' },
    { label: 'Wind Speed', unit: 'km/h', value: fmt(current.wind_kmh), icon: '💨' },
  ]
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-2xl">{c.icon}</div>
          <div className="mt-2 text-lg font-bold text-slate-800">
            {c.value} <span className="text-xs font-normal text-slate-500">{c.unit}</span>
          </div>
          <div className="text-xs text-slate-500">{c.label}</div>
        </div>
      ))}
    </div>
  )
}
