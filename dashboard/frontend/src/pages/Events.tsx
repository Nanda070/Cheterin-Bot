import { useEffect, useState } from 'react'
import {
  createEvent,
  fetchChannels,
  fetchEvents,
  fetchRoles,
  type ChannelInfo,
  type CreateEventSpec,
  type EmbedFieldSpec,
  type EmbedSpec,
  type EventSummary,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmbedPreview } from '../components/EmbedPreview'
import { Modal } from '../components/ui/Modal'
import { EventDetailPanel } from './EventDetailPanel'

type StatusFilter = 'open' | 'closed'

function emptyCreateSpec(): CreateEventSpec {
  return {
    channel_id: '',
    type: 'tournament',
    title: '',
    description: '',
    banner_url: '',
    ping: 'none',
    mode: 'solo',
    require_info: false,
    max_limit: 0,
    team_size: 5,
    role_reward: null,
    options: [],
    multi_select: false,
  }
}

const MODE_LABELS: Record<CreateEventSpec['mode'], string> = {
  solo: 'Соло',
  team_captain: 'Командный',
  team_code: 'Командный (по коду)',
}

function buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string): EmbedSpec {
  const fields: EmbedFieldSpec[] =
    spec.type === 'tournament'
      ? [
          { name: 'Формат', value: MODE_LABELS[spec.mode], inline: true },
          spec.max_limit > 0
            ? { name: 'Лимит', value: `0 / ${spec.max_limit}`, inline: true }
            : { name: 'Участники', value: '0', inline: true },
        ]
      : optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean)
          .map((opt) => ({ name: opt, value: '░░░░░░░░░░ 0% (0 гол.)', inline: false }))

  return {
    title: spec.title,
    description: spec.description,
    url: '',
    color: spec.type === 'tournament' ? '#ed4245' : '#5865f2',
    author: { name: '', url: '', icon_url: '' },
    footer: { text: '🟢 Статус: Открыто', icon_url: '' },
    image: { url: spec.banner_url },
    thumbnail: { url: '' },
    timestamp: null,
    fields,
  }
}

