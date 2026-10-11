import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/predictions', label: 'Predictions', icon: '🔮' },
  { to: '/history', label: 'Historical Analysis', icon: '📈' },
  { to: '/performance', label: 'Performance', icon: '🎯' },
  { to: '/profitability', label: 'Profitability', icon: '💰' },
  { to: '/profile', label: 'Profile', icon: '👤' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const items = user?.role === 'admin' ? [...NAV, { to: '/admin', label: 'Admin', icon: '🛡️' }] : NAV

  return (
    <aside className="flex w-60 shrink-0 flex-col bg-navy-900 text-white">
      <div className="flex items-center gap-3 px-5 py-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500 text-xl">🌧️</div>
        <div>
          <div className="text-lg font-bold leading-tight">RainMumbai AI</div>
          <div className="text-xs text-slate-400">Index Prediction</div>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-3">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                isActive ? 'bg-sky-600 font-medium text-white' : 'text-slate-300 hover:bg-navy-800'
              }`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-300 hover:bg-navy-800"
        >
          <span>🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}
