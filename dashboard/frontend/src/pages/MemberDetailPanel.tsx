import { ClockCounterClockwise, Trash, Warning, X } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  banMember,
  createMemberWarn,
  deleteWarn,
  fetchCaseTimeline,
  fetchMemberDetail,
  fetchMemberWarns,
  fetchRoles,
  grantRole,
  kickMember,
  revokeRole,
  timeoutMember,
  type CaseTimeline,
  type CaseTimelineItem,
  type MemberDetail,
  type RoleInfo,
  type Warn,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { useLanguage, useT } from '../context/LanguageContext'

type PendingAction = 'ban' | 'kick' | 'warn' | 'timeout' | null

interface Props {
  memberId: string
  onClose: () => void
  onActionDone: () => void
}

function kindDotClass(kind: string): string {
  if (kind.includes('unban') || kind.includes('unmute')) return 'bg-emerald-500'
  if (kind.includes('ban') || kind === 'tempban') return 'bg-danger'
  if (kind.includes('kick')) return 'bg-orange-500'
  if (kind.includes('mute')) return 'bg-yellow-400'
  if (kind.startsWith('warn')) return 'bg-amber-500'
  if (kind.startsWith('automod') || kind === 'spam_punish' || kind === 'antiraid_trigger') {
    return 'bg-primary'
  }
  return 'bg-muted'
}

function kindLabel(kind: string, t: (key: string, params?: Record<string, string | number>) => string): string {
  const key = `members.caseTimeline.kind.${kind}`
  const translated = t(key)
  return translated === key ? kind : translated
}

