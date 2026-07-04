import {
  CalendarCheck,
  ChatCircleText,
  Clock,
  Prohibit,
  ShieldCheck,
  ShieldWarning,
  SignOut,
  UsersThree,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchEvents,
  fetchFeedbackCases,
  fetchLockdownStatus,
  fetchMembers,
  fetchModerationLog,
  type LockdownStatus,
  type ModerationLogEntry,
} from '../api/client'
import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'

const TYPE_ICON: Record<ModerationLogEntry['type'], typeof Warning> = {
  spam_punish: Warning,
  tempban: Clock,
  manual_ban: Prohibit,
  manual_kick: SignOut,
}

const TYPE_LABEL: Record<ModerationLogEntry['type'], string> = {
  spam_punish: 'Анти-спам',
  tempban: 'Tempban',
  manual_ban: 'Бан (дашборд)',
  manual_kick: 'Кик (дашборд)',
}

export function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [feedbackCount, setFeedbackCount] = useState<number | null>(null)
  const [feedbackError, setFeedbackError] = useState('')

  const [eventsCount, setEventsCount] = useState<number | null>(null)
  const [eventsError, setEventsError] = useState('')

  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)
  const [activityError, setActivityError] = useState('')

  const [lockdownStatus, setLockdownStatus] = useState<LockdownStatus | null>(null)
  const [lockdownError, setLockdownError] = useState('')

  const [memberCount, setMemberCount] = useState<number | null>(null)
  const [memberError, setMemberError] = useState('')

  useEffect(() => {
    fetchFeedbackCases('pending')
      .then((cases) => setFeedbackCount(cases.length))
      .catch(() => setFeedbackError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchEvents('open')
      .then((events) => setEventsCount(events.length))
      .catch(() => setEventsError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchModerationLog()
      .then(setActivity)
      .catch(() => setActivityError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchLockdownStatus()
      .then(setLockdownStatus)
      .catch(() => setLockdownError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchMembers('', 1, 1)
      .then((page) => setMemberCount(page.total))
      .catch(() => setMemberError('Не удалось загрузить'))
  }, [])

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold text-foreground">Добро пожаловать, {user?.username}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/feedback')}>
          <div className="flex items-center gap-2 text-foreground">
            <ChatCircleText size={20} className="text-primary" />
            <h2 className="font-semibold">Feedback</h2>
          </div>
          {feedbackError && <p className="mt-2 text-sm text-danger">{feedbackError}</p>}
          {!feedbackError && feedbackCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!feedbackError && feedbackCount !== null && (
            <p className="mt-2 text-sm text-muted">
              {feedbackCount === 0 ? 'Нет ожидающих' : `Ожидают решения: ${feedbackCount}`}
            </p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/events')}>
          <div className="flex items-center gap-2 text-foreground">
            <CalendarCheck size={20} className="text-primary" />
            <h2 className="font-semibold">События</h2>
          </div>
          {eventsError && <p className="mt-2 text-sm text-danger">{eventsError}</p>}
          {!eventsError && eventsCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!eventsError && eventsCount !== null && (
            <p className="mt-2 text-sm text-muted">Активных событий: {eventsCount}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            <ShieldWarning size={20} className="text-primary" />
            <h2 className="font-semibold">Модерация</h2>
          </div>
          {activityError && <p className="mt-2 text-sm text-danger">{activityError}</p>}
          {!activityError && activity === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!activityError && activity !== null && activity.length === 0 && (
            <p className="mt-2 text-sm text-muted">Активности пока нет.</p>
          )}
          {!activityError && activity !== null && activity.length > 0 && (
            <ul className="mt-2 flex flex-col gap-1">
              {activity.slice(0, 3).map((entry, index) => {
                const Icon = TYPE_ICON[entry.type]
                return (
                  <li key={index} className="flex items-center gap-2 text-sm text-muted">
                    <Icon size={14} className="shrink-0" />
                    <span className="truncate">
                      {TYPE_LABEL[entry.type]} — {entry.user_display}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            {lockdownStatus?.active ? (
              <ShieldWarning size={20} weight="fill" className="text-danger" />
            ) : (
              <ShieldCheck size={20} weight="fill" className="text-success" />
            )}
            <h2 className="font-semibold">Антиспам</h2>
          </div>
          {lockdownError && <p className="mt-2 text-sm text-danger">{lockdownError}</p>}
          {!lockdownError && lockdownStatus === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!lockdownError && lockdownStatus !== null && (
            <p className="mt-2 text-sm text-muted">{lockdownStatus.active ? 'ВКЛЮЧЁН' : 'ВЫКЛЮЧЕН'}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/members')}>
          <div className="flex items-center gap-2 text-foreground">
            <UsersThree size={20} className="text-primary" />
            <h2 className="font-semibold">Участники</h2>
          </div>
          {memberError && <p className="mt-2 text-sm text-danger">{memberError}</p>}
          {!memberError && memberCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!memberError && memberCount !== null && (
            <p className="mt-2 text-sm text-muted">Участников: {memberCount}</p>
          )}
        </Card>
      </div>
    </div>
  )
}
