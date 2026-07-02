import { useEffect, useState } from 'react'
import {
  deleteReactionRole,
  fetchChannels,
  fetchReactionRoles,
  fetchRoles,
  type ChannelInfo,
  type ReactionRoleEntry,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { ReactionRoleForm } from '../components/ReactionRoleForm'

export function ReactionRolesPage() {
  const [entries, setEntries] = useState<ReactionRoleEntry[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<ReactionRoleEntry | null>(null)
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)

  const reload = () => {
    fetchReactionRoles()
      .then(setEntries)
      .catch(() => setError('Не удалось загрузить reaction roles'))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [])

  const channelName = (id: string) => channels.find((c) => c.id === id)?.name ?? id
  const roleNames = (pairIds: string[]) =>
    pairIds.map((id) => roles.find((r) => r.id === id)?.name ?? id).join(', ')

  const confirmDelete = async () => {
    if (!pendingDelete) return
    try {
      await deleteReactionRole(pendingDelete)
      setPendingDelete(null)
      reload()
    } catch {
      setError('Не удалось удалить')
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Reaction Roles</h1>
        <Button
          variant="primary"
          onClick={() => {
            setEditing(null)
            setFormOpen(true)
          }}
        >
          Создать reaction role
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {entries.map((entry) => (
          <Card key={entry.message_id} className="flex items-center justify-between !p-3">
            <div>
              <p className="text-sm text-foreground">{channelName(entry.channel_id)}</p>
              <p className="text-xs text-muted">{roleNames(entry.pairs.map((p) => p.role_id))}</p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setEditing(entry)
                  setFormOpen(true)
                }}
              >
                Edit
              </Button>
              <Button variant="danger" onClick={() => setPendingDelete(entry.message_id)}>
                Delete
              </Button>
            </div>
          </Card>
        ))}
        {entries.length === 0 && <p className="text-sm text-muted">Пока ничего не настроено.</p>}
      </div>

      <ReactionRoleForm
        open={formOpen}
        editing={editing}
        onClose={() => setFormOpen(false)}
        onSaved={reload}
      />

      <Modal open={pendingDelete !== null} title="Удалить reaction role?" onClose={() => setPendingDelete(null)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить
          </Button>
        </div>
      </Modal>
    </div>
  )
}
