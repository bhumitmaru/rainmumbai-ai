import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  if (!user) return null

  const rows = [
    { label: 'Full Name', value: user.full_name },
    { label: 'Email', value: user.email },
    { label: 'Contact Number', value: user.contact_number },
    { label: 'Role', value: user.role },
    { label: 'Member Since', value: new Date(user.created_at).toLocaleDateString() },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-800">Profile</h1>
      <div className="max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-navy-900 text-xl font-bold text-white">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="text-lg font-bold text-slate-800">{user.full_name}</div>
            <div className="text-sm text-slate-500">{user.email}</div>
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {rows.map((r) => (
            <div key={r.label} className="flex justify-between py-3">
              <span className="text-sm text-slate-500">{r.label}</span>
              <span className="text-sm font-medium text-slate-800">{r.value}</span>
            </div>
          ))}
        </div>
        <button
          onClick={handleLogout}
          className="mt-5 w-full rounded-lg bg-red-600 py-2.5 font-medium text-white hover:bg-red-700"
        >
          Logout
        </button>
      </div>
    </div>
  )
}
