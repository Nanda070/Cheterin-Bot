import { useEffect, useState } from 'react'
import { fetchEvents, type EventSummary } from '../api/client'
import { Card } from '../components/ui/Card'
import { EventDetailPanel } from './EventDetailPanel'

type StatusFilter = 'open' | 'closed'

export function EventsPage() {
  const [status, setStatus] = useState<StatusFilter>('open')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const reload = () => {
    fetchEvents(status)
      .then(setEvents)
      .catch(() => setError('Не удалось загрузить события'))
  }

  useEffect(reload, [status])

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">События и голосования</h1>
          <label className="ml-auto text-sm text-muted" htmlFor="event-status">
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
    </div>
  )
}
