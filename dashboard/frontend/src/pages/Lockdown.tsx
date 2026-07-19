import { Broom, Clock, HandWaving, LockKeyOpen, Prohibit, ShieldCheck, ShieldStar, ShieldWarning, SignOut, Siren, SpeakerSimpleSlash, SpeakerSimpleX, UserCheck, UserCirclePlus, Warning } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  activateLockdown,
  deactivateLockdown,
  fetchLockdownStatus,
  fetchModerationLog,
  type LockdownStatus,
  type ModerationLogEntry,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { AntiRaidPage } from './AntiRaid'
import { AutoRolesPage } from './AutoRoles'
import { VerificationPage } from './Verification'
import { WelcomePage } from './Welcome'

type Tab = 'moderation' | 'welcome' | 'auto-roles' | 'antiraid' | 'verification'

const TABS: { key: Tab; label: string; icon: typeof ShieldWarning }[] = [
  { key: 'moderation', label: 'Lockdown и лог', icon: ShieldWarning },
  { key: 'welcome', label: 'Приветствие и прощание', icon: HandWaving },
  { key: 'auto-roles', label: 'Авто-роли', icon: UserCirclePlus },
  { key: 'antiraid', label: 'Антирейд', icon: ShieldStar },
  { key: 'verification', label: 'Верификация', icon: UserCheck },
]

const TYPE_ICON: Record<ModerationLogEntry['type'], typeof Warning> = {
  spam_punish: Warning,
  tempban: Clock,
  manual_ban: Prohibit,
  manual_kick: SignOut,
  warn_manual: Warning,
  command_ban: Prohibit,
  command_kick: SignOut,
  command_mute: SpeakerSimpleX,
  command_unmute: SpeakerSimpleSlash,
  command_unban: LockKeyOpen,
  command_clear: Broom,
  antiraid_trigger: Siren,
  verification_pass: UserCheck,
}

const TYPE_LABEL: Record<ModerationLogEntry['type'], string> = {
  spam_punish: 'Анти-спам',
  tempban: 'Tempban',
  manual_ban: 'Бан (дашборд)',
  manual_kick: 'Кик (дашборд)',
  warn_manual: 'Предупреждение',
  command_ban: 'Бан (команда)',
  command_kick: 'Кик (команда)',
  command_mute: 'Таймаут (команда)',
  command_unmute: 'Снятие таймаута (команда)',
  command_unban: 'Разбан (команда)',
  command_clear: 'Очистка чата (команда)',
  antiraid_trigger: 'Антирейд сработал',
  verification_pass: 'Верификация пройдена',
}

export function LockdownPage() {
  const [tab, setTab] = useState<Tab>('moderation')
  const [status, setStatus] = useState<LockdownStatus | null>(null)
  const [confirming, setConfirming] = useState<'activate' | 'deactivate' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)

  const reload = () => {
    fetchLockdownStatus()
      .then((s) => {
        setStatus(s)
        setError('')
      })
      .catch(() => setError('Не удалось получить статус'))
  }

  useEffect(reload, [])
  useEffect(() => {
    fetchModerationLog()
      .then(setActivity)
      .catch(() => setActivity([]))
  }, [])

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      if (confirming === 'activate') await activateLockdown()
      if (confirming === 'deactivate') await deactivateLockdown()
      setConfirming(null)
      reload()
    } catch {
      setError('Операция не удалась — подробности в логах бота')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <div className="flex gap-1 border-b border-border">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'welcome' && <WelcomePage />}
      {tab === 'auto-roles' && <AutoRolesPage />}
      {tab === 'antiraid' && <AntiRaidPage />}
      {tab === 'verification' && <VerificationPage />}

      {tab === 'moderation' && !status && <p className="text-sm text-muted">{error || 'Загрузка…'}</p>}
      {tab === 'moderation' && status && (
    <div className="flex max-w-xl flex-col gap-4">
      <Card className="animate-fade-in-up">
        <div className="flex items-center gap-3">
          {status.active ? (
            <ShieldWarning size={28} weight="fill" className="text-danger" />
          ) : (
            <ShieldCheck size={28} weight="fill" className="text-success" />
          )}
          <div>
            <h1 className="font-semibold text-foreground">
              Антиспам-режим: {status.active ? 'ВКЛЮЧЁН' : 'ВЫКЛЮЧЕН'}
            </h1>
            <p className="text-sm text-muted">
              {status.active
                ? `Изменённых ролей в бэкапе: ${status.role_count}`
                : 'Все роли работают в обычном режиме.'}
            </p>
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-danger">{error}</p>}

        <div className="mt-5 flex gap-2">
          {status.active ? (
            <Button variant="secondary" onClick={() => setConfirming('deactivate')} disabled={busy}>
              Выключить антиспам
            </Button>
          ) : (
            <Button variant="danger" onClick={() => setConfirming('activate')} disabled={busy}>
              Включить антиспам
            </Button>
          )}
        </div>

        <Modal
          open={confirming !== null}
          title={confirming === 'activate' ? 'Включить антиспам-режим?' : 'Выключить антиспам-режим?'}
          onClose={() => setConfirming(null)}
        >
          <p className="mb-4 text-sm text-muted">
            {confirming === 'activate'
              ? 'У всех не-исключённых ролей будут сняты права massive mention, текущее состояние сохранится в бэкап.'
              : 'Права ролей будут восстановлены из бэкапа.'}
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setConfirming(null)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="danger" onClick={confirm} disabled={busy}>
              {busy ? 'Выполняем…' : 'Подтвердить'}
            </Button>
          </div>
        </Modal>
      </Card>

      <Card className="animate-fade-in-up">
        <h2 className="font-semibold text-foreground">Последняя активность</h2>
        {activity === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
        {activity !== null && activity.length === 0 && (
          <p className="mt-2 text-sm text-muted">Активности пока нет.</p>
        )}
        {activity !== null && activity.length > 0 && (
          <ul className="mt-3 flex flex-col gap-3">
            {activity.map((entry, index) => {
              const Icon = TYPE_ICON[entry.type]
              return (
                <li key={index} className="flex items-start gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                  <Icon size={18} className="mt-0.5 shrink-0 text-muted" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-foreground">
                      <span className="font-medium">{TYPE_LABEL[entry.type]}</span> — <span>{entry.user_display}</span>
                    </p>
                    <p className="text-xs text-muted">{entry.reason}</p>
                    <p className="text-xs text-muted">
                      <span>{entry.moderator_display ?? 'Автоматически'}</span> ·{' '}
                      <span>{new Date(entry.timestamp).toLocaleString()}</span>
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </Card>
    </div>
      )}
    </div>
  )
}
