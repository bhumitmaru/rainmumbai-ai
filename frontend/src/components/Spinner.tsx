export default function Spinner({ label = 'Loading…' }: { label?: string }) {
  return <div className="flex items-center justify-center py-10 text-slate-400">{label}</div>
}
