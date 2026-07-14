import { Broadcast, Plus, Trash, TwitchLogo, YoutubeLogo } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createStreamSubscription,
  deleteStreamSubscription,
  fetchChannels,
  fetchRoles,
  fetchStreams,
  updateStreamSubscription,
  type ChannelInfo,
  type RoleInfo,
  type StreamSubscription,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function PlatformIcon({ platform }: { platform: 'twitch' | 'youtube' }) {
  return platform === 'twitch' ? (
    <TwitchLogo size={20} weight="fill" className="text-[#9146ff]" />
  ) : (
    <YoutubeLogo size={20} weight="fill" className="text-[#ff0000]" />
  )
}

export function StreamsPage() {
  const [subs, setSubs] = useState<StreamSubscription[] | null>(null)
  const [twitchConfigured, setTwitchConfigured] = useState(true)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const [adding, setAdding] = useState(false)
  const [addForm, setAddForm] = useState({ platform: 'twitch' as 'twitch' | 'youtube', query: '', channel_id: '' })
  const [expanded, setExpanded] = useState<string | null>(null)
  const [keywordsDraft, setKeywordsDraft] = useState('')

  const reload = () =>
    fetchStreams()
      .then((data) => {
        setSubs(data.subscriptions)
        setTwitchConfigured(data.twitch_configured)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить подписки'))

  useEffect(() => {
    reload()
    fetchChannels().then(setChannels).catch(() => setChannels([]))
    fetchRoles().then(setRoles).catch(() => setRoles([]))
  }, [])

  if (!subs) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      await reload()
    } catch (e) {
      const message = e instanceof Error ? e.message : ''
      setError(
        message === 'channel_not_found'
          ? 'Канал не найден — проверьте имя или ссылку'
          : message === 'already_subscribed'
            ? 'Подписка на этот канал уже существует'
            : message === 'twitch_not_configured'
              ? 'Twitch API не настроен: добавьте TWITCH_CLIENT_ID и TWITCH_CLIENT_SECRET в .env'
              : 'Операция не удалась',
      )
    } finally {
      setBusy(false)
    }
  }

  const patchSub = (id: string, fields: Parameters<typeof updateStreamSubscription>[1]) =>
    act(() => updateStreamSubscription(id, fields))

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Broadcast size={22} className="text-primary" />
          Публикации и подписки
        </h1>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={16} />
          Подписаться
        </Button>
      </div>

      {!twitchConfigured && (
        <Card>
          <p className="text-sm text-warning">
            ⚠️ Twitch API не настроен. Зарегистрируйте приложение на dev.twitch.tv и добавьте TWITCH_CLIENT_ID и
            TWITCH_CLIENT_SECRET в .env — до этого работают только YouTube-подписки.
          </p>
        </Card>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      {subs.length === 0 && (
        <Card>
          <p className="text-sm text-muted">
            Подписок пока нет. Добавьте стримера — участники будут получать уведомления о начале трансляций и новых
            видео.
          </p>
        </Card>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {subs.map((sub) => (
          <Card key={sub.id} className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              {sub.avatar_url ? (
                <img src={sub.avatar_url} alt="" className="h-10 w-10 rounded-full" />
              ) : (
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-hover">
                  <PlatformIcon platform={sub.platform} />
                </span>
              )}
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1.5 truncate text-sm font-semibold text-foreground">
                  <PlatformIcon platform={sub.platform} />
                  {sub.display_name}
                </p>
                <p className="text-xs text-muted">{sub.platform === 'twitch' ? 'Канал Twitch.tv' : 'Канал YouTube'}</p>
              </div>
              <Toggle checked={sub.enabled} onChange={(v) => patchSub(sub.id, { enabled: v })} disabled={busy} />
              <button
                type="button"
                onClick={() => act(() => deleteStreamSubscription(sub.id))}
                className="text-muted transition-colors hover:text-danger"
                aria-label="Удалить подписку"
              >
                <Trash size={17} />
              </button>
            </div>

            <button
              type="button"
              onClick={() => {
                setExpanded(expanded === sub.id ? null : sub.id)
                setKeywordsDraft(sub.keywords.join(', '))
              }}
              className="self-start text-xs text-primary hover:underline"
            >
              {expanded === sub.id ? 'Скрыть настройки' : 'Настройки уведомления'}
            </button>

            {expanded === sub.id && (
              <div className="flex flex-col gap-3 border-t border-border pt-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted">Канал публикации</label>
                  <Select
                    value={sub.channel_id}
                    onChange={(id) => patchSub(sub.id, { channel_id: id })}
                    options={channels}
                    placeholder="Не выбран"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted">Роль для пинга</label>
                  <Select
                    value={sub.ping_role_id}
                    onChange={(id) => patchSub(sub.id, { ping_role_id: id })}
                    options={roles}
                    placeholder="Без пинга"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted">Шаблон сообщения (пусто = стандартный)</label>
                  <textarea
                    rows={3}
                    defaultValue={sub.template}
                    onBlur={(e) => e.target.value !== sub.template && patchSub(sub.id, { template: e.target.value })}
                    className={inputClass}
                  />
                  <span className="text-[11px] text-muted">
                    {'Переменные: {{channel}}, {{stream}} — название, {{game}}, {{channel.url}}'}
                  </span>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted">Ключевые слова в названии (через запятую)</label>
                  <input
                    value={keywordsDraft}
                    onChange={(e) => setKeywordsDraft(e.target.value)}
                    onBlur={() =>
                      patchSub(sub.id, {
                        keywords: keywordsDraft
                          .split(',')
                          .map((k) => k.trim())
                          .filter(Boolean),
                      })
                    }
                    placeholder="например: #дота, турнир"
                    className={inputClass}
                  />
                </div>
                <div className="flex gap-3">
                  <div className="flex flex-1 flex-col gap-1">
                    <label className="text-xs text-muted">Режим фильтра</label>
                    <Select
                      value={sub.keyword_mode}
                      onChange={(id) => patchSub(sub.id, { keyword_mode: id as 'any' | 'all' })}
                      options={[
                        { id: 'any', name: 'Любое из слов' },
                        { id: 'all', name: 'Все слова' },
                      ]}
                    />
                  </div>
                  <div className="flex flex-1 flex-col gap-1">
                    <label className="text-xs text-muted">Мин. интервал (минут)</label>
                    <input
                      type="number"
                      min={0}
                      max={10080}
                      defaultValue={sub.min_interval_minutes}
                      onBlur={(e) => {
                        const v = Math.max(0, Number(e.target.value))
                        if (v !== sub.min_interval_minutes) patchSub(sub.id, { min_interval_minutes: v })
                      }}
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>

      <Modal open={adding} title="Новая подписка" onClose={() => setAdding(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex gap-2">
            {(['twitch', 'youtube'] as const).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setAddForm((f) => ({ ...f, platform: p }))}
                className={`flex flex-1 items-center justify-center gap-2 rounded-control border px-3 py-2 text-sm transition-colors ${
                  addForm.platform === p
                    ? 'border-primary/60 bg-primary-muted text-foreground'
                    : 'border-border bg-background text-muted hover:text-foreground'
                }`}
              >
                <PlatformIcon platform={p} />
                {p === 'twitch' ? 'Twitch' : 'YouTube'}
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="stream-query">
              {addForm.platform === 'twitch' ? 'Логин стримера или ссылка на канал' : 'Ссылка на канал, @handle или ID'}
            </label>
            <input
              id="stream-query"
              value={addForm.query}
              onChange={(e) => setAddForm((f) => ({ ...f, query: e.target.value }))}
              placeholder={addForm.platform === 'twitch' ? 'cheterin' : '@cheterin или UC…'}
              className={inputClass}
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="stream-channel">
              Канал для уведомлений
            </label>
            <Select
              id="stream-channel"
              value={addForm.channel_id}
              onChange={(id) => setAddForm((f) => ({ ...f, channel_id: id }))}
              options={channels}
              placeholder="Выберите канал"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)} disabled={busy}>
              Отмена
            </Button>
            <Button
              variant="primary"
              disabled={busy || !addForm.query.trim() || !addForm.channel_id}
              onClick={() =>
                act(async () => {
                  await createStreamSubscription({
                    platform: addForm.platform,
                    query: addForm.query.trim(),
                    channel_id: addForm.channel_id,
                  })
                  setAdding(false)
                  setAddForm({ platform: 'twitch', query: '', channel_id: '' })
                })
              }
            >
              {busy ? 'Проверяем…' : 'Подписаться'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
