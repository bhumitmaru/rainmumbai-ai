import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import ConfidenceDonut from '../components/ConfidenceDonut'
import Disclaimer from '../components/Disclaimer'
import IndexLineChart from '../components/IndexLineChart'
import KpiCard from '../components/KpiCard'
import ProbabilityBar from '../components/ProbabilityBar'
import RadialGauge from '../components/RadialGauge'
import Spinner from '../components/Spinner'
import WeatherCards from '../components/WeatherCards'
import { DISCLAIMER } from '../lib/constants'
import type { Performance, Prediction, PredictionHistory, WeatherForecast } from '../types'

export default function DashboardPage() {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [weather, setWeather] = useState<WeatherForecast | null>(null)
  const [history, setHistory] = useState<PredictionHistory | null>(null)
  const [perf, setPerf] = useState<Performance | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/predictions/latest'),
      api.get('/weather/forecast'),
      api.get('/predictions/history?limit=60'),
      api.get('/performance'),
    ])
      .then(([p, w, h, pf]) => {
        setPrediction(p.data as Prediction)
        setWeather(w.data as WeatherForecast)
        setHistory(h.data as PredictionHistory)
        setPerf(pf.data as Performance)
      })
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load dashboard'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner label="Loading dashboard…" />
  if (!prediction) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-600">
        {error ?? 'No prediction available yet. Please wait for the next scheduled run.'}
      </div>
    )
  }

  const dirColor =
    prediction.direction === 'Increase'
      ? 'text-green-600'
      : prediction.direction === 'Decrease'
        ? 'text-red-600'
        : 'text-amber-600'

  const devColor =
    prediction.expected_deviation > 0
      ? 'text-green-600'
      : prediction.expected_deviation < 0
        ? 'text-red-600'
        : 'text-slate-800'

  const rainData = (weather?.hourly_rainfall_24h ?? []).map((p) => ({
    time: new Date(p.time).toLocaleTimeString(undefined, { hour: '2-digit' }),
    mm: p.rainfall_mm ?? 0,
  }))

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard
          title="Current Index"
          value={prediction.current_index.toFixed(2)}
          subtitle={`Category: ${prediction.category_current}`}
        />
        <KpiCard
          title="Predicted Index"
          value={prediction.predicted_index.toFixed(2)}
          subtitle={`Category: ${prediction.category_predicted}`}
        />
        <KpiCard
          title="Expected Deviation"
          value={`${prediction.expected_deviation >= 0 ? '+' : ''}${prediction.expected_deviation.toFixed(2)}`}
          accent={devColor}
          subtitle="Predicted − current"
        />
        <KpiCard title="Direction" value={prediction.direction} accent={dirColor} subtitle="Movement" />
        <div className="flex items-center justify-center rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <RadialGauge value={prediction.confidence.overall} />
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">Direction Probability Distribution</h3>
          <span className="text-xs text-slate-500">
            Last updated: {new Date(prediction.generated_at).toLocaleString()}
          </span>
        </div>
        <ProbabilityBar probabilities={prediction.probabilities} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-800">Current Meteorological Parameters</h3>
        {weather?.current ? (
          <WeatherCards current={weather.current} />
        ) : (
          <p className="text-sm text-slate-500">Weather data unavailable.</p>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-800">24h Rainfall Trend (forecast)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={rainData} margin={{ top: 5, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="mm" name="Rainfall (mm)" fill="#38bdf8" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <h3 className="mb-3 font-semibold text-slate-800">RainMumbai Index — Actual vs Predicted</h3>
          <IndexLineChart items={history?.items ?? []} />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-800">Confidence Breakdown</h3>
          <ConfidenceDonut confidence={prediction.confidence} />
          {perf && perf.sample_count > 0 && (
            <p className="mt-2 text-center text-xs text-slate-500">
              {perf.sample_count} evaluated sample(s) · model {perf.model_version}
            </p>
          )}
        </div>
      </div>

      <Disclaimer text={prediction.disclaimer || DISCLAIMER} />
    </div>
  )
}
