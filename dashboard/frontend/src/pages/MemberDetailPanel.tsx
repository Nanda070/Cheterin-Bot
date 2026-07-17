import { Trash, Warning, X } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  banMember,
  createMemberWarn,
  deleteWarn,
  fetchMemberDetail,
  fetchMemberWarns,
  fetchRoles,
  grantRole,
  kickMember,
  revokeRole,
  type MemberDetail,
  type RoleInfo,
  type Warn,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'

type PendingAction = 'ban' | 'kick' | 'warn' | null

interface Props {
  memberId: string
  onClose: () => void
  onActionDone: () => void
}

export function MemberDetailPanel({ memberId, onClose, onActionDone }: Props) {
  const [detail, setDetail] = useState<MemberDetail | null>(null)
  const [assignable, setAssignable] = useState<RoleInfo[]>([])
  const [pending, setPending] = useState<PendingAction>(null)
  const [reason, setReason] = useState('')
  const [deleteDays, setDeleteDays] = useState<0 | 1 | 7>(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [warns, setWarns] = useState<Warn[]>([])
  const [activeWarnCount, setActiveWarnCount] = useState(0)
  const [warnBusy, setWarnBusy] = useState(false)

  const reload = () => {
    fetchMemberDetail(memberId).then(setDetail).catch(() => setError('Не удалось загрузить участника'))
    fetchRoles().then(setAssignable).catch(() => {})
    reloadWarns()
  }

  const reloadWarns = () => {
    fetchMemberWarns(memberId)
      .then((data) => {
        setWarns(data.warns)
        setActiveWarnCount(data.active_count)
      })
      .catch(() => {})
  }

  useEffect(reload, [memberId])

  const confirmAction = async () => {
    if (!reason.trim()) {
      setError('Укажите причину')
      return
    }
    setBusy(true)
    setError('')
    try {
      if (pending === 'ban') await banMember(memberId, reason.trim(), deleteDays)
      if (pending === 'kick') await kickMember(memberId, reason.trim())
      if (pending === 'warn') {
        await createMemberWarn(memberId, reason.trim())
        reloadWarns()
      }
      setPending(null)
      setReason('')
      onActionDone()
      if (pending !== 'warn') onClose()
    } catch {
      setError('Discord отклонил действие (не хватает прав?)')
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
      setError('Не удалось снять предупреждение')
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
      setError('Discord отклонил изменение роли')
    } finally {
      setBusy(false)
    }
  }

  if (!detail) {
    return (
      <Card className="animate-fade-in-up">
        <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
      </Card>
    )
  }

  const memberRoleIds = new Set(detail.roles.map((r) => r.id))

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
        <dt className="text-muted">Вошёл на сервер</dt>
        <dd>{detail.joined_at ? new Date(detail.joined_at).toLocaleDateString('ru-RU') : '—'}</dd>
        <dt className="text-muted">Аккаунт создан</dt>
        <dd>{new Date(detail.created_at).toLocaleDateString('ru-RU')}</dd>
        <dt className="text-muted">Приглашения</dt>
        <dd>
          {detail.invite_stats.invites} (зашло {detail.invite_stats.joins}, ушло {detail.invite_stats.leaves})
        </dd>
        <dt className="text-muted">Обращений/жалоб</dt>
        <dd>{detail.feedback_case_count}</dd>
      </dl>

      <div>
        <h3 className="mb-2 text-sm font-medium text-muted">Роли</h3>
        <div className="flex flex-wrap gap-1.5">
          {detail.roles.map((role) => (
            <button
              key={role.id}
              onClick={() => toggleRole(role.id, true)}
              disabled={busy}
              title="Нажмите, чтобы снять роль"
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
                + добавить роль
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
            Предупреждения ({activeWarnCount})
          </h3>
          {warns.length === 0 ? (
            <p className="text-sm text-muted">Предупреждений нет.</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {warns.map((w) => {
                const isActive = !w.removed && (!w.expires_at || w.expires_at > new Date().toISOString())
                return (
                  <li key={w.id} className="flex items-start justify-between gap-2 text-xs">
                    <span className={isActive ? 'text-foreground' : 'text-muted line-through'}>
                      #{w.id} — {w.reason}
                      <span className="ml-1 text-muted">({new Date(w.created_at).toLocaleDateString('ru-RU')})</span>
                    </span>
                    {isActive && (
                      <button
                        onClick={() => removeWarn(w.id)}
                        disabled={warnBusy}
                        title="Снять предупреждение"
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

      {error && <p className="text-sm text-danger">{error}</p>}

      {!detail.is_bot && (
        <div className="flex gap-2 border-t border-border pt-4">
          <Button variant="danger" onClick={() => setPending('ban')} disabled={busy}>
            Забанить
          </Button>
          <Button variant="secondary" onClick={() => setPending('kick')} disabled={busy}>
            Кикнуть
          </Button>
          <Button variant="secondary" onClick={() => setPending('warn')} disabled={busy}>
            Выдать предупреждение
          </Button>
        </div>
      )}

      <Modal
        open={pending !== null}
        title={
          pending === 'ban'
            ? `Забанить ${detail.display_name}?`
            : pending === 'kick'
              ? `Кикнуть ${detail.display_name}?`
              : `Выдать предупреждение ${detail.display_name}?`
        }
        onClose={() => setPending(null)}
      >
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="mod-reason">
            Причина (обязательно)
          </label>
          <input
            id="mod-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            placeholder="Например: спам в общем чате"
          />
          {pending === 'ban' && (
            <>
              <label className="text-sm text-muted" htmlFor="mod-days">
                Удалить сообщения за
              </label>
              <Select
                id="mod-days"
                value={String(deleteDays)}
                onChange={(id) => setDeleteDays(Number(id) as 0 | 1 | 7)}
                options={[
                  { id: '0', name: 'Не удалять' },
                  { id: '1', name: '1 день' },
                  { id: '7', name: '7 дней' },
                ]}
              />
            </>
          )}
          {error && <p className="text-sm text-danger">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setPending(null)} disabled={busy}>
              Отмена
            </Button>
            <Button variant={pending === 'warn' ? 'primary' : 'danger'} onClick={confirmAction} disabled={busy}>
              {busy ? 'Выполняем…' : 'Подтвердить'}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
