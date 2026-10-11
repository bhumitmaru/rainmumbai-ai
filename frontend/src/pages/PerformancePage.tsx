import { useEffect, useState } from 'react'
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
import type { Performance, PerformanceSample } from '../types'

function fmtMetric(value: number | null, digits = 2) {
  return value == null ? '—' : value.toFixed(digits)
}

function fmtPct(value: number | null) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

function errorChart(samples: PerformanceSample[]) {
  return samples.map((s) => ({
    label: new Date(s.target_timestamp).toLocaleDateString(undefined, {
      day: 'numeric',
      month: 'short',
    }),
    error: s.error,
    absError: s.abs_error,
  }))
}

function rollingAccuracy(samples: PerformanceSample[]) {
  let hits = 0
  return samples.map((s, idx) => {
    if (s.direction_correct) hits += 1
    return {
      label: new Date(s.target_timestamp).toLocaleDateString(undefined, {
        day: 'numeric',
        month: 'short',
      }),
      accuracy: Number(((hits / (idx + 1)) * 100).toFixed(1)),
    }
  })
}

export default function PerformancePage() {
  const [data, setData] = useState<Performance | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get('/performance')
      .then((r) => setData(r.data as Performance))
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load performance'))
  }, [])

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
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard title="MAE" value={fmtMetric(data.mae)} subtitle="Mean absolute error" />
        <KpiCard title="RMSE" value={fmtMetric(data.rmse)} subtitle="Root mean square error" />
        <KpiCard title="Direction Accuracy" value={fmtPct(data.direction_accuracy)} subtitle="Correct direction" />
        <KpiCard title="Direction F1" value={fmtPct(data.direction_f1)} subtitle="Macro-F1" />
        <KpiCard title="Samples" value={data.sample_count} subtitle="Matched outcomes" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-800">Prediction error over time</h3>
          {data.samples.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">
              No evaluated samples yet. Error series appear once predictions are matched to observed outcomes.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={errorChart(data.samples)} margin={{ top: 5, right: 12, left: 0, bottom: 0 }}>
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
          {data.samples.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">
              Direction accuracy builds as outcomes are recorded.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={rollingAccuracy(data.samples)} margin={{ top: 5, right: 12, left: 0, bottom: 0 }}>
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
                <td className={`px-4 py-3 font-medium ${s.direction_correct ? 'text-green-600' : 'text-red-600'}`}>
                  {s.direction_correct ? 'Yes' : 'No'}
                </td>
              </tr>
            ))}
            {data.samples.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                  No matured outcomes yet. Historical performance appears once predictions are compared with observed
                  index values.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
