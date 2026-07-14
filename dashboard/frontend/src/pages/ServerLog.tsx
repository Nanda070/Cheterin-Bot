import { ListMagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchServerLog,
  updateServerLog,
  type ChannelInfo,
  type ServerLogEventConfig,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

export function ServerLogPage() {
  const [labels, setLabels] = useState<Record<string, string>>({})
  const [events, setEvents] = useState<Record<string, ServerLogEventConfig> | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    Promise.all([fetchServerLog(), fetchChannels().catch(() => [] as ChannelInfo[])])
      .then(([settings, ch]) => {
        setLabels(settings.labels)
        setEvents(settings.events)
        setChannels(ch)
      })
      .catch(() => setError('Не удалось загрузить настройки логирования'))
  }, [])

  if (!events) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const setEvent = (type: string, patch: Partial<ServerLogEventConfig>) => {
    setEvents((prev) => (prev ? { ...prev, [type]: { ...prev[type], ...patch } } : prev))
  }

  const setAllTo = (channelId: string) => {
    setEvents((prev) => {
      if (!prev) return prev
      const next: Record<string, ServerLogEventConfig> = {}
      for (const [type, cfg] of Object.entries(prev)) next[type] = { ...cfg, channel_id: channelId }
      return next
    })
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateServerLog(events)
      setEvents(updated.events)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить — у каждого включённого события должен быть выбран канал')
    } finally {
      setBusy(false)
    }
  }

  const enabledCount = Object.values(events).filter((e) => e.enabled).length

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ListMagnifyingGlass size={22} className="text-primary" />
          Логирование событий
        </h1>
        <p className="mt-1 text-sm text-muted">
          Каждый тип события включается отдельно и пишет в свой канал. Включено: {enabledCount} из{' '}
          {Object.keys(events).length}.
        </p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-1 p-0">
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <span className="text-sm text-muted">Назначить всем один канал:</span>
          <Select
            value=""
            onChange={(id) => setAllTo(id)}
            options={channels}
            placeholder="Выбрать канал…"
            className="w-56"
          />
        </div>

        {Object.entries(labels).map(([type, label]) => {
          const cfg = events[type]
          if (!cfg) return null
          return (
            <div
              key={type}
              className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
            >
              <Toggle checked={cfg.enabled} onChange={(v) => setEvent(type, { enabled: v })} label={label} />
              <Select
                value={cfg.channel_id}
                onChange={(id) => setEvent(type, { channel_id: id })}
                options={channels}
                placeholder="Канал не выбран"
                className="w-56"
              />
            </div>
          )
        })}
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