export function EventsPage() {
  const [status, setStatus] = useState<StatusFilter>('open')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [createSpec, setCreateSpec] = useState<CreateEventSpec>(emptyCreateSpec())
  const [optionsText, setOptionsText] = useState('')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)

  const reload = () => {
    fetchEvents(status)
      .then(setEvents)
      .catch(() => setError('Не удалось загрузить события'))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [status])

  const openCreate = () => {
    setCreateSpec(emptyCreateSpec())
    setOptionsText('')
    setCreateError('')
    setCreateOpen(true)
  }

  const saveCreate = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      const spec: CreateEventSpec = {
        ...createSpec,
        options: optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean),
      }
      await createEvent(spec)
      setCreateOpen(false)
      reload()
    } catch {
      setCreateError('Не удалось создать событие — проверьте поля')
    } finally {
      setCreateBusy(false)
    }
  }

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">События и голосования</h1>
          <Button variant="primary" onClick={openCreate} className="ml-auto">
            Создать событие
          </Button>
          <label className="text-sm text-muted" htmlFor="event-status">
            Статус
          </label>
          <select
            id="event-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as StatusFilter)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="open">Активные</option>
            <option value="closed">Закрытые</option>
          </select>
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {events.map((ev) => (
            <Card key={ev.message_id} interactive className="!p-3" onClick={() => setSelectedId(ev.message_id)}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">{ev.title}</p>
                  <p className="text-xs text-muted">
                    {ev.type === 'tournament' ? 'Турнир' : 'Опрос'} · {ev.count}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {events.length === 0 && <p className="text-sm text-muted">Событий нет.</p>}
        </div>
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <EventDetailPanel
            messageId={selectedId}
            onClose={() => setSelectedId(null)}
            onChanged={() => {
              setSelectedId(null)
              reload()
            }}
          />
        </div>
      )}

      <Modal open={createOpen} title="Создать событие" onClose={() => setCreateOpen(false)}>
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <div className="flex gap-2">
            <Button
              variant={createSpec.type === 'tournament' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'tournament' }))}
            >
              Турнир
            </Button>
            <Button
              variant={createSpec.type === 'poll' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'poll' }))}
            >
              Опрос
            </Button>
          </div>

          <div data-testid="event-embed-preview">
            <EmbedPreview content="" embed={buildEventEmbedPreview(createSpec, optionsText)} />
          </div>

          <label className="text-sm text-muted" htmlFor="event-title">
            Название
          </label>
          <input
            id="event-title"
            value={createSpec.title}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-description">
            Описание
          </label>
          <textarea
            id="event-description"
            value={createSpec.description}
            onChange={(e) => {
              setCreateSpec((prev) => ({ ...prev, description: e.target.value }))
              e.target.style.height = 'auto'
              e.target.style.height = `${e.target.scrollHeight}px`
            }}
            rows={8}
            className="min-h-[180px] resize-none overflow-hidden rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-banner">
            URL баннера (опционально)
          </label>
          <input
            id="event-banner"
            value={createSpec.banner_url}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, banner_url: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-ping">
            Пинг
          </label>
          <select
            id="event-ping"
            value={createSpec.ping}
            onChange={(e) =>
              setCreateSpec((prev) => ({ ...prev, ping: e.target.value as CreateEventSpec['ping'] }))
            }
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="none">Нет</option>
            <option value="everyone">@everyone</option>
            <option value="here">@here</option>
          </select>

          <label className="text-sm text-muted" htmlFor="event-channel">
            Канал
          </label>
          <select
            id="event-channel"
            value={createSpec.channel_id}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, channel_id: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите канал…</option>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          {createSpec.type === 'tournament' ? (
            <>
              <label className="text-sm text-muted" htmlFor="event-mode">
                Формат
              </label>
              <select
                id="event-mode"
                value={createSpec.mode}
                onChange={(e) =>
                  setCreateSpec((prev) => ({ ...prev, mode: e.target.value as CreateEventSpec['mode'] }))
                }
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="solo">Соло</option>
                <option value="team_captain">Командный (Капитан)</option>
                <option value="team_code">Командный (По коду)</option>
              </select>

              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={createSpec.require_info}
                  onChange={(e) => setCreateSpec((prev) => ({ ...prev, require_info: e.target.checked }))}
                />
                Анкета (запрашивать игровой ник)
              </label>

              <label className="text-sm text-muted" htmlFor="event-max-limit">
                Макс. участников/команд (0 = безлимит)
              </label>
              <input
                id="event-max-limit"
                type="number"
                min={0}
                value={createSpec.max_limit}
                onChange={(e) => setCreateSpec((prev) => ({ ...prev, max_limit: Number(e.target.value) }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              {createSpec.mode !== 'solo' && (
                <>
                  <label className="text-sm text-muted" htmlFor="event-team-size">
                    Размер команды
                  </label>
                  <input
                    id="event-team-size"
                    type="number"
                    min={2}
                    value={createSpec.team_size}
                    onChange={(e) => setCreateSpec((prev) => ({ ...prev, team_size: Number(e.target.value) }))}
                    className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </>
              )}

              <label className="text-sm text-muted" htmlFor="event-role-reward">
                Выдаваемая роль (опционально)
              </label>
              <select
                id="event-role-reward"
                value={createSpec.role_reward ?? ''}
                onChange={(e) => setCreateSpec((prev) => ({ ...prev, role_reward: e.target.value || null }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="">Без роли</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </>
          ) : (
            <>
              <label className="text-sm text-muted" htmlFor="event-options">
                Варианты ответа (каждый с новой строки, 2–10)
              </label>
              <textarea
                id="event-options"
                value={optionsText}
                onChange={(e) => setOptionsText(e.target.value)}
                rows={4}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={createSpec.multi_select}
                  onChange={(e) => setCreateSpec((prev) => ({ ...prev, multi_select: e.target.checked }))}
                />
                Мульти-выбор
              </label>
            </>
          )}

          {createError && <p className="text-sm text-danger">{createError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)} disabled={createBusy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={saveCreate} disabled={createBusy}>
              {createBusy ? 'Создаём…' : 'Создать'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
