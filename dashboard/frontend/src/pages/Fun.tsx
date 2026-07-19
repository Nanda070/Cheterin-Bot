import { Confetti } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchFunSettings,
  fetchWordleSettings,
  updateFunSettings,
  updateWordleSettings,
  type FunSettings,
  type WordleSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function FunPage() {
  const [settings, setSettings] = useState<FunSettings | null>(null)
  const [wordle, setWordle] = useState<WordleSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchFunSettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки модуля «Развлечения»'))
    fetchWordleSettings()
      .then(setWordle)
      .catch(() => setError('Не удалось загрузить настройки Вордла'))
  }, [])

  if (!settings || !wordle) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateFunSettings(settings)
      setSettings(updated)
      const updatedWordle = await updateWordleSettings(wordle)
      setWordle(updatedWordle)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Confetti size={22} className="text-primary" />
          Развлечения
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>
      <p className="text-sm text-muted">
        Лёгкие фан-команды для чата. Пока модуль выключен, обе команды отвечают «Модуль отключён».
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">🔫 Русская рулетка — /русская-рулетка</h2>
        <p className="text-sm text-muted">
          Игрок сам жмёт на курок: 1 шанс из 6 «погибнуть». Проигравший получает Discord-таймаут на заданное число
          минут. Игрок рискует добровольно — команда действует только на того, кто её вызвал.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-roulette-timeout">
              Таймаут проигравшему, мин (0 — без наказания, максимум 1440)
            </label>
            <input
              id="fun-roulette-timeout"
              type="number"
              min={0}
              max={1440}
              value={settings.roulette_timeout_minutes}
              onChange={(e) => setSettings({ ...settings, roulette_timeout_minutes: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-roulette-cooldown">
              Кулдаун на игрока, сек (0 — без кулдауна, максимум 3600)
            </label>
            <input
              id="fun-roulette-cooldown"
              type="number"
              min={0}
              max={3600}
              value={settings.roulette_cooldown_sec}
              onChange={(e) => setSettings({ ...settings, roulette_cooldown_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">
          Для выдачи таймаута боту нужно право «Отправлять участников подумать» (Timeout Members). Администраторам
          Discord таймаут выдать нельзя — в этом случае бот честно напишет, что игроку «повезло».
        </p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">🎰 Эмодзи-рулетка — /эмодзи-рулетка</h2>
        <p className="text-sm text-muted">
          Выдаёт случайное эмодзи из кастомных эмодзи сервера. Если своих эмодзи на сервере нет — используется
          стандартный набор. Настроек не требует.
        </p>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">✨ Авто-Эмодзи</h2>
          <Toggle
            checked={settings.auto_emoji_enabled}
            onChange={(v) => setSettings({ ...settings, auto_emoji_enabled: v })}
            label={settings.auto_emoji_enabled ? 'Включено' : 'Выключено'}
          />
        </div>
        <p className="text-sm text-muted">
          Бот изредка ставит случайное серверное эмодзи реакцией на сообщения участников (в любом канале, только на
          сообщения людей) — как в Juniper. Частота управляется шансом и минимальным интервалом на канал, а чтобы
          реакции «не висели долго», бот сам снимает свою реакцию через заданное время.
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-chance">
              Шанс на сообщение, % (1–100)
            </label>
            <input
              id="fun-ae-chance"
              type="number"
              min={1}
              max={100}
              value={settings.auto_emoji_chance_percent}
              onChange={(e) => setSettings({ ...settings, auto_emoji_chance_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-interval">
              Мин. интервал на канал, сек (0–86400)
            </label>
            <input
              id="fun-ae-interval"
              type="number"
              min={0}
              max={86400}
              value={settings.auto_emoji_min_interval_sec}
              onChange={(e) => setSettings({ ...settings, auto_emoji_min_interval_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-remove">
              Снять реакцию через, сек (0 — не снимать, до 3600)
            </label>
            <input
              id="fun-ae-remove"
              type="number"
              min={0}
              max={3600}
              value={settings.auto_emoji_remove_after_sec}
              onChange={(e) => setSettings({ ...settings, auto_emoji_remove_after_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">🟩 Вордл — /вордл</h2>
          <Toggle
            checked={wordle.enabled}
            onChange={(v) => setWordle({ ...wordle, enabled: v })}
            label={wordle.enabled ? 'Вордл включён' : 'Вордл выключен'}
          />
        </div>
        <p className="text-sm text-muted">
          Русский Wordle: каждый день одно общее слово из 5 букв на 6 попыток. Своя доска с буквами видна только
          игроку (ввод через кнопку и модальное окно), а в канал бот публикует живую карточку «X играет» с цветами
          без букв. Тренировка без статистики — /вордл-тренировка, личная статистика — /вордл-стата, топ сервера —
          /вордл-топ. Раз в день бот подводит итоги: серия сервера, 👑 у лучшего результата и кнопка «Играть».
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="wordle-channel">
              ID канала для анонсов и live-карточек (0 — карточки в канале команды, без ежедневных анонсов)
            </label>
            <input
              id="wordle-channel"
              type="number"
              min={0}
              value={wordle.channel_id}
              onChange={(e) => setWordle({ ...wordle, channel_id: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="wordle-time">
              Время ежедневного анонса, МСК (ЧЧ:ММ)
            </label>
            <input
              id="wordle-time"
              type="text"
              placeholder="09:00"
              value={wordle.announce_time}
              onChange={(e) => setWordle({ ...wordle, announce_time: e.target.value })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">
          Слово дня общее для всего сервера и меняется в полночь по МСК. Словарь — существительные из 5 букв,
          буква «ё» считается как «е».
        </p>
      </Card>

      {saved && <p className="text-sm text-primary">{saved}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
