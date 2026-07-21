import {
  ArrowsLeftRight,
  Broadcast,
  CalendarCheck,
  Car,
  Confetti,
  ChartBar,
  ChartLine,
  ChatCircleText,
  ClipboardText,
  Coins,
  Crown,
  DiceThree,
  FilmSlate,
  GearSix,
  Headset,
  House,
  Lightbulb,
  ListMagnifyingGlass,
  Megaphone,
  Package,
  Shield,
  ShieldWarning,
  SignOut,
  Skull,
  Sparkle,
  Stack,
  Ticket,
  TrendUp,
  Trophy,
  Users,
  UsersThree,
  Vault,
  Wrench,
  type Icon,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { logout } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'

interface Section {
  label: string
  icon: Icon
  to: string
  mainGuildOnly?: boolean
}

interface NavGroup {
  title: string
  icon: Icon
  items: Section[]
  superAdminOnly?: boolean
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Активность',
    icon: TrendUp,
    items: [
      { label: 'Рейтинг участников', icon: ChartBar, to: '/levels' },
      { label: 'Экономика', icon: Coins, to: '/economy' },
      { label: 'Казино', icon: DiceThree, to: '/casino' },
      { label: 'Статистика войса', icon: ChartLine, to: '/voice-stats' },
    ],
  },
  {
    title: 'GTA5RP',
    icon: Car,
    items: [
      { label: 'Семья', icon: House, to: '/family' },
      { label: 'Поставки', icon: Package, to: '/supply' },
    ],
  },
  {
    title: 'Сообщество',
    icon: Users,
    items: [
      { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
      { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
      { label: 'Сетки', icon: Trophy, to: '/brackets' },
      { label: 'Мафия', icon: Skull, to: '/mafia' },
      { label: 'Бункер', icon: Vault, to: '/bunker' },
      { label: 'Развлечения', icon: Confetti, to: '/fun' },
      { label: 'Приватные комнаты', icon: Headset, to: '/voice-rooms' },
    ],
  },
  {
    title: 'Контент',
    icon: FilmSlate,
    items: [
      { label: 'Кнопки и эмбеды', icon: Stack, to: '/reaction-roles' },
      { label: 'Публикации и подписки', icon: Broadcast, to: '/streams' },
      { label: 'Ежедневная рубрика', icon: Lightbulb, to: '/daily-topic' },
    ],
  },
  {
    title: 'Администрирование',
    icon: Wrench,
    items: [
      { label: 'Логирование', icon: ListMagnifyingGlass, to: '/serverlog' },
      { label: 'Модерация', icon: ShieldWarning, to: '/lockdown' },
      { label: 'Автомодерация', icon: Shield, to: '/automod' },
      { label: 'Участники и роли', icon: UsersThree, to: '/members' },
      { label: 'Аудит дашборда', icon: ClipboardText, to: '/audit' },
      { label: 'Конфигурация', icon: GearSix, to: '/config' },
      { label: 'Тикеты CTD', icon: Ticket, to: '/ctd', mainGuildOnly: true },
    ],
  },
  {
    title: 'Супер-админ',
    icon: Crown,
    superAdminOnly: true,
    items: [
      { label: 'Серверы бота', icon: Crown, to: '/superadmin' },
      { label: 'Ретрансляция новостей', icon: Megaphone, to: '/news' },
    ],
  },
]

export function DashboardShell() {
  const { user, refresh } = useAuth()
  const navigate = useNavigate()
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
    'flex items-center gap-2.5 rounded-control border-l-2 px-2.5 py-2 text-sm transition-colors duration-200 ease-out'

  return (
    <div className="flex h-dvh flex-col">
      <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4">
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
          <DropdownItem onClick={() => navigate('/servers')}>
            <ArrowsLeftRight size={16} />
            Сменить сервер
          </DropdownItem>
          <DropdownItem onClick={handleLogout} danger>
            <SignOut size={16} />
            {isLoggingOut ? 'Выходим…' : 'Выйти'}
          </DropdownItem>
        </Dropdown>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-border p-4">
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
          <nav className="flex flex-col gap-5">
            {NAV_GROUPS.filter((group) => !group.superAdminOnly || user?.is_super_admin).map((group, groupIndex) => (
              <div key={group.title} className="animate-fade-in-up" style={{ animationDelay: `${groupIndex * 60}ms` }}>
                <p className="mb-1.5 flex items-center gap-1.5 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
                  <group.icon size={13} weight="bold" className="shrink-0" />
                  {group.title}
                </p>
                <div className="flex flex-col gap-0.5">
                  {group.items
                    .filter((item) => !item.mainGuildOnly || user?.is_main_guild)
                    .map(({ label, icon: SectionIcon, to }) => (
                    <NavLink
                      key={label}
                      to={to}
                      className={({ isActive }) =>
                        `${itemBase} cursor-pointer ${
                          isActive
                            ? 'border-primary bg-primary-muted font-medium text-foreground'
                            : 'border-transparent text-muted hover:bg-surface-hover hover:text-foreground'
                        }`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <SectionIcon size={17} weight={isActive ? 'fill' : 'regular'} className={`shrink-0 ${isActive ? 'text-primary' : ''}`} />
                          {label}
                        </>
                      )}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
