import type { ReactNode } from 'react'

export default function KpiCard({
  title,
  value,
  subtitle,
  accent = 'text-slate-900',
  children,
}: {
  title: string
  value: string | number
  subtitle?: string
  accent?: string
  children?: ReactNode
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{title}</div>
      <div className={`mt-1 text-2xl font-bold ${accent}`}>{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-500">{subtitle}</div>}
      {children}
    </div>
  )
}
