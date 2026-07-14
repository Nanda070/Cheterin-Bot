import { Package, Plus, Trophy, XCircle } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  cancelSupply,
  closeSupply,
  createSupply,
  fetchChannels,
  fetchSupplyOverview,
  type ChannelInfo,
  type Supply,
  type SupplyOverview,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'

const STATUS_LABEL: Record<Supply['status'], string> = {
  active: 'Активен',
  finished: 'Завершён',
  cancelled: 'Отменён',
}

function SupplyCard({
  supply,
  onClose,
  onCancel,
  busy,
}: {
  supply: Supply
  onClose?: () => void
  onCancel?: () => void
  busy?: boolean
}) {
  const isActive = supply.status === 'active'
  return (
    <Card className="animate-fade-in-up">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">
            №{supply.id} · против {supply.opponent}
          </p>
          <p className="text-sm text-muted">
            {supply.time_str} МСК · инициатор {supply.initiator_display} ·{' '}
            <span className={isActive ? 'text-success' : 'text-muted'}>{STATUS_LABEL[supply.status]}</span>
          </p>
        </div>
        {isActive && (
          <div className="flex shrink-0 gap-2">
            <Button variant="secondary" onClick={onClose} disabled={busy}>
              Завершить
            </Button>
            <Button variant="danger" onClick={onCancel} disabled={busy}>
              Отменить
            </Button>
          </div>
        )}
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            Участники [{supply.participants.length}/{supply.limit}]
          </p>
          {supply.participants.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {supply.participants.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Резерв [{supply.reserve.length}]</p>
          {supply.reserve.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {supply.reserve.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  )
}

export function SupplyPage() {
  const [overview, setOverview] = useState<SupplyOverview | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ channel_id: '', opponent: '', limit: '10', time_str: '' })

  const reload = () => {
    fetchSupplyOverview()
      .then((data) => {
        setOverview(data)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить данные о поставках'))
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
      await createSupply({
        channel_id: form.channel_id,
        opponent: form.opponent.trim(),
        limit: Number(form.limit),
        time_str: form.time_str.trim(),
      })
      setCreating(false)
      setForm({ channel_id: '', opponent: '', limit: '10', time_str: '' })
    })

  if (!overview) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Package size={22} className="text-primary" />
          Сборы на поставку
        </h1>
        <Button variant="primary" onClick={() => setCreating(true)}>
          <Plus size={16} />
          Новый сбор
        </Button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Активные</h2>
        {overview.active.length === 0 && <p className="text-sm text-muted">Активных сборов нет.</p>}
        {overview.active.map((supply) => (
          <SupplyCard
            key={supply.id}
            supply={supply}
            busy={busy}
            onClose={() => act(() => closeSupply(supply.id))}
            onCancel={() => act(() => cancelSupply(supply.id))}
          />
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <Trophy size={16} />
          Топ участников
        </h2>
        {overview.stats.length === 0 && <p className="text-sm text-muted">Статистики пока нет.</p>}
        {overview.stats.length > 0 && (
          <Card>
            <ul className="flex flex-col gap-1">
              {overview.stats.map((row, i) => (
                <li key={row.user_id} className="flex justify-between text-sm">
                  <span className="text-foreground">
                    {i + 1}. {row.display}
                  </span>
                  <span className="text-muted">{row.count}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <XCircle size={16} />
          История
        </h2>
        {overview.history.length === 0 && <p className="text-sm text-muted">Истории пока нет.</p>}
        {overview.history.map((supply) => (
          <SupplyCard key={supply.id} supply={supply} />
        ))}
      </section>

      <Modal open={creating} title="Новый сбор на поставку" onClose={() => setCreating(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="supply-channel">
              Канал публикации
            </label>
            <Select
              id="supply-channel"
              value={form.channel_id}
              onChange={(id) => setForm((f) => ({ ...f, channel_id: id }))}
              options={channels}
              placeholder="Выберите канал"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="supply-opponent">
              Против кого
            </label>
            <input
              id="supply-opponent"
              value={form.opponent}
              onChange={(e) => setForm((f) => ({ ...f, opponent: e.target.value }))}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="supply-limit">
                Лимит участников
              </label>
              <input
                id="supply-limit"
                type="number"
                min={1}
                max={99}
                value={form.limit}
                onChange={(e) => setForm((f) => ({ ...f, limit: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="supply-time">
                Время (ЧЧ:ММ, МСК)
              </label>
              <input
                id="supply-time"
                placeholder="15:10"
                value={form.time_str}
                onChange={(e) => setForm((f) => ({ ...f, time_str: e.target.value }))}
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
              disabled={busy || !form.channel_id || !form.opponent.trim() || !form.time_str.trim()}
            >
              {busy ? 'Создаём…' : 'Создать'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
