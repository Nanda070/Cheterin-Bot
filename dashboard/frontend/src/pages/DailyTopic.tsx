import { Lightbulb, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createDailyTopic,
  deleteDailyTopic,
  fetchChannels,
  fetchDailyTopic,
  postDailyTopicNow,
  updateDailyTopic,
  updateDailyTopicSettings,
  type ChannelInfo,
  type DailyTopicSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function DailyTopicPage() {
  const [settings, setSettings] = useState<DailyTopicSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  const [enabled, setEnabled] = useState(false)
  const [channelId, setChannelId] = useState('')
  const [postTimes, setPostTimes] = useState<string[]>([])
  const [newTime, setNewTime] = useState('')

  const [addingTopic, setAddingTopic] = useState(false)
  const [topicDraft, setTopicDraft] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editDraft, setEditDraft] = useState('')

  const reload = () =>
    fetchDailyTopic()
      .then((data) => {
        setSettings(data)
        setEnabled(data.enabled)
        setChannelId(data.channel_id)
        setPostTimes(data.post_times)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить настройки рубрики'))

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
  }, [])

  const act = async (fn: () => Promise<unknown>, errorMessage = 'Операция не удалась') => {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await fn()
      await reload()
    } catch {
      setError(errorMessage)
    } finally {
      setBusy(false)
    }
  }

  const saveSettings = () => act(() => updateDailyTopicSettings({ enabled, channel_id: channelId, post_times: postTimes }))

  const addTime = () => {
    const value = newTime.trim()
    if (!value || postTimes.includes(value)) return
    setPostTimes((prev) => [...prev, value].sort())
    setNewTime('')
  }

  const removeTime = (time: string) => setPostTimes((prev) => prev.filter((t) => t !== time))

  const submitNewTopic = () =>
    act(async () => {
      await createDailyTopic(topicDraft.trim())
      setAddingTopic(false)
      setTopicDraft('')
    })

  const saveEdit = (id: string) =>
    act(async () => {
      await updateDailyTopic(id, editDraft.trim())
      setEditingId(null)
    })

  const postNow = () =>
    act(async () => {
      await postDailyTopicNow()
      setNotice('Тема дня опубликована.')
    }, 'Не удалось опубликовать — проверьте канал и список тем')

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Lightbulb size={22} className="text-primary" />
          Ежедневная рубрика
        </h1>
        <p className="mt-1 text-sm text-muted">
          Бот сам публикует вопрос/тему дня в заданный канал по расписанию, чтобы разговор не затухал в тихие дни.
          Выключена по умолчанию.
        </p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {notice && <p className="text-sm text-primary">{notice}</p>}

      <Card className="flex flex-col gap-4">
        <Toggle checked={enabled} onChange={setEnabled} label="Рубрика включена" disabled={busy} />

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">Канал публикации</label>
          <Select value={channelId} onChange={setChannelId} options={channels} placeholder="Канал не выбран" />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-muted">
            Время публикации (МСК) — каждый день бот случайно выбирает одно из них
          </label>
          <div className="flex flex-wrap gap-2">
            {postTimes.length === 0 && <span className="text-sm text-muted">Время не задано</span>}
            {postTimes.map((time) => (
              <span
                key={time}
                className="flex items-center gap-1.5 rounded-control border border-border bg-surface-hover px-2.5 py-1 text-sm text-foreground"
              >
                {time}
                <button
                  type="button"
                  onClick={() => removeTime(time)}
                  aria-label={`Удалить время ${time}`}
                  className="text-muted hover:text-danger"
                >
                  <Trash size={13} />
                </button>
              </span>
            ))}
          </div>
          <div className="mt-1 flex gap-2">
            <input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)} className={`${inputClass} w-36`} />
            <Button variant="secondary" onClick={addTime} disabled={!newTime}>
              <Plus size={15} />
              Добавить время
            </Button>
          </div>
        </div>

        <div className="flex justify-between gap-2 border-t border-border pt-3">
          <Button
            variant="secondary"
            onClick={postNow}
            disabled={busy || !settings.channel_id || settings.topics.length === 0}
          >
            Опубликовать сейчас
          </Button>
          <Button variant="primary" onClick={saveSettings} disabled={busy}>
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </Button>
        </div>
      </Card>

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Темы дня ({settings.topics.length})</h2>
          <Button variant="primary" onClick={() => setAddingTopic(true)}>
            <Plus size={16} />
            Добавить тему
          </Button>
        </div>

        {settings.topics.length === 0 && (
          <Card>
            <p className="text-sm text-muted">Тем пока нет — добавьте хотя бы одну, чтобы включить рубрику.</p>
          </Card>
        )}

        {settings.topics.map((topic) => (
          <Card key={topic.id} className="flex flex-col gap-2">
            {editingId === topic.id ? (
              <>
                <textarea rows={2} value={editDraft} onChange={(e) => setEditDraft(e.target.value)} className={inputClass} />
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setEditingId(null)} disabled={busy}>
                    Отмена
                  </Button>
                  <Button variant="primary" onClick={() => saveEdit(topic.id)} disabled={busy || !editDraft.trim()}>
                    Сохранить
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-foreground">{topic.text}</p>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(topic.id)
                      setEditDraft(topic.text)
                    }}
                    className="text-xs text-primary hover:underline"
                  >
                    Изменить
                  </button>
                  <button
                    type="button"
                    onClick={() => act(() => deleteDailyTopic(topic.id))}
                    className="text-muted transition-colors hover:text-danger"
                    aria-label="Удалить тему"
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </section>

      <Modal open={addingTopic} title="Новая тема дня" onClose={() => setAddingTopic(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="daily-topic-text">
              Текст темы/вопроса
            </label>
            <textarea id="daily-topic-text" rows={3} value={topicDraft} onChange={(e) => setTopicDraft(e.target.value)} className={inputClass} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAddingTopic(false)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={submitNewTopic} disabled={busy || !topicDraft.trim()}>
              {busy ? 'Добавляем…' : 'Добавить'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
