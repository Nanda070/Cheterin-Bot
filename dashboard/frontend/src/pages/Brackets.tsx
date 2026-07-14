import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createBracket,
  fetchBrackets,
  fetchEventEntries,
  fetchEvents,
  type BracketFormat,
  type BracketSummary,
  type EventSummary,
} from '../api/client'

const FORMAT_LABEL: Record<BracketFormat, string> = {
  single_elim: 'Single Elimination',
  double_elim: 'Double Elimination',
  round_robin: 'Round Robin',
}
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'

type SourceTab = 'event' | 'manual'

function shuffle(items: string[]): string[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

export function BracketsPage() {
  const navigate = useNavigate()
  const [brackets, setBrackets] = useState<BracketSummary[]>([])
  const [events, setEvents] = useState<EventSummary[]>([])
  const [error, setError] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [tab, setTab] = useState<SourceTab>('event')
  const [selectedEventId, setSelectedEventId] = useState('')
  const [manualText, setManualText] = useState('')
  const [title, setTitle] = useState('')
  const [entries, setEntries] = useState<string[]>([])
  const [step, setStep] = useState<'source' | 'seed'>('source')
  const [format, setFormat] = useState<BracketFormat>('single_elim')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)

  const reload = () => {
    fetchBrackets()
      .then(setBrackets)
      .catch(() => setError('Не удалось загрузить сетки'))
  }

  useEffect(reload, [])
  useEffect(() => {
    Promise.all([fetchEvents('open'), fetchEvents('closed')])
      .then(([open, closed]) => setEvents([...open, ...closed]))
      .catch(() => {})
  }, [])

  const openCreate = () => {
    setTab('event')
    setSelectedEventId('')
    setManualText('')
    setTitle('')
    setEntries([])
    setStep('source')
    setCreateError('')
    setCreateOpen(true)
  }

  const loadEventEntries = async (eventId: string) => {
    setSelectedEventId(eventId)
    if (!eventId) {
      setEntries([])
      return
    }
    try {
      const loaded = await fetchEventEntries(eventId)
      setEntries(loaded)
    } catch {
      setCreateError('Не удалось загрузить участников события')
    }
  }

  const goToSeedStep = () => {
    if (tab === 'manual') {
      const lines = manualText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
      setEntries(lines)
    }
    setStep('seed')
  }

  const moveEntry = (index: number, direction: -1 | 1) => {
    setEntries((prev) => {
      const target = index + direction
      if (target < 0 || target >= prev.length) return prev
      const copy = [...prev]
      ;[copy[index], copy[target]] = [copy[target], copy[index]]
      return copy
    })
  }

  const save = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      await createBracket(title, entries, tab === 'event' ? selectedEventId || null : null, format)
      setCreateOpen(false)
      reload()
    } catch {
      setCreateError('Не удалось создать сетку')
    } finally {
      setCreateBusy(false)
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">Сетки</h1>
        <Button variant="primary" onClick={openCreate} className="ml-auto">
          Создать сетку
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {brackets.map((b) => (
          <Card key={b.id} interactive className="!p-3" onClick={() => navigate(`/brackets/${b.id}`)}>
            <p className="text-sm text-foreground">{b.title}</p>
            <p className="text-xs text-muted">
              {b.entry_count} участников · {FORMAT_LABEL[b.format] ?? b.format}
            </p>
          </Card>
        ))}
        {brackets.length === 0 && <p className="text-sm text-muted">Сеток пока нет.</p>}
      </div>

      <Modal open={createOpen} title="Создать сетку" onClose={() => setCreateOpen(false)}>
        {step === 'source' ? (
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <Button variant={tab === 'event' ? 'primary' : 'secondary'} onClick={() => setTab('event')}>
                Из ивента
              </Button>
              <Button variant={tab === 'manual' ? 'primary' : 'secondary'} onClick={() => setTab('manual')}>
                Вручную
              </Button>
            </div>

            {tab === 'event' ? (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-event">
                  Событие
                </label>
                <Select
                  id="bracket-event"
                  value={selectedEventId}
                  onChange={(id) => loadEventEntries(id)}
                  options={events
                    .filter((ev) => ev.type === 'tournament')
                    .map((ev) => ({ id: ev.message_id, name: ev.title }))}
                  placeholder="Выберите событие…"
                />
                {entries.length > 0 && (
                  <p className="text-xs text-muted">Загружено участников: {entries.length}</p>
                )}
              </>
            ) : (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-manual-names">
                  Имена (по одному на строку)
                </label>
                <textarea
                  id="bracket-manual-names"
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  rows={6}
                  className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                />
              </>
            )}

            <label className="text-sm text-muted" htmlFor="bracket-title">
              Название
            </label>
            <input
              id="bracket-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />

            <label className="text-sm text-muted" htmlFor="bracket-format">
              Формат
            </label>
            <Select
              id="bracket-format"
              value={format}
              onChange={(id) => setFormat(id as BracketFormat)}
              options={(Object.keys(FORMAT_LABEL) as BracketFormat[]).map((f) => ({ id: f, name: FORMAT_LABEL[f] }))}
            />
            <p className="text-xs text-muted">
              {format === 'single_elim' && 'Классическая сетка на вылет: одно поражение — выбывание.'}
              {format === 'double_elim' && 'Верхняя и нижняя сетки: выбывание после двух поражений, гранд-финал.'}
              {format === 'round_robin' && 'Круговая система: каждый играет с каждым, таблица очков (победа 3, ничья 1). До 20 участников.'}
            </p>

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>
                Отмена
              </Button>
              <Button variant="primary" onClick={goToSeedStep}>
                Далее
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted">Порядок посева</p>
              <Button variant="secondary" onClick={() => setEntries((prev) => shuffle(prev))}>
                Перемешать
              </Button>
            </div>

            <ul className="flex flex-col gap-1">
              {entries.map((entry, index) => (
                <li
                  key={`${entry}-${index}`}
                  className="flex items-center justify-between rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <span>{entry}</span>
                  <span className="flex gap-1">
                    <button
                      type="button"
                      aria-label="Переместить вверх"
                      onClick={() => moveEntry(index, -1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      aria-label="Переместить вниз"
                      onClick={() => moveEntry(index, 1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↓
                    </button>
                  </span>
                </li>
              ))}
            </ul>

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setStep('source')} disabled={createBusy}>
                Назад
              </Button>
              <Button variant="primary" onClick={save} disabled={createBusy || entries.length < 2}>
                {createBusy ? 'Создаём…' : 'Сгенерировать'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
