import {
  Broadcast,
  CalendarCheck,
  ChartBar,
  ChartLine,
  ChatCircleText,
  ClipboardText,
  GearSix,
  HandWaving,
  Headset,
  ListMagnifyingGlass,
  Megaphone,
  Package,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  Trophy,
  UserCirclePlus,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { logout } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'

interface Section {
  label: string
  icon: Icon
  to: string
}

interface NavGroup {
  title: string
  items: Section[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Активность',
    items: [
      { label: 'Рейтинг участников', icon: ChartBar, to: '/levels' },
      { label: 'Статистика войса', icon: ChartLine, to: '/voice-stats' },
    ],
  },
  {
    title: 'Сообщество',
    items: [
      { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
      { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
      { label: 'Сетки', icon: Trophy, to: '/brackets' },
      { label: 'Поставки', icon: Package, to: '/supply' },
      { label: 'Приватные комнаты', icon: Headset, to: '/voice-rooms' },
    ],
  },
  {
    title: 'Контент',
    items: [
      { label: 'Кнопки и эмбеды', icon: Stack, to: '/reaction-roles' },
      { label: 'Публикации и подписки', icon: Broadcast, to: '/streams' },
      { label: 'Ретрансляция новостей', icon: Megaphone, to: '/news' },
      { label: 'Приветствие и прощание', icon: HandWaving, to: '/welcome' },
      { label: 'Авто-роли', icon: UserCirclePlus, to: '/auto-roles' },
    ],
  },
  {
    title: 'Администрирование',
    items: [
      { label: 'Логирование', icon: ListMagnifyingGlass, to: '/serverlog' },
      { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
      { label: 'Участники и роли', icon: UsersThree, to: '/members' },
      { label: 'Аудит дашборда', icon: ClipboardText, to: '/audit' },
      { label: 'Конфигурация', icon: GearSix, to: '/config' },
    ],
  },
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

  const itemBase =
    'flex items-center gap-2.5 rounded-control px-2.5 py-2 text-sm transition-colors duration-200 ease-out'

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-foreground">
            <Sparkle size={20} weight="fill" className="text-primary" />
            <span className="font-semibold">Cheterin</span>
          </Link>
          <nav className="hidden items-center gap-3 text-sm text-muted sm:flex">
            <Link to="/docs" className="transition-colors hover:text-foreground">
              Документация
            </Link>
            <Link to="/terms" className="transition-colors hover:text-foreground">
              Условия
            </Link>
            <Link to="/privacy" className="transition-colors hover:text-foreground">
              Приватность
            </Link>
          </nav>
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
          <div className="mb-4 flex items-center gap-3 rounded-control border border-border bg-surface p-3">
            {user?.avatar ? (
              <img src={user.avatar} alt="" className="h-9 w-9 rounded-full" />
            ) : (
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-muted text-sm font-semibold text-primary">
                {user?.username?.slice(0, 1).toUpperCase()}
              </span>
            )}
            <span className="truncate text-sm font-medium text-foreground">{user?.username}</span>
          </div>
          <nav className="flex flex-col gap-4">
            {NAV_GROUPS.map((group, groupIndex) => (
              <div key={group.title} className="animate-fade-in-up" style={{ animationDelay: `${groupIndex * 60}ms` }}>
                <p className="mb-1 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
                  {group.title}
                </p>
                <div className="flex flex-col gap-0.5">
                  {group.items.map(({ label, icon: SectionIcon, to }) => (
                    <NavLink
                      key={label}
                      to={to}
                      className={({ isActive }) =>
                        `${itemBase} cursor-pointer ${
                          isActive
                            ? 'bg-primary-muted font-medium text-foreground'
                            : 'text-muted hover:bg-surface-hover hover:text-foreground'
                        }`
                      }
                    >
                      <SectionIcon size={17} className="shrink-0" />
                      {label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
