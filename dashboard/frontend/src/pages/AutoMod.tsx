import { Gear, Plus, ShieldWarning, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createEscalationRule,
  deleteEscalationRule,
  fetchAutomod,
  fetchChannels,
  updateAutomodEnabled,
  updateAutomodFilter,
  updateManualWarnDuration,
  type AutomodFilter,
  type AutomodPunishment,
  type AutomodSettings,
  type ChannelInfo,
  type EscalationAction,
  type EscalationRule,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const PUNISHMENT_LABELS: Record<AutomodPunishment, string> = {
  none: 'Ничего',
  warn: 'Выдать предупреждение',
  mute: 'Мут (таймаут)',
  kick: 'Кик',
  ban: 'Бан',
}

const ESCALATION_ACTION_LABELS: Record<EscalationAction, string> = {
  mute: 'Мут (таймаут)',
  kick: 'Кик',
  ban: 'Бан',
}

function minutesToParts(total: number) {
  const days = Math.floor(total / 1440)
  const hours = Math.floor((total % 1440) / 60)
  const minutes = total % 60
  return { days, hours, minutes }
}

function partsToMinutes(days: number, hours: number, minutes: number) {
  return days * 1440 + hours * 60 + minutes
}

function formatDuration(minutes: number): string {
  if (minutes <= 0) return 'бессрочно'
  const { days, hours, minutes: mins } = minutesToParts(minutes)
  return [days && `${days}д`, hours && `${hours}ч`, mins && `${mins}м`].filter(Boolean).join(' ') || '0м'
}

function DurationInputs({ minutes, onChange }: { minutes: number; onChange: (m: number) => void }) {
  const parts = minutesToParts(minutes)
  return (
    <div className="flex gap-2">
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">Дни</label>
        <input
          type="number"
          min={0}
          value={parts.days}
          onChange={(e) => onChange(partsToMinutes(Number(e.target.value) || 0, parts.hours, parts.minutes))}
          className={inputClass}
        />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">Часы</label>
        <input
          type="number"
          min={0}
          max={23}
          value={parts.hours}
          onChange={(e) => onChange(partsToMinutes(parts.days, Number(e.target.value) || 0, parts.minutes))}
          className={inputClass}
        />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">Минуты</label>
        <input
          type="number"
          min={0}
          max={59}
          value={parts.minutes}
          onChange={(e) => onChange(partsToMinutes(parts.days, parts.hours, Number(e.target.value) || 0))}
          className={inputClass}
        />
      </div>
    </div>
  )
}

function FilterExtraFields({
  filterKey,
  draft,
  setDraft,
}: {
  filterKey: string
  draft: AutomodFilter
  setDraft: (patch: Partial<AutomodFilter>) => void
}) {
  const listInput = (value: string[] | undefined, key: 'whitelist_domains' | 'blocklist_keywords' | 'words', label: string) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-muted">{label}</label>
      <input
        defaultValue={(value ?? []).join(', ')}
        onBlur={(e) =>
          setDraft({ [key]: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) } as Partial<AutomodFilter>)
        }
        className={inputClass}
      />
    </div>
  )

  switch (filterKey) {
    case 'links':
      return listInput(draft.whitelist_domains, 'whitelist_domains', 'Разрешённые домены (через запятую)')
    case 'invites':
      return (
        <Toggle
          checked={!!draft.allow_own_server}
          onChange={(v) => setDraft({ allow_own_server: v })}
          label="Разрешить приглашение на свой сервер"
        />
      )
    case 'scam_links':
      return listInput(draft.blocklist_keywords, 'blocklist_keywords', 'Стоп-слова/домены (через запятую)')
    case 'bad_words':
      return listInput(draft.words, 'words', 'Запрещённые слова (через запятую)')
    case 'repeated_text':
      return (
        <>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">Количество одинаковых сообщений</label>
            <input
              type="number"
              min={1}
              value={draft.max_repeats ?? 4}
              onChange={(e) => setDraft({ max_repeats: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <Toggle
            checked={!!draft.consecutive_only}
            onChange={(v) => setDraft({ consecutive_only: v })}
            label="Учитывать только последовательные сообщения"
          />
          <Toggle
            checked={!!draft.reset_on_trigger}
            onChange={(v) => setDraft({ reset_on_trigger: v })}
            label="Сбрасывать счётчик флуда при срабатывании"
          />
        </>
      )
    case 'caps_lock':
      return (
        <div className="flex gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted">Макс. % капса</label>
            <input
              type="number"
              min={1}
              max={100}
              value={draft.max_percent ?? 70}
              onChange={(e) => setDraft({ max_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted">Мин. длина сообщения</label>
            <input
              type="number"
              min={0}
              value={draft.min_length ?? 10}
              onChange={(e) => setDraft({ min_length: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      )
    case 'emoji_spam':
    case 'mentions':
    case 'zalgo': {
      const label =
        filterKey === 'emoji_spam' ? 'Макс. число эмодзи' : filterKey === 'mentions' ? 'Макс. число упоминаний' : 'Макс. число zalgo-символов'
      return (
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{label}</label>
          <input
            type="number"
            min={1}
            value={draft.max_count ?? 5}
            onChange={(e) => setDraft({ max_count: Number(e.target.value) })}
            className={inputClass}
          />
        </div>
      )
    }
    default:
      return null
  }
}

function FilterModal({
  filterKey,
  filter,
  channels,
  onClose,
  onSaved,
}: {
  filterKey: string
  filter: AutomodFilter
  channels: ChannelInfo[]
  onClose: () => void
  onSaved: () => void
}) {
  const [draft, setDraftState] = useState<AutomodFilter>(filter)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const setDraft = (patch: Partial<AutomodFilter>) => setDraftState((prev) => ({ ...prev, ...patch }))

  const save = async () => {
    setBusy(true)
    setError('')
    try {
      await updateAutomodFilter(filterKey, draft)
      onSaved()
      onClose()
    } catch {
      setError('Не удалось сохранить настройки фильтра')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open title={filter.label} onClose={onClose}>
      <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto pr-1">
        <Toggle checked={draft.delete_message} onChange={(v) => setDraft({ delete_message: v })} label="Удалять сообщение с нарушением" />

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">Мера пресечения</label>
          <Select
            value={draft.punishment}
            onChange={(id) => setDraft({ punishment: id as AutomodPunishment })}
            options={Object.entries(PUNISHMENT_LABELS).map(([id, name]) => ({ id, name }))}
          />
        </div>

        {draft.punishment !== 'none' && draft.punishment !== 'kick' && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">
              {draft.punishment === 'warn' ? 'Срок действия предупреждения (0 = бессрочно)' : 'Длительность (0 = бессрочно, макс. для таймаута: 28 дней)'}
            </label>
            <DurationInputs minutes={draft.duration_minutes} onChange={(m) => setDraft({ duration_minutes: m })} />
          </div>
        )}

        <FilterExtraFields filterKey={filterKey} draft={draft} setDraft={setDraft} />

        <div className="border-t border-border pt-3">
          <Toggle checked={draft.notify_member} onChange={(v) => setDraft({ notify_member: v })} label="Уведомлять участника о нарушении" />
        </div>

        {draft.notify_member && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">Канал для отправки (текущий, если не указан)</label>
              <Select
                value={draft.notify_channel_id}
                onChange={(id) => setDraft({ notify_channel_id: id })}
                options={channels}
                placeholder="Текущий канал"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{'Шаблон сообщения ({{member}}, {{reason}})'}</label>
              <textarea
                rows={3}
                value={draft.notify_template}
                onChange={(e) => setDraft({ notify_template: e.target.value })}
                className={inputClass}
              />
            </div>
          </>
        )}

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Отмена
          </Button>
          <Button variant="primary" onClick={save} disabled={busy}>
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function FilterCard({
  filter,
  onToggle,
  onOpenSettings,
}: {
  filter: AutomodFilter
  onToggle: (v: boolean) => void
  onOpenSettings: () => void
}) {
  return (
    <Card className="flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">{filter.label}</p>
          <p className="text-xs text-muted">{filter.description}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Toggle checked={filter.enabled} onChange={onToggle} />
          <button
            type="button"
            onClick={onOpenSettings}
            aria-label={`Настройки фильтра ${filter.label}`}
            className="cursor-pointer text-muted transition-colors hover:text-foreground"
          >
            <Gear size={18} />
          </button>
        </div>
      </div>
    </Card>
  )
}

function EscalationSection({
  escalation,
  busy,
  onCreate,
  onDelete,
}: {
  escalation: EscalationRule[]
  busy: boolean
  onCreate: (input: { count: number; action: EscalationAction; duration_minutes: number }) => Promise<unknown>
  onDelete: (id: string) => Promise<unknown>
}) {
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ count: '3', action: 'mute' as EscalationAction, duration_minutes: 1440 })

  const submit = async () => {
    await onCreate({ count: Number(form.count), action: form.action, duration_minutes: form.duration_minutes })
    setAdding(false)
    setForm({ count: '3', action: 'mute', duration_minutes: 1440 })
  }

  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Эскалация по количеству предупреждений</h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={15} />
          Добавить порог
        </Button>
      </div>

      {escalation.length === 0 && (
        <p className="text-sm text-muted">Порогов не задано — накопление предупреждений ни к чему не приводит автоматически.</p>
      )}

      {escalation
        .slice()
        .sort((a, b) => a.count - b.count)
        .map((rule) => (
          <div key={rule.id} className="flex items-center justify-between gap-3 border-b border-border pb-2 last:border-b-0">
            <p className="text-sm text-foreground">
              {rule.count} предупрежд{rule.count === 1 ? 'ение' : 'ений'} → {ESCALATION_ACTION_LABELS[rule.action]} (
              {formatDuration(rule.duration_minutes)})
            </p>
            <button
              type="button"
              onClick={() => onDelete(rule.id)}
              disabled={busy}
              aria-label={`Удалить порог ${rule.count}`}
              className="cursor-pointer text-muted transition-colors hover:text-danger"
            >
              <Trash size={16} />
            </button>
          </div>
        ))}

      <Modal open={adding} title="Новый порог эскалации" onClose={() => setAdding(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="escalation-count">
              Количество активных предупреждений
            </label>
            <input
              id="escalation-count"
              type="number"
              min={1}
              value={form.count}
              onChange={(e) => setForm((f) => ({ ...f, count: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">Действие</label>
            <Select
              value={form.action}
              onChange={(id) => setForm((f) => ({ ...f, action: id as EscalationAction }))}
              options={Object.entries(ESCALATION_ACTION_LABELS).map(([id, name]) => ({ id, name }))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">Длительность (0 = бессрочно, макс. для таймаута: 28 дней)</label>
            <DurationInputs minutes={form.duration_minutes} onChange={(m) => setForm((f) => ({ ...f, duration_minutes: m }))} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              Отмена
            </Button>
            <Button variant="primary" onClick={submit} disabled={!form.count}>
              Добавить
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}

export function AutoModPage() {
  const [settings, setSettings] = useState<AutomodSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [manualWarnDuration, setManualWarnDuration] = useState(0)

  const reload = () =>
    fetchAutomod()
      .then((data) => {
        setSettings(data)
        setManualWarnDuration(data.manual_warn_duration_minutes)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить настройки автомодерации'))

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
      await reload()
    } catch {
      setError('Операция не удалась')
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <ShieldWarning size={22} className="text-primary" />
            Автомодерация
          </h1>
          <p className="mt-1 text-sm text-muted">
            Фильтры сообщений с настраиваемыми наказаниями и эскалацией по предупреждениям. Выключена по умолчанию.
          </p>
        </div>
        <Toggle checked={settings.enabled} onChange={(v) => act(() => updateAutomodEnabled(v))} label="Автомодерация включена" disabled={busy} />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(settings.filters).map(([key, filter]) => (
          <FilterCard
            key={key}
            filter={filter}
            onToggle={(v) => act(() => updateAutomodFilter(key, { enabled: v }))}
            onOpenSettings={() => setEditingKey(key)}
          />
        ))}
      </div>

      <EscalationSection
        escalation={settings.escalation}
        busy={busy}
        onCreate={(input) => act(() => createEscalationRule(input))}
        onDelete={(id) => act(() => deleteEscalationRule(id))}
      />

      <Card className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Срок ручных предупреждений</h2>
        <p className="text-sm text-muted">
          Действует для предупреждений, выданных вручную (/warn, дашборд) — у предупреждений от фильтров свой срок,
          настраиваемый в каждом фильтре отдельно.
        </p>
        <DurationInputs minutes={manualWarnDuration} onChange={setManualWarnDuration} />
        <div>
          <Button variant="primary" onClick={() => act(() => updateManualWarnDuration(manualWarnDuration))} disabled={busy}>
            Сохранить
          </Button>
        </div>
      </Card>

      {editingKey && (
        <FilterModal
          filterKey={editingKey}
          filter={settings.filters[editingKey]}
          channels={channels}
          onClose={() => setEditingKey(null)}
          onSaved={reload}
        />
      )}
    </div>
  )
}
