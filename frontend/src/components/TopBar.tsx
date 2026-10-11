import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function TopBar() {
  const { user } = useAuth()
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex items-center gap-3">
        <span className="rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-700">
          📍 Mumbai, India
        </span>
        <span className="text-xs text-slate-500">
          {now.toLocaleString(undefined, {
            dateStyle: 'medium',
            timeStyle: 'medium',
          })}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="text-sm font-medium text-slate-800">{user?.full_name}</div>
          <div className="text-xs text-slate-500">{user?.role}</div>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-navy-900 text-sm font-semibold text-white">
          {user?.full_name?.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  )
}
