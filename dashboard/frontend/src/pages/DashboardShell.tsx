import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { logout } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Card } from '../components/ui/Card'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'

interface Section {
  label: string
  icon: Icon
}

const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack },
  { label: 'События и голосования', icon: CalendarCheck },
  { label: 'Lockdown и модерация', icon: ShieldWarning },
  { label: 'Участники и роли', icon: UsersThree },
  { label: 'Конфигурация', icon: GearSix },
]

export function DashboardShell() {
  const { user, refresh } = useAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
      await refresh()
    } catch (error) {
      console.error('Failed to log out:', error)
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-2 text-foreground">
          <Sparkle size={20} weight="fill" className="text-primary" />
          <span className="font-semibold">Панель управления ботом</span>
        </div>

        <Dropdown
          trigger={
            <span className="flex items-center gap-2 rounded-control px-2 py-1.5 hover:bg-surface-hover">
              {user?.avatar ? (
                <img src={user.avatar} alt="" className="h-7 w-7 rounded-full" />
              ) : (
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                  {user?.username?.slice(0, 1).toUpperCase()}
                </span>
              )}
              <span className="text-sm text-foreground">{user?.username}</span>
            </span>
          }
        >
          <DropdownItem onClick={handleLogout} danger>
            <SignOut size={16} />
            {isLoggingOut ? 'Выходим…' : 'Выйти'}
          </DropdownItem>
        </Dropdown>
      </header>

      <div className="flex flex-1">
        <aside className="w-72 shrink-0 border-r border-border p-4">
          <nav className="flex flex-col gap-2">
            {SECTIONS.map(({ label, icon: SectionIcon }, index) => (
              <Card
                key={label}
                interactive
                className="animate-fade-in-up flex items-center justify-between gap-3 !rounded-control !p-3"
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <span className="flex items-center gap-3 text-sm text-foreground">
                  <SectionIcon size={18} className="text-muted" />
                  {label}
                </span>
                <span className="rounded-full bg-surface-hover px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted">
                  скоро
                </span>
              </Card>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <Card className="animate-fade-in-up max-w-2xl">
            <h1 className="text-lg font-semibold text-foreground">
              Добро пожаловать, {user?.username}
            </h1>
            <p className="mt-2 text-sm text-muted">
              Фундамент панели готов: вход через Discord, проверка прав и каркас разделов.
              Функциональность модерации появится в следующих фазах — разделы слева уже отражают,
              что будет добавлено.
            </p>
          </Card>
        </main>
      </div>
    </div>
  )
}
