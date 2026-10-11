import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { HistoryItem } from '../types'

export default function IndexLineChart({ items }: { items: HistoryItem[] }) {
  const ordered = [...items].sort(
    (a, b) => new Date(a.target_timestamp).getTime() - new Date(b.target_timestamp).getTime(),
  )
  const data = ordered.map((item, idx) => ({
    i: idx,
    label: new Date(item.target_timestamp).toLocaleDateString(undefined, {
      day: 'numeric',
      month: 'short',
    }),
    Actual: item.actual_index,
    Predicted: item.predicted_index,
  }))

  let lastActualIdx = -1
  ordered.forEach((item, idx) => {
    if (item.actual_index != null) lastActualIdx = idx
  })

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 20, right: 24, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="i"
          type="number"
          domain={['dataMin', 'dataMax']}
          tickFormatter={(i: number) => data[i]?.label ?? ''}
          tickCount={6}
        />
        <YAxis domain={['auto', 'auto']} width={60} />
        <Tooltip labelFormatter={(i) => data[i as number]?.label ?? i} />
        <Legend />
        {lastActualIdx >= 0 && lastActualIdx < data.length - 1 && (
          <ReferenceArea
            x1={lastActualIdx}
            x2={data.length - 1}
            fill="#93c5fd"
            fillOpacity={0.18}
            label={{ value: 'Prediction window', position: 'insideTop', fontSize: 11, fill: '#2563eb' }}
          />
        )}
        <Line type="monotone" dataKey="Actual" stroke="#0ea5e9" strokeWidth={2} dot={false} connectNulls />
        <Line
          type="monotone"
          dataKey="Predicted"
          stroke="#6366f1"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
