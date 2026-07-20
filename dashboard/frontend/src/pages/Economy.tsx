import { Coins, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchCasinoSettings,
  fetchEconomySettings,
  fetchEconomyTop,
  setEconomyBalance,
  updateCasinoSettings,
  updateEconomySettings,
  type CasinoSettings,
  type EconomySettings,
  type EconomyTopEntry,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function EconomyPage() {
  const [settings, setSettings] = useState<EconomySettings | null>(null)
  const [casino, setCasino] = useState<CasinoSettings | null>(null)
  const [top, setTop] = useState<EconomyTopEntry[] | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [editBalances, setEditBalances] = useState<Record<string, string>>({})

  const reloadTop = () => {
    fetchEconomyTop()
      .then(setTop)
      .catch(() => setTop([]))
  }

  useEffect(() => {
    fetchEconomySettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки модуля «Экономика»'))
    fetchCasinoSettings()
      .then(setCasino)
      .catch(() => setError('Не удалось загрузить настройки казино'))
    reloadTop()
  }, [])

  if (!settings || !casino) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateEconomySettings(settings)
      setSettings(updated)
      const updatedCasino = await updateCasinoSettings(casino)
      setCasino(updatedCasino)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  const applyBalance = async (userId: string) => {
    const raw = editBalances[userId]
    const value = Number(raw)
    if (!Number.isInteger(value) || value < 0) return
    try {
      await setEconomyBalance(userId, value)
      setEditBalances((prev) => ({ ...prev, [userId]: '' }))
      reloadTop()
    } catch {
      setError('Не удалось изменить баланс')
    }
  }

  const updateItem = (index: number, patch: Partial<EconomySettings['shop_items'][number]>) => {
    const items = settings.shop_items.map((item, i) => (i === index ? { ...item, ...patch } : item))
    setSettings({ ...settings, shop_items: items })
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Coins size={22} className="text-primary" />
          Экономика
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>
      <p className="text-sm text-muted">
        Серверная валюта: монеты начисляются автоматически как процент от заработанного XP (наследуют все правила
        рейтинга — кулдауны, игнор-листы, множители), тратятся в магазине ролей и на ставках в русской рулетке.
        Команды: /баланс, /перевести, /монеты-топ, /магазин.
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Валюта и начисление</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-name">
              Название валюты (1–30 символов)
            </label>
            <input
              id="eco-name"
              type="text"
              value={settings.currency_name}
              onChange={(e) => setSettings({ ...settings, currency_name: e.target.value })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-emoji">
              Эмодзи валюты
            </label>
            <input
              id="eco-emoji"
              type="text"
              value={settings.currency_emoji}
              onChange={(e) => setSettings({ ...settings, currency_emoji: e.target.value })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-text-rate">
              Монет за текстовый XP, % (0–1000; 50% = 5 монет за 10 XP)
            </label>
            <input
              id="eco-text-rate"
              type="number"
              min={0}
              max={1000}
              value={settings.text_rate_percent}
              onChange={(e) => setSettings({ ...settings, text_rate_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-voice-rate">
              Монет за голосовой XP, % (0–1000)
            </label>
            <input
              id="eco-voice-rate"
              type="number"
              min={0}
              max={1000}
              value={settings.voice_rate_percent}
              onChange={(e) => setSettings({ ...settings, voice_rate_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">Переводы — /перевести</h2>
          <Toggle
            checked={settings.transfer_enabled}
            onChange={(v) => setSettings({ ...settings, transfer_enabled: v })}
            label={settings.transfer_enabled ? 'Разрешены' : 'Запрещены'}
          />
        </div>
        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label className="text-sm text-muted" htmlFor="eco-fee">
            Комиссия перевода, % (0–50)
          </label>
          <input
            id="eco-fee"
            type="number"
            min={0}
            max={50}
            value={settings.transfer_fee_percent}
            onChange={(e) => setSettings({ ...settings, transfer_fee_percent: Number(e.target.value) })}
            className={inputClass}
          />
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">Ставки в русской рулетке</h2>
          <Toggle
            checked={settings.roulette_bets_enabled}
            onChange={(v) => setSettings({ ...settings, roulette_bets_enabled: v })}
            label={settings.roulette_bets_enabled ? 'Разрешены' : 'Запрещены'}
          />
        </div>
        <p className="text-sm text-muted">Выжил — удвоил ставку, погиб — потерял. Ставка списывается до выстрела.</p>
        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label className="text-sm text-muted" htmlFor="eco-max-bet">
            Максимальная ставка (0 — без лимита)
          </label>
          <input
            id="eco-max-bet"
            type="number"
            min={0}
            max={1000000}
            value={settings.roulette_max_bet}
            onChange={(e) => setSettings({ ...settings, roulette_max_bet: Number(e.target.value) })}
            className={inputClass}
          />
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">🎰 Казино — /слоты, /монетка</h2>
          <Toggle
            checked={casino.enabled}
            onChange={(v) => setCasino({ ...casino, enabled: v })}
            label={casino.enabled ? 'Включено' : 'Выключено'}
          />
        </div>
        <p className="text-sm text-muted">
          Слоты (3 барабана, совпадения дают выигрыш) и монетка (орёл/решка). Обе команды делят один кулдаун на
          игрока. Требует включённой «Экономики» выше.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-edge">
              Преимущество казино, % (0–50; срезает выигрыш на этот процент)
            </label>
            <input
              id="casino-edge"
              type="number"
              min={0}
              max={50}
              value={casino.house_edge_percent}
              onChange={(e) => setCasino({ ...casino, house_edge_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-cooldown">
              Кулдаун на игрока, сек (0–300, общий для /слоты и /монетка)
            </label>
            <input
              id="casino-cooldown"
              type="number"
              min={0}
              max={300}
              value={casino.cooldown_sec}
              onChange={(e) => setCasino({ ...casino, cooldown_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-min-bet">
              Минимальная ставка
            </label>
            <input
              id="casino-min-bet"
              type="number"
              min={1}
              value={casino.min_bet}
              onChange={(e) => setCasino({ ...casino, min_bet: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-max-bet">
              Максимальная ставка (0 — без лимита)
            </label>
            <input
              id="casino-max-bet"
              type="number"
              min={0}
              value={casino.max_bet}
              onChange={(e) => setCasino({ ...casino, max_bet: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">🎁 Ежедневный бонус — /daily</h2>
          <Toggle
            checked={settings.daily_bonus_enabled}
            onChange={(v) => setSettings({ ...settings, daily_bonus_enabled: v })}
            label={settings.daily_bonus_enabled ? 'Включено' : 'Выключено'}
          />
        </div>
        <p className="text-sm text-muted">
          Раз в календарный день (МСК) — монеты без активности. Сумма растёт со стриком дней подряд линейно от базы
          до плато на макс. дне, пропуск дня сбрасывает стрик до 1.
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-daily-base">
              База (день 1)
            </label>
            <input
              id="eco-daily-base"
              type="number"
              min={0}
              value={settings.daily_base_amount}
              onChange={(e) => setSettings({ ...settings, daily_base_amount: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-daily-growth">
              Прирост за день
            </label>
            <input
              id="eco-daily-growth"
              type="number"
              min={0}
              value={settings.daily_growth_per_day}
              onChange={(e) => setSettings({ ...settings, daily_growth_per_day: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="eco-daily-max-days">
              Плато на дне (1–365)
            </label>
            <input
              id="eco-daily-max-days"
              type="number"
              min={1}
              max={365}
              value={settings.daily_max_streak_days}
              onChange={(e) => setSettings({ ...settings, daily_max_streak_days: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">🛒 Магазин — /магазин, /косметика</h2>
        <p className="text-sm text-muted">
          До 25 товаров трёх типов. <strong>Роль</strong> выдаётся в Discord сразу; <strong>рамка карточки</strong> и{' '}
          <strong>титул</strong> — косметика для карточки <code className="rounded bg-background px-1 py-0.5 text-xs">/ранг</code>,
          покупатель выбирает купленное командой <code className="rounded bg-background px-1 py-0.5 text-xs">/косметика</code>.
          Монеты списываются сразу; если роль не удалось выдать — возвращаются автоматически.
        </p>
        {settings.shop_items.map((item, index) => (
          <div key={item.id || index} className="flex flex-col gap-2 rounded-control border border-border p-3">
            <div className="grid gap-2 sm:grid-cols-[140px_1fr_120px_40px]">
              <select
                aria-label={`Тип товара ${index + 1}`}
                value={item.type}
                onChange={(e) => updateItem(index, { type: e.target.value as EconomySettings['shop_items'][number]['type'] })}
                className={inputClass}
              >
                <option value="role">Роль</option>
                <option value="frame_color">Рамка карточки</option>
                <option value="title">Титул</option>
              </select>
              <input
                type="text"
                placeholder="Название (видно в магазине)"
                aria-label={`Название товара ${index + 1}`}
                value={item.name}
                onChange={(e) => updateItem(index, { name: e.target.value })}
                className={inputClass}
              />
              <input
                type="number"
                placeholder="Цена"
                aria-label={`Цена товара ${index + 1}`}
                min={1}
                value={item.price || ''}
                onChange={(e) => updateItem(index, { price: Number(e.target.value) })}
                className={inputClass}
              />
              <Button
                variant="ghost"
                aria-label={`Удалить товар ${index + 1}`}
                onClick={() =>
                  setSettings({ ...settings, shop_items: settings.shop_items.filter((_, i) => i !== index) })
                }
              >
                <Trash size={16} />
              </Button>
            </div>
            {item.type === 'role' && (
              <input
                type="text"
                inputMode="numeric"
                placeholder="ID роли"
                aria-label={`ID роли товара ${index + 1}`}
                value={item.role_id}
                onChange={(e) => updateItem(index, { role_id: e.target.value.replace(/\D/g, '') })}
                className={`${inputClass} sm:max-w-xs`}
              />
            )}
            {item.type === 'frame_color' && (
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  aria-label={`Цвет рамки товара ${index + 1}`}
                  value={item.color_hex || '#5865F2'}
                  onChange={(e) => updateItem(index, { color_hex: e.target.value })}
                  className="h-9 w-14 rounded-control border border-border bg-background"
                />
                <input
                  type="text"
                  placeholder="#RRGGBB"
                  aria-label={`Hex-код рамки товара ${index + 1}`}
                  value={item.color_hex}
                  onChange={(e) => updateItem(index, { color_hex: e.target.value })}
                  className={`${inputClass} max-w-[140px]`}
                />
              </div>
            )}
            {item.type === 'title' && (
              <input
                type="text"
                placeholder="Текст титула под именем"
                aria-label={`Текст титула товара ${index + 1}`}
                maxLength={30}
                value={item.title_text}
                onChange={(e) => updateItem(index, { title_text: e.target.value })}
                className={`${inputClass} sm:max-w-xs`}
              />
            )}
          </div>
        ))}
        <div>
          <Button
            variant="secondary"
            disabled={settings.shop_items.length >= 25}
            onClick={() =>
              setSettings({
                ...settings,
                shop_items: [
                  ...settings.shop_items,
                  { id: '', type: 'role', role_id: '', color_hex: '', title_text: '', price: 100, name: '' },
                ],
              })
            }
          >
            <Plus size={16} /> Добавить товар
          </Button>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Топ балансов</h2>
        {top === null && <p className="text-sm text-muted">Загрузка…</p>}
        {top !== null && top.length === 0 && <p className="text-sm text-muted">Пока ни у кого нет монет.</p>}
        {top !== null && top.length > 0 && (
          <ul className="flex flex-col gap-2">
            {top.map((entry) => (
              <li key={entry.user_id} className="flex items-center gap-3 border-t border-border pt-2 first:border-t-0 first:pt-0">
                <span className="min-w-0 flex-1 truncate text-sm text-foreground">{entry.display_name}</span>
                <span className="text-sm text-muted">{entry.balance}</span>
                <input
                  type="number"
                  min={0}
                  placeholder="Новый баланс"
                  aria-label={`Новый баланс ${entry.display_name}`}
                  value={editBalances[entry.user_id] ?? ''}
                  onChange={(e) => setEditBalances((prev) => ({ ...prev, [entry.user_id]: e.target.value }))}
                  className={`${inputClass} w-32`}
                />
                <Button variant="secondary" onClick={() => applyBalance(entry.user_id)}>
                  Применить
                </Button>
              </li>
            ))}
          </ul>
        )}
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
