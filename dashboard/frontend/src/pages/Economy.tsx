import { Coins, Gear, Plus, Trash, UsersThree } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  fetchEconomySettings,
  fetchEconomyTop,
  fetchEconomyWeeklyReport,
  resetAllEconomyBalances,
  setEconomyBalance,
  updateEconomySettings,
  type EconomySettings,
  type EconomyTopEntry,
  type EconomyWeeklyReportRow,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

type Tab = 'settings' | 'balances'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function EconomyPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<EconomySettings | null>(null)
  const [top, setTop] = useState<EconomyTopEntry[] | null>(null)
  const [weeklyRows, setWeeklyRows] = useState<EconomyWeeklyReportRow[] | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [editBalances, setEditBalances] = useState<Record<string, string>>({})
  const [confirmResetAll, setConfirmResetAll] = useState(false)

  const tabs = useMemo(
    (): { key: Tab; label: string; icon: typeof Gear }[] => [
      { key: 'settings', label: t('economy.tab.settings'), icon: Gear },
      { key: 'balances', label: t('economy.tab.balances'), icon: UsersThree },
    ],
    [t],
  )

  const reloadTop = () => {
    fetchEconomyTop()
      .then(setTop)
      .catch(() => setTop([]))
  }

  const reloadWeekly = () => {
    fetchEconomyWeeklyReport()
      .then((r) => setWeeklyRows(r.rows))
      .catch(() => setWeeklyRows([]))
  }

  useEffect(() => {
    fetchEconomySettings()
      .then((s) =>
        setSettings({
          ...s,
          weekly_report_enabled: s.weekly_report_enabled ?? false,
          weekly_report_channel_id: s.weekly_report_channel_id ?? '',
          weekly_report_days: s.weekly_report_days ?? 7,
        }),
      )
      .catch(() => setError(t('economy.errorLoad')))
    reloadWeekly()
  }, [t])

  useEffect(() => {
    if (tab !== 'balances') return
    setTop(null)
    reloadTop()
  }, [tab])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateEconomySettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'economy.errorSave'))
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
    } catch (err) {
      setError(formatApiError(err, t, 'economy.errorBalance'))
    }
  }

  const updateItem = (index: number, patch: Partial<EconomySettings['shop_items'][number]>) => {
    const items = settings.shop_items.map((item, i) => (i === index ? { ...item, ...patch } : item))
    setSettings({ ...settings, shop_items: items })
  }

  const resetAll = async () => {
    setBusy(true)
    setError('')
    try {
      await resetAllEconomyBalances()
      setConfirmResetAll(false)
      setEditBalances({})
      reloadTop()
    } catch (err) {
      setError(formatApiError(err, t, 'economy.errorBalance'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Coins size={22} className="text-primary" />
          {t('economy.title')}
        </h1>
        {tab === 'settings' && (
          <Toggle
            checked={settings.enabled}
            onChange={(v) => setSettings({ ...settings, enabled: v })}
            label={settings.enabled ? t('economy.moduleEnabled') : t('economy.moduleDisabled')}
          />
        )}
      </div>

      <nav className="flex flex-wrap gap-1 rounded-card border border-border bg-surface p-1.5">
        {tabs.map(({ key, label, icon: TabIcon }) => (
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

      {tab === 'settings' && <p className="text-sm text-muted">{t('economy.intro')}</p>}

      {error && <p className="text-sm text-danger">{error}</p>}

      {tab === 'settings' && (
        <>
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('economy.currencySection')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="eco-name">
                  {t('economy.currencyName')}
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
                  {t('economy.currencyEmoji')}
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
                  {t('economy.textRate')}
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
                  {t('economy.voiceRate')}
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
              <h2 className="font-semibold text-foreground">{t('economy.transfers')}</h2>
              <Toggle
                checked={settings.transfer_enabled}
                onChange={(v) => setSettings({ ...settings, transfer_enabled: v })}
                label={settings.transfer_enabled ? t('economy.allowed') : t('economy.forbidden')}
              />
            </div>
            <div className="flex flex-col gap-1 sm:max-w-xs">
              <label className="text-sm text-muted" htmlFor="eco-fee">
                {t('economy.transferFee')}
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
              <h2 className="font-semibold text-foreground">{t('economy.dailyBonus')}</h2>
              <Toggle
                checked={settings.daily_bonus_enabled}
                onChange={(v) => setSettings({ ...settings, daily_bonus_enabled: v })}
                label={settings.daily_bonus_enabled ? t('economy.enabled') : t('economy.disabled')}
              />
            </div>
            <p className="text-sm text-muted">{t('economy.dailyHint')}</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="eco-daily-base">
                  {t('economy.dailyBase')}
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
                  {t('economy.dailyGrowth')}
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
                  {t('economy.dailyMaxDays')}
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
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('economy.weeklyReport')}</h2>
              <Toggle
                checked={settings.weekly_report_enabled}
                onChange={(v) => setSettings({ ...settings, weekly_report_enabled: v })}
                label={settings.weekly_report_enabled ? t('economy.enabled') : t('economy.disabled')}
              />
            </div>
            <p className="text-sm text-muted">{t('economy.weeklyHint')}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="eco-weekly-channel">
                  {t('economy.weeklyChannel')}
                </label>
                <input
                  id="eco-weekly-channel"
                  type="text"
                  inputMode="numeric"
                  placeholder={t('economy.weeklyChannelPlaceholder')}
                  value={settings.weekly_report_channel_id}
                  onChange={(e) =>
                    setSettings({ ...settings, weekly_report_channel_id: e.target.value.replace(/\D/g, '') })
                  }
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="eco-weekly-days">
                  {t('economy.weeklyDays')}
                </label>
                <input
                  id="eco-weekly-days"
                  type="number"
                  min={1}
                  max={30}
                  value={settings.weekly_report_days}
                  onChange={(e) => setSettings({ ...settings, weekly_report_days: Number(e.target.value) })}
                  className={inputClass}
                />
              </div>
            </div>
            {weeklyRows === null && <p className="text-sm text-muted">{t('common.loading')}</p>}
            {weeklyRows !== null && weeklyRows.length === 0 && (
              <p className="text-sm text-muted">{t('economy.weeklyEmpty')}</p>
            )}
            {weeklyRows !== null && weeklyRows.length > 0 && (
              <ul className="flex flex-col gap-1 text-sm">
                {weeklyRows.slice(0, 15).map((row) => (
                  <li
                    key={row.user_id}
                    className="flex justify-between gap-2 border-t border-border pt-1 first:border-t-0 first:pt-0"
                  >
                    <span className="truncate text-foreground">{row.display_name}</span>
                    <span className="shrink-0 text-muted">
                      +{row.earned} / −{row.spent} ({row.net >= 0 ? '+' : ''}
                      {row.net})
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('economy.shop')}</h2>
            <p className="text-sm text-muted">{t('economy.shopHint')}</p>
            {settings.shop_items.map((item, index) => (
              <div key={item.id || index} className="flex flex-col gap-2 rounded-control border border-border p-3">
                <div className="grid gap-2 sm:grid-cols-[140px_1fr_120px_40px]">
                  <select
                    aria-label={t('economy.itemTypeAria', { index: index + 1 })}
                    value={item.type}
                    onChange={(e) =>
                      updateItem(index, { type: e.target.value as EconomySettings['shop_items'][number]['type'] })
                    }
                    className={inputClass}
                  >
                    <option value="role">{t('economy.itemType.role')}</option>
                    <option value="frame_color">{t('economy.itemType.frame')}</option>
                    <option value="title">{t('economy.itemType.title')}</option>
                  </select>
                  <input
                    type="text"
                    placeholder={t('economy.itemNamePlaceholder')}
                    aria-label={t('economy.itemNameAria', { index: index + 1 })}
                    value={item.name}
                    onChange={(e) => updateItem(index, { name: e.target.value })}
                    className={inputClass}
                  />
                  <input
                    type="number"
                    placeholder={t('economy.pricePlaceholder')}
                    aria-label={t('economy.priceAria', { index: index + 1 })}
                    min={1}
                    value={item.price || ''}
                    onChange={(e) => updateItem(index, { price: Number(e.target.value) })}
                    className={inputClass}
                  />
                  <Button
                    variant="ghost"
                    aria-label={t('economy.deleteItemAria', { index: index + 1 })}
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
                    placeholder={t('economy.roleIdPlaceholder')}
                    aria-label={t('economy.roleIdAria', { index: index + 1 })}
                    value={item.role_id}
                    onChange={(e) => updateItem(index, { role_id: e.target.value.replace(/\D/g, '') })}
                    className={`${inputClass} sm:max-w-xs`}
                  />
                )}
                {item.type === 'frame_color' && (
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      aria-label={t('economy.frameColorAria', { index: index + 1 })}
                      value={item.color_hex || '#5865F2'}
                      onChange={(e) => updateItem(index, { color_hex: e.target.value })}
                      className="h-9 w-14 rounded-control border border-border bg-background"
                    />
                    <input
                      type="text"
                      placeholder={t('economy.frameHexPlaceholder')}
                      aria-label={t('economy.frameHexAria', { index: index + 1 })}
                      value={item.color_hex}
                      onChange={(e) => updateItem(index, { color_hex: e.target.value })}
                      className={`${inputClass} max-w-[140px]`}
                    />
                  </div>
                )}
                {item.type === 'title' && (
                  <input
                    type="text"
                    placeholder={t('economy.titlePlaceholder')}
                    aria-label={t('economy.titleAria', { index: index + 1 })}
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
                <Plus size={16} /> {t('economy.addItem')}
              </Button>
            </div>
          </Card>

          {saved && <p className="text-sm text-primary">{saved}</p>}
          <div>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? t('common.saving') : t('common.save')}
            </Button>
          </div>
        </>
      )}

      {tab === 'balances' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-semibold text-foreground">{t('economy.topBalances')}</h2>
            <Button variant="danger" onClick={() => setConfirmResetAll(true)} disabled={busy}>
              {t('economy.resetAllBalances')}
            </Button>
          </div>

          <Card className="flex flex-col gap-3">
            {top === null && <p className="text-sm text-muted">{t('common.loading')}</p>}
            {top !== null && top.length === 0 && <p className="text-sm text-muted">{t('economy.noBalances')}</p>}
            {top !== null && top.length > 0 && (
              <ul className="flex flex-col gap-2">
                {top.map((entry) => (
                  <li
                    key={entry.user_id}
                    className="flex items-center gap-3 border-t border-border pt-2 first:border-t-0 first:pt-0"
                  >
                    <span className="min-w-0 flex-1 truncate text-sm text-foreground">{entry.display_name}</span>
                    <span className="text-sm text-muted">{entry.balance}</span>
                    <input
                      type="number"
                      min={0}
                      placeholder={t('economy.newBalancePlaceholder')}
                      aria-label={t('economy.newBalanceAria', { name: entry.display_name })}
                      value={editBalances[entry.user_id] ?? ''}
                      onChange={(e) => setEditBalances((prev) => ({ ...prev, [entry.user_id]: e.target.value }))}
                      className={`${inputClass} w-32`}
                    />
                    <Button variant="secondary" onClick={() => applyBalance(entry.user_id)}>
                      {t('economy.apply')}
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}

      <Modal open={confirmResetAll} title={t('economy.resetAllTitle')} onClose={() => setConfirmResetAll(false)}>
        <p className="mb-4 text-sm text-muted">{t('economy.resetAllWarning')}</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmResetAll(false)} disabled={busy}>
            {t('common.cancel')}
          </Button>
          <Button variant="danger" disabled={busy} onClick={resetAll}>
            {t('economy.resetAllConfirm')}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
