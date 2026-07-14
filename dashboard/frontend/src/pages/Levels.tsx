import { ChartBar, Crown, Gear, IdentificationCard, Microphone, Star, Trash, UsersThree } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import {
  deleteCardBg,
  fetchChannels,
  fetchRoles,
  fetchXpLeaderboard,
  fetchXpOverview,
  resetAllXp,
  resetMemberXp,
  setMemberXp,
  updateXpSettings,
  uploadCardBg,
  type ChannelInfo,
  type RoleInfo,
  type XpLeaderboardEntry,
  type XpLeaderboardPage,
  type XpSettings,
} from '../api/client'
import { ChipPicker } from '../components/ChipPicker'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

type Tab = 'settings' | 'level-rewards' | 'voice-rewards' | 'card' | 'members'

const TABS: { key: Tab; label: string; icon: typeof Gear }[] = [
  { key: 'settings', label: 'Настройки рейтинга', icon: Gear },
  { key: 'level-rewards', label: 'Награды за уровень', icon: Star },
  { key: 'voice-rewards', label: 'Награды за голос', icon: Microphone },
  { key: 'card', label: 'Карточка рейтинга', icon: IdentificationCard },
  { key: 'members', label: 'Участники', icon: UsersThree },
]

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function minutesToParts(minutes: number): { weeks: number; days: number; hours: number } {
  const weeks = Math.floor(minutes / (7 * 24 * 60))
  const days = Math.floor((minutes % (7 * 24 * 60)) / (24 * 60))
  const hours = Math.floor((minutes % (24 * 60)) / 60)
  return { weeks, days, hours }
}

function formatMinutes(minutes: number): string {
  const { weeks, days, hours } = minutesToParts(minutes)
  const parts: string[] = []
  if (weeks) parts.push(`${weeks} нед.`)
  if (days) parts.push(`${days} д.`)
  if (hours) parts.push(`${hours} ч.`)
  return parts.length ? parts.join(' ') : `${minutes} мин.`
}