export function MemberDetailPanel({ memberId, onClose, onActionDone }: Props) {
  const t = useT()
  const { lang } = useLanguage()
  const dateLocale = lang === 'ru' ? 'ru-RU' : 'en-US'
  const [detail, setDetail] = useState<MemberDetail | null>(null)
  const [assignable, setAssignable] = useState<RoleInfo[]>([])
  const [pending, setPending] = useState<PendingAction>(null)
  const [reason, setReason] = useState('')
  const [deleteDays, setDeleteDays] = useState<0 | 1 | 7>(0)
  const [timeoutDuration, setTimeoutDuration] = useState('1h')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [warns, setWarns] = useState<Warn[]>([])
  const [activeWarnCount, setActiveWarnCount] = useState(0)
  const [warnBusy, setWarnBusy] = useState(false)
  const [timeline, setTimeline] = useState<CaseTimeline | null>(null)

  const deleteMessageOptions = useMemo(
    () => [
      { id: '0', name: t('members.detail.deleteNone') },
      { id: '1', name: t('members.detail.delete1Day') },
      { id: '7', name: t('members.detail.delete7Days') },
    ],
    [t],
  )

  const reload = () => {
    fetchMemberDetail(memberId)
      .then(setDetail)
      .catch((err) => setError(formatApiError(err, t, 'members.detail.errorLoad')))
    fetchRoles()
      .then(setAssignable)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadRoles')))
    reloadWarns()
  }

  const reloadWarns = () => {
    fetchMemberWarns(memberId)
      .then((data) => {
        setWarns(data.warns)
        setActiveWarnCount(data.active_count)
      })
      .catch(() => {})
    reloadTimeline()
  }

  const reloadTimeline = () => {
    fetchCaseTimeline(memberId)
      .then(setTimeline)
      .catch(() => setTimeline(null))
  }

  useEffect(reload, [memberId, t])

  const confirmAction = async () => {
    if (!reason.trim()) {
      setError(t('members.detail.reasonRequired'))
      return
    }
    if (pending === 'timeout' && !timeoutDuration.trim()) {
      setError(t('members.detail.durationRequired'))
      return
    }
    setBusy(true)
    setError('')
    try {
      if (pending === 'ban') await banMember(memberId, reason.trim(), deleteDays)
      if (pending === 'kick') await kickMember(memberId, reason.trim())
      if (pending === 'timeout') {
        await timeoutMember(memberId, reason.trim(), timeoutDuration.trim())
        reloadTimeline()
      }
      if (pending === 'warn') {
        await createMemberWarn(memberId, reason.trim())
        reloadWarns()
      }
      setPending(null)
      setReason('')
      onActionDone()
      if (pending !== 'warn' && pending !== 'timeout') onClose()
    } catch {
      setError(t('members.detail.discordRejected'))
    } finally {
      setBusy(false)
    }
  }

  const removeWarn = async (warnId: number) => {
    setWarnBusy(true)
    try {
      await deleteWarn(warnId)
      reloadWarns()
    } catch {
      setError(t('members.detail.warnRemoveFailed'))
    } finally {
      setWarnBusy(false)
    }
  }

  const toggleRole = async (roleId: string, has: boolean) => {
    setBusy(true)
    setError('')
    try {
      if (has) await revokeRole(memberId, roleId)
      else await grantRole(memberId, roleId)
      reload()
    } catch {
      setError(t('members.detail.roleChangeFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!detail) {
    return (
      <Card className="animate-fade-in-up">
        <p className="text-sm text-muted">{error || t('common.loading')}</p>
      </Card>
    )
  }

  const memberRoleIds = new Set(detail.roles.map((r) => r.id))

  const modalTitle =
    pending === 'ban'
      ? t('members.detail.banTitle', { name: detail.display_name })
      : pending === 'kick'
        ? t('members.detail.kickTitle', { name: detail.display_name })
        : pending === 'timeout'
          ? t('members.detail.timeoutTitle', { name: detail.display_name })
          : t('members.detail.warnTitle', { name: detail.display_name })

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {detail.avatar && <img src={detail.avatar} alt="" className="h-12 w-12 rounded-full" />}
          <div>
            <h2 className="font-semibold text-foreground">{detail.display_name}</h2>
            <p className="text-xs text-muted">@{detail.username} · {detail.id}</p>
          </div>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          <X size={18} />
        </button>
      </div>

      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-muted">{t('members.detail.joinedAt')}</dt>
        <dd>{detail.joined_at ? new Date(detail.joined_at).toLocaleDateString(dateLocale) : t('common.none')}</dd>
        <dt className="text-muted">{t('members.detail.accountCreated')}</dt>
        <dd>{new Date(detail.created_at).toLocaleDateString(dateLocale)}</dd>
        <dt className="text-muted">{t('members.detail.invites')}</dt>
        <dd>
          {t('members.detail.inviteStats', {
            invites: detail.invite_stats.invites,
            joins: detail.invite_stats.joins,
            leaves: detail.invite_stats.leaves,
          })}
        </dd>
        <dt className="text-muted">{t('members.detail.feedbackCases')}</dt>
        <dd>{detail.feedback_case_count}</dd>
      </dl>

      <div>
        <h3 className="mb-2 text-sm font-medium text-muted">{t('members.detail.roles')}</h3>
        <div className="flex flex-wrap gap-1.5">
          {detail.roles.map((role) => (
            <button
              key={role.id}
              onClick={() => toggleRole(role.id, true)}
              disabled={busy}
              title={t('members.detail.removeRoleTitle')}
              className="cursor-pointer rounded-full border border-border px-2.5 py-0.5 text-xs transition-colors hover:border-danger hover:text-danger"
              style={{ color: role.color !== '#000000' ? role.color : undefined }}
            >
              {role.name} ×
            </button>
          ))}
          <Dropdown
            align="left"
            trigger={
              <span className="rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted hover:text-foreground">
                {t('members.detail.addRole')}
              </span>
            }
          >
            {assignable
              .filter((r) => !memberRoleIds.has(r.id))
              .map((role) => (
                <DropdownItem key={role.id} onClick={() => toggleRole(role.id, false)}>
                  {role.name}
                </DropdownItem>
              ))}
          </Dropdown>
        </div>
      </div>

      {!detail.is_bot && (
        <div>
          <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-muted">
            <Warning size={14} />
            {t('members.detail.warns', { count: activeWarnCount })}
          </h3>
          {warns.length === 0 ? (
            <p className="text-sm text-muted">{t('members.detail.noWarns')}</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {warns.map((w) => {
                const isActive = !w.removed && (!w.expires_at || w.expires_at > new Date().toISOString())
                return (
                  <li key={w.id} className="flex items-start justify-between gap-2 text-xs">
                    <span className={isActive ? 'text-foreground' : 'text-muted line-through'}>
                      #{w.id} — {w.reason}
                      <span className="ml-1 text-muted">({new Date(w.created_at).toLocaleDateString(dateLocale)})</span>
                    </span>
                    {isActive && (
                      <button
                        onClick={() => removeWarn(w.id)}
                        disabled={warnBusy}
                        title={t('members.detail.removeWarnTitle')}
                        className="shrink-0 cursor-pointer text-muted hover:text-danger"
                      >
                        <Trash size={14} />
                      </button>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}

      {!detail.is_bot && (
        <CaseTimelineSection timeline={timeline} dateLocale={dateLocale} t={t} />
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      {!detail.is_bot && (
        <div className="flex flex-wrap gap-2 border-t border-border pt-4">
          <Button variant="danger" onClick={() => setPending('ban')} disabled={busy}>
            {t('members.detail.ban')}
          </Button>
          <Button variant="secondary" onClick={() => setPending('kick')} disabled={busy}>
            {t('members.detail.kick')}
          </Button>
          <Button variant="secondary" onClick={() => setPending('timeout')} disabled={busy}>
            {t('members.detail.timeout')}
          </Button>
          <Button variant="secondary" onClick={() => setPending('warn')} disabled={busy}>
            {t('members.detail.warn')}
          </Button>
        </div>
      )}

      <Modal open={pending !== null} title={modalTitle} onClose={() => setPending(null)}>
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="mod-reason">
            {t('members.detail.reasonLabel')}
          </label>
          <input
            id="mod-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            placeholder={t('members.detail.reasonPlaceholder')}
          />
          {pending === 'ban' && (
            <>
              <label className="text-sm text-muted" htmlFor="mod-days">
                {t('members.detail.deleteMessages')}
              </label>
              <Select
                id="mod-days"
                value={String(deleteDays)}
                onChange={(id) => setDeleteDays(Number(id) as 0 | 1 | 7)}
                options={deleteMessageOptions}
              />
            </>
          )}
          {pending === 'timeout' && (
            <>
              <label className="text-sm text-muted" htmlFor="mod-timeout-duration">
                {t('members.detail.timeoutDuration')}
              </label>
              <input
                id="mod-timeout-duration"
                value={timeoutDuration}
                onChange={(e) => setTimeoutDuration(e.target.value)}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                placeholder={t('members.detail.timeoutDurationPlaceholder')}
              />
              <p className="text-xs text-muted">{t('members.detail.timeoutDurationHint')}</p>
            </>
          )}
          {error && <p className="text-sm text-danger">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setPending(null)} disabled={busy}>
              {t('common.cancel')}
            </Button>
            <Button
              variant={pending === 'warn' || pending === 'timeout' ? 'primary' : 'danger'}
              onClick={confirmAction}
              disabled={busy}
            >
              {busy ? t('common.confirming') : t('common.confirm')}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}

function CaseTimelineSection({
  timeline,
  dateLocale,
  t,
}: {
  timeline: CaseTimeline | null
  dateLocale: string
  t: (key: string, params?: Record<string, string | number>) => string
}) {
  const headerUser = timeline?.user
  const items: CaseTimelineItem[] = timeline?.items ?? []

  return (
    <div className="rounded-card border border-border bg-background/40 p-3">
      <div className="mb-3 flex items-center gap-3">
        {headerUser?.avatar ? (
          <img src={headerUser.avatar} alt="" className="h-9 w-9 rounded-full" />
        ) : (
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-surface text-muted">
            <ClockCounterClockwise size={16} />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="flex items-center gap-1.5 text-sm font-medium text-foreground">
            <ClockCounterClockwise size={14} className="text-primary" />
            {t('members.caseTimeline.title')}
          </h3>
          {headerUser && (
            <p className="truncate text-xs text-muted">
              {headerUser.display_name} · {headerUser.id}
              {timeline && !timeline.in_guild && (
                <span className="ml-1.5 text-amber-500">({t('members.caseTimeline.notInGuild')})</span>
              )}
            </p>
          )}
        </div>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted">{t('members.caseTimeline.empty')}</p>
      ) : (
        <ol className="relative flex flex-col gap-0 border-l border-border pl-4">
          {items.map((item) => {
            const removed = Boolean(item.meta?.removed)
            const modLabel = item.moderator_display
              ? t('members.caseTimeline.byModerator', { name: item.moderator_display })
              : item.moderator_id
                ? t('members.caseTimeline.byModerator', { name: item.moderator_id })
                : t('members.caseTimeline.automatic')
            return (
              <li key={item.id} className="relative pb-3 last:pb-0">
                <span
                  className={`absolute -left-[1.3rem] top-1.5 h-2.5 w-2.5 rounded-full ring-2 ring-background ${kindDotClass(item.kind)}`}
                />
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                  <span className="text-xs font-medium text-foreground">{kindLabel(item.kind, t)}</span>
                  {item.timestamp && (
                    <time className="text-[11px] text-muted">
                      {new Date(item.timestamp).toLocaleString(dateLocale)}
                    </time>
                  )}
                  {removed && (
                    <span className="text-[11px] text-muted">· {t('members.caseTimeline.removed')}</span>
                  )}
                </div>
                {item.reason && (
                  <p className={`mt-0.5 text-xs ${removed ? 'text-muted line-through' : 'text-foreground'}`}>
                    {item.reason}
                  </p>
                )}
                <p className="mt-0.5 text-[11px] text-muted">
                  {modLabel}
                  {item.extra ? ` · ${item.extra}` : ''}
                </p>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
