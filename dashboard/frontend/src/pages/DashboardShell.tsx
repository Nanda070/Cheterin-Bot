import { useAuth } from '../context/AuthContext'
import { logout } from '../api/client'

const SECTIONS = [
  'Feedback и тикеты',
  'Конструктор кнопок и эмбедов',
  'События и голосования',
  'Lockdown и модерация',
  'Участники и роли',
  'Конфигурация',
]

export function DashboardShell() {
  const { user, refresh } = useAuth()

  const handleLogout = async () => {
    await logout()
    await refresh()
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <aside className="w-64 border-r border-slate-800 p-4">
        <nav className="flex flex-col gap-2">
          {SECTIONS.map((section) => (
            <div key={section} className="rounded-md px-3 py-2 text-slate-400">
              {section} <span className="text-xs">(скоро)</span>
            </div>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">
        <div className="flex items-center justify-between">
          <span>Вы вошли как {user?.username}</span>
          <button onClick={handleLogout} className="rounded-md bg-slate-800 px-4 py-2">
            Выйти
          </button>
        </div>
      </main>
    </div>
  )
}
