import {
  Broom,
  Clock,
  Gear,
  LockKeyOpen,
  Prohibit,
  ShieldCheck,
  ShieldStar,
  ShieldWarning,
  SignOut,
  Siren,
  SpeakerSimpleSlash,
  SpeakerSimpleX,
  UserCheck,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  activateLockdown,
  deactivateLockdown,
  fetchLockdownStatus,
  fetchModerationLog,
  type LockdownStatus,
  type ModerationLogEntry,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { useT } from '../context/LanguageContext'
import { AntiRaidPage } from './AntiRaid'
import { AntiSpamPage } from './AntiSpam'
import { TempbanPage } from './Tempban'
import { VerificationPage } from './Verification'

type Tab = 'moderation' | 'settings' | 'antiraid' | 'antispam' | 'tempban' | 'verification'

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
  verification_expired: UserCheck,
}

export function LockdownPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('moderation')
  const [status, setStatus] = useState<LockdownStatus | null>(null)
  const [confirming, setConfirming] = useState<'activate' | 'deactivate' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)

  const tabs = useMemo(
    () =>
      [
        { key: 'moderation' as const, label: t('lockdown.tab.moderation'), icon: ShieldWarning },
        { key: 'settings' as const, label: t('lockdown.tab.settings'), icon: Gear },
        { key: 'antiraid' as const, label: t('lockdown.tab.antiraid'), icon: ShieldStar },
        { key: 'antispam' as const, label: t('lockdown.tab.antispam'), icon: Warning },
        { key: 'tempban' as const, label: t('lockdown.tab.tempban'), icon: Clock },
        { key: 'verification' as const, label: t('lockdown.tab.verification'), icon: UserCheck },
      ] as const,
    [t],
  )

  const typeLabel = (type: ModerationLogEntry['type']) => t(`lockdown.type.${type}`)

  const reload = () => {
    fetchLockdownStatus()
      .then((s) => {
        setStatus(s)
        setError('')
      })
      .catch(() => setError(t('lockdown.errorStatus')))
  }

  useEffect(reload, [t])
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
    } catch (err) {
      setError(formatApiError(err, t, 'lockdown.errorOperation'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-1 border-b border-border">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setTab(key)
              setError('')
            }}
            className={`flex cursor-pointer items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'settings' && (
        <ModuleConfigPanel
          variant="moderation"
          title={t('config.section.moderation')}
          intro={t('lockdown.settingsIntro')}
        />
      )}
      {tab === 'antiraid' && <AntiRaidPage />}
      {tab === 'antispam' && <AntiSpamPage />}
      {tab === 'tempban' && <TempbanPage />}
      {tab === 'verification' && <VerificationPage />}

      {tab === 'moderation' && !status && (
        <p className="text-sm text-muted">{error || t('common.loading')}</p>
      )}

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
                  {t('lockdown.antispamTitle', {
                    status: status.active ? t('lockdown.statusOn') : t('lockdown.statusOff'),
                  })}
                </h1>
                <p className="text-sm text-muted">
                  {status.active
                    ? t('lockdown.rolesInBackup', { count: status.role_count })
                    : t('lockdown.rolesNormal')}
                </p>
              </div>
            </div>

            {error && <p className="mt-3 text-sm text-danger">{error}</p>}

            <div className="mt-5 flex gap-2">
              {status.active ? (
                <Button variant="secondary" onClick={() => setConfirming('deactivate')} disabled={busy}>
                  {t('lockdown.deactivate')}
                </Button>
              ) : (
                <Button variant="danger" onClick={() => setConfirming('activate')} disabled={busy}>
                  {t('lockdown.activate')}
                </Button>
              )}
            </div>

            <Modal
              open={confirming !== null}
              title={
                confirming === 'activate'
                  ? t('lockdown.modal.activateTitle')
                  : t('lockdown.modal.deactivateTitle')
              }
              onClose={() => setConfirming(null)}
            >
              <p className="mb-4 text-sm text-muted">
                {confirming === 'activate'
                  ? t('lockdown.modal.activateBody')
                  : t('lockdown.modal.deactivateBody')}
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setConfirming(null)} disabled={busy}>
                  {t('common.cancel')}
                </Button>
                <Button variant="danger" onClick={confirm} disabled={busy}>
                  {busy ? t('common.confirming') : t('common.confirm')}
                </Button>
              </div>
            </Modal>
          </Card>

          <Card className="animate-fade-in-up">
            <h2 className="font-semibold text-foreground">{t('lockdown.activityTitle')}</h2>
            {activity === null && <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>}
            {activity !== null && activity.length === 0 && (
              <p className="mt-2 text-sm text-muted">{t('lockdown.activityEmpty')}</p>
            )}
            {activity !== null && activity.length > 0 && (
              <ul className="mt-3 flex flex-col gap-3">
                {activity.map((entry, index) => {
                  const Icon = TYPE_ICON[entry.type]
                  return (
                    <li
                      key={index}
                      className="flex items-start gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0"
                    >
                      <Icon size={18} className="mt-0.5 shrink-0 text-muted" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-foreground">
                          <span className="font-medium">{typeLabel(entry.type)}</span> —{' '}
                          <span>{entry.user_display}</span>
                        </p>
                        <p className="text-xs text-muted">{entry.reason}</p>
                        <p className="text-xs text-muted">
                          <span>{entry.moderator_display ?? t('lockdown.moderatorAuto')}</span> ·{' '}
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
