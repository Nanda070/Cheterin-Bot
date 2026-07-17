import { Gift, Plus, XCircle } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createGiveaway,
  endGiveaway,
  fetchChannels,
  fetchGiveawayOverview,
  rerollGiveaway,
  type ChannelInfo,
  type Giveaway,
  type GiveawayOverview,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'

const STATUS_LABEL: Record<Giveaway['status'], string> = {
  active: 'Активен',
  finished: 'Завершён',
  cancelled: 'Отменён',
}

function GiveawayCard({
  giveaway,
  onEnd,
  onReroll,
  busy,
}: {
  giveaway: Giveaway
  onEnd?: () => void
  onReroll?: () => void
  busy?: boolean
}) {
  const isActive = giveaway.status === 'active'
  return (
    <Card className="animate-fade-in-up">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">
            №{giveaway.id} · {giveaway.prize}
          </p>
          <p className="text-sm text-muted">
            {giveaway.winners_count} победител{giveaway.winners_count === 1 ? 'ь' : 'ей'} · инициатор{' '}
            {giveaway.initiator_display} ·{' '}
            <span className={isActive ? 'text-success' : 'text-muted'}>{STATUS_LABEL[giveaway.status]}</span>
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          {isActive && (
            <Button variant="danger" onClick={onEnd} disabled={busy}>
              Завершить
            </Button>
          )}
          {giveaway.status === 'finished' && (
            <Button variant="secondary" onClick={onReroll} disabled={busy}>
              Реролл
            </Button>
          )}
        </div>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            Участники [{giveaway.entrants.length}]
          </p>
          {giveaway.entrants.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {giveaway.entrants.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Победители [{giveaway.winners.length}]</p>
          {giveaway.winners.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {giveaway.winners.map((p) => (
                <li key={p.id} className="text-sm text-foreground">
                  🏆 {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  )
}

export function GiveawaysPage() {
  const [overview, setOverview] = useState<GiveawayOverview | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ channel_id: '', prize: '', duration_str: '', winners_count: '1' })

  const reload = () => {
    fetchGiveawayOverview()
      .then((data) => {
        setOverview(data)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить данные о розыгрышах'))
  }

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
  }, [])

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      reload()
    } catch {
      setError('Операция не удалась')
    } finally {
      setBusy(false)
    }
  }

  const submitCreate = () =>
    act(async () => {
      await createGiveaway({
        channel_id: form.channel_id,
        prize: form.prize.trim(),
        duration_str: form.duration_str.trim(),
        winners_count: Number(form.winners_count),
      })
      setCreating(false)
      setForm({ channel_id: '', prize: '', duration_str: '', winners_count: '1' })
    })

  if (!overview) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Gift size={22} className="text-primary" />
          Гивевеи
        </h1>
        <Button variant="primary" onClick={() => setCreating(true)}>
          <Plus size={16} />
          Новый гивевей
        </Button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Активные</h2>
        {overview.active.length === 0 && <p className="text-sm text-muted">Активных розыгрышей нет.</p>}
        {overview.active.map((giveaway) => (
          <GiveawayCard
            key={giveaway.id}
            giveaway={giveaway}
            busy={busy}
            onEnd={() => act(() => endGiveaway(giveaway.id))}
          />
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <XCircle size={16} />
          История
        </h2>
        {overview.history.length === 0 && <p className="text-sm text-muted">Истории пока нет.</p>}
        {overview.history.map((giveaway) => (
          <GiveawayCard
            key={giveaway.id}
            giveaway={giveaway}
            busy={busy}
            onReroll={() => act(() => rerollGiveaway(giveaway.id))}
          />
        ))}
      </section>

      <Modal open={creating} title="Новый гивевей" onClose={() => setCreating(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="giveaway-channel">
              Канал публикации
            </label>
            <Select
              id="giveaway-channel"
              value={form.channel_id}
              onChange={(id) => setForm((f) => ({ ...f, channel_id: id }))}
              options={channels}
              placeholder="Выберите канал"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="giveaway-prize">
              Приз
            </label>
            <input
              id="giveaway-prize"
              value={form.prize}
              onChange={(e) => setForm((f) => ({ ...f, prize: e.target.value }))}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="giveaway-duration">
                Длительность
              </label>
              <input
                id="giveaway-duration"
                placeholder="10m, 2h, 1d"
                value={form.duration_str}
                onChange={(e) => setForm((f) => ({ ...f, duration_str: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="giveaway-winners">
                Победителей
              </label>
              <input
                id="giveaway-winners"
                type="number"
                min={1}
                max={20}
                value={form.winners_count}
                onChange={(e) => setForm((f) => ({ ...f, winners_count: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreating(false)} disabled={busy}>
              Отмена
            </Button>
            <Button
              variant="primary"
              onClick={submitCreate}
              disabled={busy || !form.channel_id || !form.prize.trim() || !form.duration_str.trim()}
            >
              {busy ? 'Создаём…' : 'Создать'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
