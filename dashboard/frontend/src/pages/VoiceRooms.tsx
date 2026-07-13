import { ArrowsClockwise, Headset, LockSimple, LockSimpleOpen, Trash, UsersThree } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { deleteVoiceRoom, fetchVoiceRooms, publishVoicePanel, type VoiceRoom } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

export function VoiceRoomsPage() {
  const [rooms, setRooms] = useState<VoiceRoom[] | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [deleting, setDeleting] = useState<VoiceRoom | null>(null)

  const reload = () => {
    fetchVoiceRooms()
      .then((data) => {
        setRooms(data)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить список комнат'))
  }

  useEffect(reload, [])

  const confirmDelete = async () => {
    if (!deleting) return
    setBusy(true)
    setError('')
    try {
      await deleteVoiceRoom(deleting.channel_id)
      setDeleting(null)
      reload()
    } catch {
      setError('Не удалось удалить комнату')
    } finally {
      setBusy(false)
    }
  }

  const republish = async () => {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await publishVoicePanel()
      setNotice('Панель управления опубликована/обновлена.')
    } catch {
      setError('Не удалось опубликовать панель — проверьте канал панели в конфигурации')
    } finally {
      setBusy(false)
    }
  }

  if (!rooms) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Headset size={22} className="text-primary" />
          Приватные комнаты
        </h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={reload} disabled={busy}>
            <ArrowsClockwise size={16} />
            Обновить
          </Button>
          <Button variant="primary" onClick={republish} disabled={busy}>
            Опубликовать панель
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {notice && <p className="text-sm text-primary">{notice}</p>}

      {rooms.length === 0 && (
        <Card>
          <p className="text-sm text-muted">
            Активных приватных комнат нет. Комната создаётся автоматически, когда участник заходит в голосовое лобби
            (настраивается в разделе «Конфигурация»).
          </p>
        </Card>
      )}

      {rooms.map((room) => (
        <Card key={room.channel_id} className="animate-fade-in-up">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="flex items-center gap-2 font-semibold text-foreground">
                {room.is_closed ? (
                  <LockSimple size={16} className="shrink-0 text-warning" />
                ) : (
                  <LockSimpleOpen size={16} className="shrink-0 text-success" />
                )}
                <span className="truncate">{room.name}</span>
              </p>
              <p className="mt-1 text-sm text-muted">
                Владелец: {room.owner_display} · {room.is_closed ? 'Закрыта для входа' : 'Открыта'} · Лимит:{' '}
                {room.user_limit === 0 ? 'нет' : room.user_limit}
              </p>
              <p className="mt-1 flex items-center gap-1 text-sm text-muted">
                <UsersThree size={15} />
                Сейчас в комнате: {room.member_count}
                {!room.exists && <span className="text-danger"> · канал не найден</span>}
              </p>
            </div>
            <Button variant="danger" onClick={() => setDeleting(room)} disabled={busy}>
              <Trash size={16} />
              Удалить
            </Button>
          </div>
        </Card>
      ))}

      <Modal open={deleting !== null} title="Удалить приватную комнату?" onClose={() => setDeleting(null)}>
        <p className="mb-4 text-sm text-muted">
          Комната «{deleting?.name}» будет удалена вместе с голосовым каналом. Участники будут отключены.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleting(null)} disabled={busy}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={busy}>
            {busy ? 'Удаляем…' : 'Удалить'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
