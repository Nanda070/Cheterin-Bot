import { useEffect, useState } from 'react'
import {
  closeEvent,
  deleteEvent,
  fetchEventDetail,
  notifyEventParticipants,
  type EventDetail,
  type EventParticipantTeamCode,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

interface Props {
  messageId: string
  onClose: () => void
  onChanged: () => void
}

export function EventDetailPanel({ messageId, onClose, onChanged }: Props) {
  const [detail, setDetail] = useState<EventDetail | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(false)
  const [notifyOpen, setNotifyOpen] = useState(false)
  const [notifyText, setNotifyText] = useState('')
  const [notifyError, setNotifyError] = useState('')

  useEffect(() => {
    fetchEventDetail(messageId)
      .then(setDetail)
      .catch(() => setError('Не удалось загрузить событие'))
  }, [messageId])

  const close = async () => {
    setBusy(true)
    setError('')
    try {
      await closeEvent(messageId)
      onChanged()
    } catch {
      setError('Не удалось закрыть событие')
    } finally {
      setBusy(false)
    }
  }

  const confirmDelete = async () => {
    setBusy(true)
    setError('')
    try {
      await deleteEvent(messageId)
      setPendingDelete(false)
      onChanged()
    } catch {
      setError('Не удалось удалить событие')
      setPendingDelete(false)
    } finally {
      setBusy(false)
    }
  }

  const sendNotify = async () => {
    if (!notifyText.trim()) {
      setNotifyError('Введите текст сообщения')
      return
    }
    setBusy(true)
    setNotifyError('')
    try {
      await notifyEventParticipants(messageId, notifyText.trim())
      setNotifyOpen(false)
      setNotifyText('')
    } catch {
      setNotifyError('Не удалось отправить рассылку')
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

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-foreground">{detail.title}</h2>
          <p className="text-xs text-muted">
            {detail.type === 'tournament' ? 'Турнир' : 'Опрос'} · {detail.status}
          </p>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          ×
        </button>
      </div>

      {detail.type === 'tournament' && detail.mode === 'solo' && (
        <ul className="flex flex-col gap-1 text-sm">
          {(detail.participants ?? []).map((p) => {
            const solo = p as { user_id: string; ign: string }
            return (
              <li key={solo.user_id} className="text-foreground">
                {solo.ign}
              </li>
            )
          })}
        </ul>
      )}

      {detail.type === 'tournament' && detail.mode === 'team_captain' && (
        <ul className="flex flex-col gap-1 text-sm">
          {(detail.participants ?? []).map((p) => {
            const team = p as { user_id: string; team_name: string; members: string }
            return (
              <li key={team.user_id} className="text-foreground">
                {team.team_name} — {team.members}
              </li>
            )
          })}
        </ul>
      )}

      {detail.type === 'tournament' && detail.mode === 'team_code' && (
        <div className="flex flex-col gap-2 text-sm">
          {(detail.participants as EventParticipantTeamCode[] | undefined)?.map((team) => (
            <div key={team.team_code}>
              <p className="text-foreground">{team.team_name}</p>
              <ul className="ml-3">
                {team.members.map((m) => (
                  <li key={m.user_id} className="text-muted">
                    {m.ign}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {detail.type === 'poll' && (
        <div className="flex flex-col gap-2 text-sm">
          {(detail.options ?? []).map((opt) => (
            <div key={opt.label} className="flex justify-between text-foreground">
              <span>{opt.label}</span>
              <span>{opt.percent}%</span>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-2 border-t border-border pt-4">
        <Button variant="secondary" onClick={close} disabled={busy}>
          Закрыть
        </Button>
        {detail.type === 'tournament' && (
          <Button variant="secondary" onClick={() => setNotifyOpen(true)} disabled={busy}>
            Рассылка
          </Button>
        )}
        <Button variant="danger" onClick={() => setPendingDelete(true)} disabled={busy}>
          Удалить
        </Button>
      </div>

      <Modal open={pendingDelete} title="Удалить событие?" onClose={() => setPendingDelete(false)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(false)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить событие
          </Button>
        </div>
      </Modal>

      <Modal open={notifyOpen} title="Рассылка участникам" onClose={() => setNotifyOpen(false)}>
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="event-notify-text">
            Текст сообщения
          </label>
          <textarea
            id="event-notify-text"
            value={notifyText}
            onChange={(e) => setNotifyText(e.target.value)}
            rows={4}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
          {notifyError && <p className="text-sm text-danger">{notifyError}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setNotifyOpen(false)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={sendNotify} disabled={busy}>
              Отправить
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
