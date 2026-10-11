import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import Disclaimer from '../components/Disclaimer'
import KpiCard from '../components/KpiCard'
import Spinner from '../components/Spinner'
import type { Performance } from '../types'

function fmtMetric(value: number | null, digits = 2) {
  return value == null ? '—' : value.toFixed(digits)
}

function fmtPct(value: number | null) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

export default function PerformancePage() {
  const [data, setData] = useState<Performance | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [source, setSource] = useState<'all' | 'live' | 'backfill'>('all')
  const [page, setPage] = useState(0)
  const limit = 25
  const seasonChoices = useMemo(() => {
    const year = new Date().getFullYear()
    return [year, year - 1, year - 2]
  }, [])
  const [season, setSeason] = useState<string>('all')

  useEffect(() => {
    const params: Record<string, string | number> = { source, limit, offset: page * limit }
    if (fromDate) params.from = `${fromDate}T00:00:00Z`
    if (toDate) params.to = `${toDate}T23:59:59Z`
    api
      .get('/performance', { params })
      .then((r) => setData(r.data as Performance))
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load performance'))
  }, [fromDate, toDate, source, page])

  useEffect(() => {
    if (season === 'all') return
    const y = Number(season)
    setFromDate(`${y}-06-01`)
    setToDate(`${y + 1}-05-31`)
    setPage(0)
  }, [season])

  if (!data) return error ? <div className="text-slate-600">{error}</div> : <Spinner />

  const runs = data.evaluation_runs.filter((r) => r.mae != null || r.rmse != null)
  const runChart = runs.map((r) => ({
    label: r.finished_at
      ? new Date(r.finished_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
      : `#${r.id}`,
    MAE: r.mae,
    RMSE: r.rmse,
    Accuracy: r.direction_accuracy == null ? null : Number((r.direction_accuracy * 100).toFixed(1)),
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Historical Performance</h1>
        <p className="mt-1 text-sm text-slate-500">
          Evaluated predictions versus observed RainMumbai Index outcomes
          {data.model_version ? ` · model ${data.model_version}` : ''}
          {data.last_evaluated_at
            ? ` · last evaluation ${new Date(data.last_evaluated_at).toLocaleString()}`
            : ''}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Historical rows marked Backfilled are backtests from archived forecasts, not live-issued predictions.
        </p>
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm md:grid-cols-4">
        <label className="space-y-1">
          <span className="text-slate-500">From</span>
          <input
            className="w-full rounded-md border border-slate-300 px-2 py-1"
            type="date"
            value={fromDate}
            onChange={(e) => {
              setPage(0)
              setSeason('all')
              setFromDate(e.target.value)
            }}
          />
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">To</span>
          <input
            className="w-full rounded-md border border-slate-300 px-2 py-1"
            type="date"
            value={toDate}
            onChange={(e) => {
              setPage(0)
              setSeason('all')
              setToDate(e.target.value)
            }}
          />
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">Source</span>
          <select
            className="w-full rounded-md border border-slate-300 px-2 py-1"
            value={source}
            onChange={(e) => {
              setPage(0)
              setSource(e.target.value as 'all' | 'live' | 'backfill')
            }}
          >
            <option value="all">All</option>
            <option value="live">Live</option>
            <option value="backfill">Backfill</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">Season</span>
          <select
            className="w-full rounded-md border border-slate-300 px-2 py-1"
            value={season}
            onChange={(e) => setSeason(e.target.value)}
          >
            <option value="all">Custom / all</option>
            {seasonChoices.map((y) => (
              <option key={y} value={String(y)}>
                {y}–{y + 1}
              </option>
            ))}
          </select>
        </label>
        <p className="md:col-span-4 text-xs text-slate-500">
          Evaluated window:{' '}
          {data.evaluated_from && data.evaluated_to
            ? `${new Date(data.evaluated_from).toLocaleDateString()} to ${new Date(data.evaluated_to).toLocaleDateString()}`
            : 'No samples'}{' '}
          · {data.sample_total} samples
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard title="MAE" value={fmtMetric(data.mae)} subtitle="Mean absolute error" />
        <KpiCard title="RMSE" value={fmtMetric(data.rmse)} subtitle="Root mean square error" />
        <KpiCard title="Direction Accuracy" value={fmtPct(data.direction_accuracy)} subtitle="Correct direction" />
        <KpiCard title="Direction F1" value={fmtPct(data.direction_f1)} subtitle="Macro-F1" />
        <KpiCard title="Samples" value={data.sample_count} subtitle="Matched outcomes" />
      </div>
      <p className="text-xs text-slate-500">
        Baseline: {data.baseline.label} · MAE {fmtMetric(data.baseline.mae)} · Direction accuracy{' '}
        {fmtPct(data.baseline.direction_accuracy)}
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-800">Prediction error over time</h3>
          {data.sample_total === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">
              No evaluated samples yet. Error series appear once predictions are matched to observed outcomes.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={data.error_series.map((s) => ({
                  label: new Date(s.target_timestamp).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }),
                  error: s.value,
                }))}
                margin={{ top: 5, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="error" name="Predicted − actual" fill="#6366f1" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-800">Cumulative direction accuracy</h3>
          {data.sample_total === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">
              Direction accuracy builds as outcomes are recorded.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart
                data={data.cumulative_accuracy_series.map((s) => ({
                  label: new Date(s.target_timestamp).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }),
                  accuracy: s.value,
                }))}
                margin={{ top: 5, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip />
                <Line type="monotone" dataKey="accuracy" name="Accuracy %" stroke="#0ea5e9" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {runChart.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-800">Evaluation runs</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={runChart} margin={{ top: 5, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="MAE" stroke="#6366f1" strokeWidth={2} dot />
              <Line yAxisId="left" type="monotone" dataKey="RMSE" stroke="#f59e0b" strokeWidth={2} dot />
              <Line yAxisId="right" type="monotone" dataKey="Accuracy" stroke="#10b981" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Predicted</th>
              <th className="px-4 py-3">Actual</th>
              <th className="px-4 py-3">Error</th>
              <th className="px-4 py-3">|Error|</th>
              <th className="px-4 py-3">Direction</th>
              <th className="px-4 py-3">Actual Dir</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Hit</th>
            </tr>
          </thead>
          <tbody>
            {data.samples.map((s, idx) => (
              <tr key={`${s.target_timestamp}-${idx}`} className="border-t border-slate-100">
                <td className="whitespace-nowrap px-4 py-3">{new Date(s.target_timestamp).toLocaleString()}</td>
                <td className="px-4 py-3">{s.predicted_index.toFixed(2)}</td>
                <td className="px-4 py-3">{s.actual_index.toFixed(2)}</td>
                <td className={`px-4 py-3 ${s.error >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {s.error >= 0 ? '+' : ''}
                  {s.error.toFixed(2)}
                </td>
                <td className="px-4 py-3">{s.abs_error.toFixed(2)}</td>
                <td className="px-4 py-3">{s.direction}</td>
                <td className="px-4 py-3">{s.actual_direction}</td>
                <td className="px-4 py-3">
                  {s.source === 'backfill' ? (
                    <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">Backfilled</span>
                  ) : (
                    <span className="text-xs text-slate-500">Live</span>
                  )}
                </td>
                <td className={`px-4 py-3 font-medium ${s.direction_correct ? 'text-green-600' : 'text-red-600'}`}>
                  {s.direction_correct ? 'Yes' : 'No'}
                </td>
              </tr>
            ))}
            {data.samples.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                  No matured outcomes yet. Historical performance appears once predictions are compared with observed
                  index values.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-end gap-2 text-sm">
        <button
          className="rounded border border-slate-300 px-2 py-1 disabled:opacity-50"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          Prev
        </button>
        <span className="text-slate-500">
          Page {page + 1} · showing {data.samples.length} of {data.sample_total}
        </span>
        <button
          className="rounded border border-slate-300 px-2 py-1 disabled:opacity-50"
          onClick={() => setPage((p) => p + 1)}
          disabled={(page + 1) * limit >= data.sample_total}
        >
          Next
        </button>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