export function LevelsPage() {
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<XpSettings | null>(null)
  const [memberCount, setMemberCount] = useState(0)
  const [hasCardBg, setHasCardBg] = useState(false)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const [board, setBoard] = useState<XpLeaderboardPage | null>(null)
  const [boardPage, setBoardPage] = useState(1)
  const [boardSearch, setBoardSearch] = useState('')
  const [boardSearchDraft, setBoardSearchDraft] = useState('')
  const [editing, setEditing] = useState<XpLeaderboardEntry | null>(null)
  const [editXp, setEditXp] = useState('')
  const [confirmResetAll, setConfirmResetAll] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const roleOptions = roles.map((r) => ({ id: r.id, name: r.name }))

  useEffect(() => {
    Promise.all([
      fetchXpOverview(),
      fetchChannels().catch(() => [] as ChannelInfo[]),
      fetchRoles().catch(() => [] as RoleInfo[]),
    ])
      .then(([overview, ch, rl]) => {
        setSettings(overview.settings)
        setMemberCount(overview.member_count)
        setHasCardBg(overview.has_card_bg)
        setChannels(ch)
        setRoles(rl)
      })
      .catch(() => setError('Не удалось загрузить настройки рейтинга'))
  }, [])

  useEffect(() => {
    if (tab !== 'members') return
    fetchXpLeaderboard(boardPage, boardSearch)
      .then(setBoard)
      .catch(() => setError('Не удалось загрузить рейтинг'))
  }, [tab, boardPage, boardSearch])

  useEffect(() => {
    const timer = setTimeout(() => {
      setBoardPage(1)
      setBoardSearch(boardSearchDraft)
    }, 300)
    return () => clearTimeout(timer)
  }, [boardSearchDraft])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const patch = (updater: (prev: XpSettings) => XpSettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateXpSettings(settings)
      setSettings(updated.settings)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  const act = async (fn: () => Promise<unknown>, reload = false) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      if (reload && tab === 'members') {
        setBoard(await fetchXpLeaderboard(boardPage, boardSearch))
      }
    } catch {
      setError('Операция не удалась')
    } finally {
      setBusy(false)
    }
  }

  const saveBar = (
    <div className="flex items-center gap-3">
      <Button variant="primary" onClick={save} disabled={busy}>
        {busy ? 'Сохраняем…' : 'Сохранить'}
      </Button>
      {saved && <span className="text-sm text-primary">{saved}</span>}
    </div>
  )

  return (
    <div className="flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ChartBar size={22} className="text-primary" />
          Рейтинг участников
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => patch((p) => ({ ...p, enabled: v }))}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>

      <nav className="flex flex-wrap gap-1 rounded-card border border-border bg-surface p-1.5">
        {TABS.map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 rounded-control px-3 py-1.5 text-sm transition-colors ${
              tab === key ? 'bg-primary-muted text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
            }`}
          >
            <TabIcon size={15} />
            {label}
          </button>
        ))}
      </nav>

      {error && <p className="text-sm text-danger">{error}</p>}

      {tab === 'settings' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Общие</h2>
            <Toggle
              checked={settings.public_leaderboard}
              onChange={(v) => patch((p) => ({ ...p, public_leaderboard: v }))}
              label="Публичная веб-страница рейтинга (/leaderboard)"
            />
            <Toggle
              checked={settings.reset_on_leave}
              onChange={(v) => patch((p) => ({ ...p, reset_on_leave: v }))}
              label="Сбрасывать рейтинг выходящим с сервера участникам"
            />
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">Опыт за текстовые сообщения</h2>
              <Toggle
                checked={settings.text.enabled}
                onChange={(v) => patch((p) => ({ ...p, text: { ...p.text, enabled: v } }))}
              />
            </div>
            <p className="text-xs text-muted">15–25 XP за сообщение, не чаще раза в минуту.</p>
            <ChipPicker
              label="Игнорируемые роли"
              hint="Участники с этими ролями не получают опыт"
              options={roleOptions}
              selected={settings.text.ignored_roles}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, ignored_roles: ids } }))}
            />
            <ChipPicker
              label="Целевые каналы"
              hint="Пусто = все каналы"
              options={channels}
              selected={settings.text.target_channels}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, target_channels: ids } }))}
            />
            <ChipPicker
              label="Игнорируемые каналы"
              options={channels}
              selected={settings.text.ignored_channels}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, ignored_channels: ids } }))}
            />
            <div className="flex items-center gap-3">
              <label className="text-sm text-muted" htmlFor="text-mult">
                Множитель опыта: {settings.text.multiplier}%
              </label>
              <input
                id="text-mult"
                type="range"
                min={0}
                max={300}
                step={5}
                value={settings.text.multiplier}
                onChange={(e) => patch((p) => ({ ...p, text: { ...p.text, multiplier: Number(e.target.value) } }))}
                className="flex-1 accent-[#5865f2]"
              />
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">Опыт за голосовую активность</h2>
              <Toggle
                checked={settings.voice.enabled}
                onChange={(v) => patch((p) => ({ ...p, voice: { ...p.voice, enabled: v } }))}
              />
            </div>
            <p className="text-xs text-muted">
              Опыт получают только активные участники (микрофон и звук включены) и только когда активных в канале
              минимум двое. При N активных каждый получает N-кратный опыт.
            </p>
            <ChipPicker
              label="Игнорируемые роли"
              options={roleOptions}
              selected={settings.voice.ignored_roles}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, ignored_roles: ids } }))}
            />
            <ChipPicker
              label="Целевые каналы"
              hint="Пусто = все голосовые каналы"
              options={channels}
              selected={settings.voice.target_channels}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, target_channels: ids } }))}
            />
            <ChipPicker
              label="Игнорируемые каналы"
              options={channels}
              selected={settings.voice.ignored_channels}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, ignored_channels: ids } }))}
            />
            <div className="flex items-center gap-3">
              <label className="text-sm text-muted" htmlFor="voice-mult">
                Множитель опыта: {settings.voice.multiplier}%
              </label>
              <input
                id="voice-mult"
                type="range"
                min={0}
                max={300}
                step={5}
                value={settings.voice.multiplier}
                onChange={(e) => patch((p) => ({ ...p, voice: { ...p.voice, multiplier: Number(e.target.value) } }))}
                className="flex-1 accent-[#5865f2]"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="voice-max">
                Максимум участников для множителя (защита от фарма)
              </label>
              <input
                id="voice-max"
                type="number"
                min={0}
                max={99}
                value={settings.voice.max_count}
                onChange={(e) => patch((p) => ({ ...p, voice: { ...p.voice, max_count: Number(e.target.value) } }))}
                className={`${inputClass} w-32`}
              />
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">Уведомление о повышении уровня</h2>
              <Toggle
                checked={settings.announce.enabled}
                onChange={(v) => patch((p) => ({ ...p, announce: { ...p.announce, enabled: v } }))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-channel">
                Канал уведомлений (пусто = канал сообщения)
              </label>
              <Select
                id="announce-channel"
                value={settings.announce.channel_id}
                onChange={(id) => patch((p) => ({ ...p, announce: { ...p.announce, channel_id: id } }))}
                options={channels}
                placeholder="Канал сообщения участника"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-template">
                Шаблон сообщения
              </label>
              <textarea
                id="announce-template"
                rows={3}
                value={settings.announce.template}
                onChange={(e) => patch((p) => ({ ...p, announce: { ...p.announce, template: e.target.value } }))}
                className={inputClass}
              />
              <span className="text-xs text-muted">
                {'Переменные: {{member}} — упоминание, {{level}} — уровень, {{roles_added}} — выданные роли'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-delete">
                Удалять сообщение через N секунд (0 = не удалять)
              </label>
              <input
                id="announce-delete"
                type="number"
                min={0}
                max={3600}
                value={settings.announce.delete_after}
                onChange={(e) =>
                  patch((p) => ({ ...p, announce: { ...p.announce, delete_after: Number(e.target.value) } }))
                }
                className={`${inputClass} w-32`}
              />
            </div>
          </Card>

          {saveBar}
        </div>
      )}

      {tab === 'level-rewards' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Роли за достижение уровня</h2>
            {settings.level_rewards.length === 0 && <p className="text-sm text-muted">Наград пока нет.</p>}
            {settings.level_rewards.map((reward, index) => (
              <div key={index} className="flex flex-wrap items-end gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                <div className="flex w-24 flex-col gap-1">
                  <label className="text-xs text-muted">Уровень</label>
                  <input
                    type="number"
                    min={1}
                    max={999}
                    value={reward.level}
                    onChange={(e) =>
                      patch((p) => ({
                        ...p,
                        level_rewards: p.level_rewards.map((r, i) =>
                          i === index ? { ...r, level: Number(e.target.value) } : r,
                        ),
                      }))
                    }
                    className={inputClass}
                  />
                </div>
                <div className="min-w-60 flex-1">
                  <ChipPicker
                    label="Роли"
                    options={roleOptions}
                    selected={reward.role_ids}
                    onChange={(ids) =>
                      patch((p) => ({
                        ...p,
                        level_rewards: p.level_rewards.map((r, i) => (i === index ? { ...r, role_ids: ids } : r)),
                      }))
                    }
                  />
                </div>
                <Button
                  variant="ghost"
                  onClick={() =>
                    patch((p) => ({ ...p, level_rewards: p.level_rewards.filter((_, i) => i !== index) }))
                  }
                >
                  <Trash size={16} />
                </Button>
              </div>
            ))}
            <div>
              <Button
                variant="secondary"
                onClick={() =>
                  patch((p) => ({ ...p, level_rewards: [...p.level_rewards, { level: 5, role_ids: [] }] }))
                }
              >
                + Добавить награду
              </Button>
            </div>
          </Card>
          {saveBar}
        </div>
      )}

      {tab === 'voice-rewards' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Роли за суммарное время в войсе</h2>
            {settings.voice_rewards.length === 0 && <p className="text-sm text-muted">Наград пока нет.</p>}
            {settings.voice_rewards.map((reward, index) => {
              const parts = minutesToParts(reward.minutes)
              const setParts = (weeks: number, days: number, hours: number) => {
                const minutes = Math.max(1, weeks * 7 * 24 * 60 + days * 24 * 60 + hours * 60)
                patch((p) => ({
                  ...p,
                  voice_rewards: p.voice_rewards.map((r, i) => (i === index ? { ...r, minutes } : r)),
                }))
              }
              return (
                <div key={index} className="flex flex-wrap items-end gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                  <div className="flex gap-2">
                    {(['weeks', 'days', 'hours'] as const).map((unit) => (
                      <div key={unit} className="flex w-20 flex-col gap-1">
                        <label className="text-xs text-muted">
                          {unit === 'weeks' ? 'Недели' : unit === 'days' ? 'Дни' : 'Часы'}
                        </label>
                        <input
                          type="number"
                          min={0}
                          value={parts[unit]}
                          onChange={(e) => {
                            const v = Math.max(0, Number(e.target.value))
                            setParts(
                              unit === 'weeks' ? v : parts.weeks,
                              unit === 'days' ? v : parts.days,
                              unit === 'hours' ? v : parts.hours,
                            )
                          }}
                          className={inputClass}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="min-w-60 flex-1">
                    <ChipPicker
                      label={`Роли (порог: ${formatMinutes(reward.minutes)})`}
                      options={roleOptions}
                      selected={reward.role_ids}
                      onChange={(ids) =>
                        patch((p) => ({
                          ...p,
                          voice_rewards: p.voice_rewards.map((r, i) => (i === index ? { ...r, role_ids: ids } : r)),
                        }))
                      }
                    />
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      patch((p) => ({ ...p, voice_rewards: p.voice_rewards.filter((_, i) => i !== index) }))
                    }
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              )
            })}
            <div>
              <Button
                variant="secondary"
                onClick={() =>
                  patch((p) => ({
                    ...p,
                    voice_rewards: [...p.voice_rewards, { minutes: 7 * 24 * 60, role_ids: [] }],
                  }))
                }
              >
                + Добавить награду
              </Button>
            </div>
          </Card>
          {saveBar}
        </div>
      )}

      {tab === 'card' && (
        <Card className="flex flex-col gap-4">
          <h2 className="font-semibold text-foreground">Фон карточки /ранг</h2>
          <p className="text-sm text-muted">
            PNG или JPEG до 5 МБ, рекомендуемый размер 900×260. Фон автоматически затемняется, чтобы текст оставался
            читаемым. {hasCardBg ? 'Сейчас используется пользовательский фон.' : 'Сейчас используется стандартный градиент.'}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                act(async () => {
                  await uploadCardBg(file)
                  setHasCardBg(true)
                  setSaved('Фон загружен.')
                })
              }
              e.target.value = ''
            }}
          />
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => fileInput.current?.click()} disabled={busy}>
              Загрузить фон
            </Button>
            {hasCardBg && (
              <Button
                variant="danger"
                onClick={() =>
                  act(async () => {
                    await deleteCardBg()
                    setHasCardBg(false)
                    setSaved('Фон удалён.')
                  })
                }
                disabled={busy}
              >
                Удалить фон
              </Button>
            )}
          </div>
          {saved && <p className="text-sm text-primary">{saved}</p>}
        </Card>
      )}

      {tab === 'members' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted">Участников сервера в списке: {board?.total ?? memberCount}</p>
            <Button variant="danger" onClick={() => setConfirmResetAll(true)} disabled={busy}>
              Сбросить весь рейтинг
            </Button>
          </div>
          <input
            value={boardSearchDraft}
            onChange={(e) => setBoardSearchDraft(e.target.value)}
            placeholder="Поиск участника…"
            className={inputClass}
          />

          <Card className="p-0">
            {!board && <p className="p-4 text-sm text-muted">Загрузка…</p>}
            {board && board.entries.length === 0 && <p className="p-4 text-sm text-muted">Рейтинг пуст.</p>}
            {board?.entries.map((entry) => (
              <div
                key={entry.user_id}
                className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
              >
                <span className="w-10 text-sm font-medium text-muted">#{entry.rank}</span>
                {entry.avatar ? (
                  <img src={entry.avatar} alt="" className="h-8 w-8 rounded-full" />
                ) : (
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {entry.display.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">
                    {entry.display}
                    {!entry.on_server && <span className="ml-2 text-xs text-muted">(покинул сервер)</span>}
                  </p>
                  <p className="text-xs text-muted">
                    Уровень {entry.level} · {entry.xp} XP · 🔊 {entry.voice_time_text} · ✉️ {entry.messages}
                  </p>
                </div>
                <div className="flex gap-1.5">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setEditing(entry)
                      setEditXp(String(entry.xp))
                    }}
                  >
                    Изменить XP
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => act(() => resetMemberXp(entry.user_id), true)}
                    disabled={busy}
                  >
                    Сбросить
                  </Button>
                </div>
              </div>
            ))}
          </Card>

          {board && board.total > board.page_size && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="ghost" disabled={boardPage <= 1} onClick={() => setBoardPage((p) => p - 1)}>
                ← Назад
              </Button>
              <span className="text-sm text-muted">
                Стр. {board.page} из {Math.ceil(board.total / board.page_size)}
              </span>
              <Button
                variant="ghost"
                disabled={boardPage >= Math.ceil(board.total / board.page_size)}
                onClick={() => setBoardPage((p) => p + 1)}
              >
                Вперёд →
              </Button>
            </div>
          )}
        </div>
      )}

      <Modal open={editing !== null} title={`Изменить XP: ${editing?.display}`} onClose={() => setEditing(null)}>
        <div className="flex flex-col gap-3">
          <input
            type="number"
            min={0}
            value={editXp}
            onChange={(e) => setEditXp(e.target.value)}
            className={inputClass}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setEditing(null)} disabled={busy}>
              Отмена
            </Button>
            <Button
              variant="primary"
              disabled={busy}
              onClick={() =>
                act(async () => {
                  if (editing) await setMemberXp(editing.user_id, Math.max(0, Number(editXp)))
                  setEditing(null)
                }, true)
              }
            >
              Сохранить
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={confirmResetAll} title="Сбросить весь рейтинг?" onClose={() => setConfirmResetAll(false)}>
        <p className="mb-4 text-sm text-muted">
          XP, уровни и время войса всех участников будут обнулены, роли-награды сняты. Это действие необратимо.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmResetAll(false)} disabled={busy}>
            Отмена
          </Button>
          <Button
            variant="danger"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await resetAllXp()
                setConfirmResetAll(false)
              }, true)
            }
          >
            <Crown size={16} />
            Сбросить всё
          </Button>
        </div>
      </Modal>
    </div>
  )
}
