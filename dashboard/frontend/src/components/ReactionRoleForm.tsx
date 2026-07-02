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
import { Button } from './ui/Button'
import { Modal } from './ui/Modal'

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
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
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
    setError('')
  }, [open, editing])

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
        <select
          id="rr-channel"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          disabled={!!editing}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground disabled:opacity-50"
        >
          <option value="">Выберите канал…</option>
          {channels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

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
            <div key={index} className="flex items-center gap-2">
              <input
                value={pair.emoji}
                onChange={(e) => updatePair(index, { emoji: e.target.value })}
                placeholder="Эмодзи (вставьте unicode или выберите ниже)"
                className="flex-1 rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <select
                aria-label="Свой эмодзи сервера"
                value=""
                onChange={(e) => {
                  const custom = emojis.find((em) => em.id === e.target.value)
                  if (custom) updatePair(index, { emoji: `<:${custom.name}:${custom.id}>` })
                }}
                className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
              >
                <option value="">Свой эмодзи…</option>
                {emojis.map((em) => (
                  <option key={em.id} value={em.id}>
                    {em.name}
                  </option>
                ))}
              </select>
              <select
                aria-label="Роль для этой пары"
                value={pair.role_id}
                onChange={(e) => updatePair(index, { role_id: e.target.value })}
                className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
              >
                <option value="">Роль…</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
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
