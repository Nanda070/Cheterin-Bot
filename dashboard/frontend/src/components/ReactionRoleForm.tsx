import { useEffect, useState } from 'react'
import {
  createReactionRole,
  fetchChannels,
  fetchEmojis,
  fetchRoles,
  updateReactionRole,
  type ChannelInfo,
  type CustomEmoji,
  type ReactionRoleEntry,
  type ReactionRolePair,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { useT } from '../context/LanguageContext'
import { Button } from './ui/Button'
import { Modal } from './ui/Modal'
import { Select } from './ui/Select'

interface Props {
  open: boolean
  onClose: () => void
  editing: ReactionRoleEntry | null
  onSaved: () => void
}

function hasDuplicateEmoji(pairs: ReactionRolePair[]): boolean {
  const emojis = pairs.map((p) => p.emoji).filter(Boolean)
  return new Set(emojis).size !== emojis.length
}

export function ReactionRoleForm({ open, onClose, editing, onSaved }: Props) {
  const t = useT()
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [emojis, setEmojis] = useState<CustomEmoji[]>([])
  const [channelId, setChannelId] = useState('')
  const [messageId, setMessageId] = useState('')
  const [pairs, setPairs] = useState<ReactionRolePair[]>([{ emoji: '', role_id: '' }])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    setError('')
    fetchChannels()
      .then(setChannels)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadChannels')))
    fetchRoles()
      .then(setRoles)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadRoles')))
    fetchEmojis().then(setEmojis).catch(() => {})
    if (editing) {
      setChannelId(editing.channel_id)
      setMessageId(editing.message_id)
      setPairs(editing.pairs.length > 0 ? editing.pairs : [{ emoji: '', role_id: '' }])
    } else {
      setChannelId('')
      setMessageId('')
      setPairs([{ emoji: '', role_id: '' }])
    }
  }, [open, editing, t])

  const updatePair = (index: number, patch: Partial<ReactionRolePair>) => {
    setPairs((prev) => prev.map((p, i) => (i === index ? { ...p, ...patch } : p)))
  }

  const removePair = (index: number) => {
    setPairs((prev) => prev.filter((_, i) => i !== index))
  }

  const addPair = () => {
    setPairs((prev) => [...prev, { emoji: '', role_id: '' }])
  }

  const handleSave = async () => {
    setError('')
    if (!channelId || !messageId) {
      setError('Укажите канал и Message ID')
      return
    }
    const validPairs = pairs.filter((p) => p.emoji && p.role_id)
    if (validPairs.length === 0) {
      setError('Добавьте хотя бы одну пару эмодзи → роль')
      return
    }
    if (hasDuplicateEmoji(validPairs)) {
      setError('Повторяющийся эмодзи в списке пар')
      return
    }

    setBusy(true)
    try {
      if (editing) {
        await updateReactionRole(editing.message_id, validPairs)
      } else {
        await createReactionRole(channelId, messageId, validPairs)
      }
      onSaved()
      onClose()
    } catch {
      setError('Не удалось сохранить — проверьте канал/ID сообщения и права на роли')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title={editing ? 'Редактировать reaction role' : 'Создать reaction role'} onClose={onClose}>
      <div className="flex flex-col gap-3">
        <label className="text-sm text-muted" htmlFor="rr-channel">
          Канал
        </label>
        <Select
          id="rr-channel"
          value={channelId}
          onChange={(id) => setChannelId(id)}
          disabled={!!editing}
          options={channels}
          placeholder="Выберите канал…"
        />

        <label className="text-sm text-muted" htmlFor="rr-message-id">
          Message ID
        </label>
        <input
          id="rr-message-id"
          value={messageId}
          onChange={(e) => setMessageId(e.target.value)}
          disabled={!!editing}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary disabled:opacity-50"
          placeholder="ID существующего сообщения"
        />

        <div className="flex flex-col gap-2">
          {pairs.map((pair, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
              <input
                value={pair.emoji}
                onChange={(e) => updatePair(index, { emoji: e.target.value })}
                placeholder="Эмодзи (вставьте unicode или выберите ниже)"
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <Select
                ariaLabel="Свой эмодзи сервера"
                value=""
                onChange={(id) => {
                  const custom = emojis.find((em) => em.id === id)
                  if (custom) updatePair(index, { emoji: `<:${custom.name}:${custom.id}>` })
                }}
                options={emojis}
                placeholder="Свой эмодзи…"
                className="min-w-0 flex-1 basis-28"
              />
              <Select
                ariaLabel="Роль для этой пары"
                value={pair.role_id}
                onChange={(id) => updatePair(index, { role_id: id })}
                options={roles}
                placeholder="Роль…"
                className="min-w-0 flex-1 basis-28"
              />
              <button
                type="button"
                onClick={() => removePair(index)}
                className="cursor-pointer text-muted hover:text-danger"
              >
                ×
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addPair}
            className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover"
          >
            + Добавить пару
          </button>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={busy}>
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
