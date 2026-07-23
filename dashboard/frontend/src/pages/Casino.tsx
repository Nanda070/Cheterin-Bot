import { DiceThree, Gear, Plus, Trash, Trophy } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  fetchCasinoLeaderboard,
  fetchCasinoSettings,
  fetchEconomySettings,
  updateCasinoSettings,
  updateEconomySettings,
  type CasinoLeaderboardEntry,
  type CasinoSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type Tab = 'settings' | 'leaderboard'

export function CasinoPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<CasinoSettings | null>(null)
  const [rouletteEnabled, setRouletteEnabled] = useState(true)
  const [rouletteMaxBet, setRouletteMaxBet] = useState(1000)
  const [rouletteReady, setRouletteReady] = useState(false)
  const [rouletteError, setRouletteError] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const [lbMode, setLbMode] = useState<'slots' | 'bj' | 'total'>('total')
  const [lbType, setLbType] = useState<'wins' | 'losses'>('losses')
  const [lbPage, setLbPage] = useState(1)
  const [lbEntries, setLbEntries] = useState<CasinoLeaderboardEntry[]>([])
  const [lbTotal, setLbTotal] = useState(0)

  const tabs = useMemo(
    () =>
      [
        { key: 'settings' as const, label: t('casino.tab.settings'), icon: Gear },
        { key: 'leaderboard' as const, label: t('casino.tab.leaderboard'), icon: Trophy },
      ] as const,
    [t],
  )

  useEffect(() => {
    fetchCasinoSettings()
      .then((casino) => {
        if (!casino.loss_roles) casino.loss_roles = []
        setSettings(casino)
      })
      .catch(() => setError(t('casino.errorLoad')))
  }, [t])

  useEffect(() => {
    setRouletteReady(false)
    setRouletteError('')
    fetchEconomySettings()
      .then((eco) => {
        setRouletteEnabled(eco.roulette_bets_enabled)
        setRouletteMaxBet(eco.roulette_max_bet)
        setRouletteReady(true)
      })
      .catch(() => setRouletteError(t('casino.rouletteLoadError')))
  }, [t])

  useEffect(() => {
    if (tab !== 'leaderboard') return
    fetchCasinoLeaderboard(lbMode, lbType, lbPage)
      .then((res) => {
        setLbEntries(res.entries)
        setLbTotal(res.total)
      })
      .catch(() => {
        setLbEntries([])
        setLbTotal(0)
      })
  }, [tab, lbMode, lbType, lbPage])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updatedCasino = await updateCasinoSettings(settings)
      if (!updatedCasino.loss_roles) updatedCasino.loss_roles = []
      setSettings(updatedCasino)

      if (rouletteReady) {
        const fresh = await fetchEconomySettings()
        const updatedEconomy = await updateEconomySettings({
          ...fresh,
          roulette_bets_enabled: rouletteEnabled,
          roulette_max_bet: rouletteMaxBet,
        })
        setRouletteEnabled(updatedEconomy.roulette_bets_enabled)
        setRouletteMaxBet(updatedEconomy.roulette_max_bet)
      }

      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'casino.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const updateRole = (index: number, patch: Partial<CasinoSettings['loss_roles'][number]>) => {
    const roles = settings.loss_roles.map((r, i) => (i === index ? { ...r, ...patch } : r))
    setSettings({ ...settings, loss_roles: roles })
  }

  const formatStats = (entry: CasinoLeaderboardEntry): string => {
    if (lbMode === 'total') {
      if (lbType === 'wins') {
        return t('casino.leaderboard.totalWins', {
          total: entry.slots_wins + entry.bj_wins,
          slots: entry.slots_wins,
          bj: entry.bj_wins,
        })
      }
      return t('casino.leaderboard.totalLosses', {
        total: entry.slots_losses + entry.bj_losses,
        slots: entry.slots_losses,
        bj: entry.bj_losses,
      })
    }
    if (lbMode === 'slots') {
      const count = lbType === 'wins' ? entry.slots_wins : entry.slots_losses
      return lbType === 'wins'
        ? t('casino.leaderboard.slotsWins', { count })
        : t('casino.leaderboard.slotsLosses', { count })
    }
    const count = lbType === 'wins' ? entry.bj_wins : entry.bj_losses
    return lbType === 'wins'
      ? t('casino.leaderboard.bjWins', { count })
      : t('casino.leaderboard.bjLosses', { count })
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <DiceThree size={22} className="text-primary" />
          {t('casino.title')}
        </h1>
        {tab === 'settings' && (
          <Toggle
            checked={settings.enabled}
            onChange={(v) => setSettings({ ...settings, enabled: v })}
            label={settings.enabled ? t('casino.enabled') : t('casino.disabled')}
          />
        )}
      </div>
      <p className="text-sm text-muted">{t('casino.intro')}</p>

      <div className="flex flex-wrap gap-1 rounded-card border border-border bg-surface p-1.5">
        {tabs.map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setTab(key)
              setError('')
              setSaved('')
            }}
            className={`flex cursor-pointer items-center gap-1.5 rounded-control px-3 py-1.5 text-sm transition-colors ${
              tab === key
                ? 'bg-primary-muted text-foreground'
                : 'text-muted hover:bg-surface-hover hover:text-foreground'
            }`}
          >
            <TabIcon size={15} />
            {label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {tab === 'settings' && (
        <>
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('casino.gameSettings')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="casino-edge">
                  {t('casino.houseEdge')}
                </label>
                <input
                  id="casino-edge"
                  type="number"
                  min={0}
                  max={50}
                  value={settings.house_edge_percent}
                  onChange={(e) => setSettings({ ...settings, house_edge_percent: Number(e.target.value) })}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="casino-cooldown">
                  {t('casino.cooldown')}
                </label>
                <input
                  id="casino-cooldown"
                  type="number"
                  min={0}
                  max={300}
                  value={settings.cooldown_sec}
                  onChange={(e) => setSettings({ ...settings, cooldown_sec: Number(e.target.value) })}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="casino-min-bet">
                  {t('casino.minBet')}
                </label>
                <input
                  id="casino-min-bet"
                  type="number"
                  min={1}
                  value={settings.min_bet}
                  onChange={(e) => setSettings({ ...settings, min_bet: Number(e.target.value) })}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="casino-max-bet">
                  {t('casino.maxBet')}
                </label>
                <input
                  id="casino-max-bet"
                  type="number"
                  min={0}
                  value={settings.max_bet}
                  onChange={(e) => setSettings({ ...settings, max_bet: Number(e.target.value) })}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('casino.rouletteBets')}</h2>
              {rouletteReady && (
                <Toggle
                  checked={rouletteEnabled}
                  onChange={setRouletteEnabled}
                  label={rouletteEnabled ? t('economy.allowed') : t('economy.forbidden')}
                />
              )}
            </div>
            <p className="text-sm text-muted">{t('casino.rouletteHint')}</p>
            {rouletteError && <p className="text-sm text-danger">{rouletteError}</p>}
            {!rouletteReady && !rouletteError && <p className="text-sm text-muted">{t('common.loading')}</p>}
            {rouletteReady && (
              <div className="flex flex-col gap-1 sm:max-w-xs">
                <label className="text-sm text-muted" htmlFor="casino-roulette-max-bet">
                  {t('casino.rouletteMaxBet')}
                </label>
                <input
                  id="casino-roulette-max-bet"
                  type="number"
                  min={0}
                  max={1000000}
                  value={rouletteMaxBet}
                  onChange={(e) => setRouletteMaxBet(Number(e.target.value))}
                  className={inputClass}
                />
              </div>
            )}
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('casino.lossRoles')}</h2>
            <p className="text-sm text-muted">{t('casino.lossRolesHint')}</p>
            {settings.loss_roles.map((item, index) => (
              <div
                key={index}
                className="flex flex-col gap-2 rounded-control border border-border p-3 sm:flex-row sm:items-center"
              >
                <select
                  value={item.game}
                  onChange={(e) =>
                    updateRole(index, { game: e.target.value as CasinoSettings['loss_roles'][number]['game'] })
                  }
                  className={inputClass}
                >
                  <option value="slots">{t('casino.game.slots')}</option>
                  <option value="bj">{t('casino.game.bj')}</option>
                  <option value="total">{t('casino.game.total')}</option>
                </select>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted">{t('casino.threshold')}</span>
                  <input
                    type="number"
                    min={1}
                    value={item.threshold || ''}
                    onChange={(e) => updateRole(index, { threshold: Number(e.target.value) })}
                    className={`${inputClass} w-24`}
                  />
                </div>
                <input
                  type="text"
                  placeholder={t('casino.roleIdPlaceholder')}
                  value={item.role_id}
                  onChange={(e) => updateRole(index, { role_id: e.target.value.replace(/\D/g, '') })}
                  className={`${inputClass} flex-1`}
                />
                <Button
                  variant="ghost"
                  onClick={() =>
                    setSettings({ ...settings, loss_roles: settings.loss_roles.filter((_, i) => i !== index) })
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
                  setSettings({
                    ...settings,
                    loss_roles: [...settings.loss_roles, { game: 'total', threshold: 10, role_id: '' }],
                  })
                }
              >
                <Plus size={16} /> {t('casino.addRole')}
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

      {tab === 'leaderboard' && (
        <Card className="flex flex-col gap-3">
          <h2 className="font-semibold text-foreground">{t('casino.leaderboard', { total: lbTotal })}</h2>
          <div className="flex flex-wrap gap-2">
            <Button variant={lbType === 'losses' ? 'primary' : 'secondary'} onClick={() => setLbType('losses')}>
              {t('casino.losses')}
            </Button>
            <Button variant={lbType === 'wins' ? 'primary' : 'secondary'} onClick={() => setLbType('wins')}>
              {t('casino.wins')}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant={lbMode === 'total' ? 'primary' : 'secondary'} onClick={() => setLbMode('total')}>
              {t('casino.mode.total')}
            </Button>
            <Button variant={lbMode === 'slots' ? 'primary' : 'secondary'} onClick={() => setLbMode('slots')}>
              {t('casino.mode.slots')}
            </Button>
            <Button variant={lbMode === 'bj' ? 'primary' : 'secondary'} onClick={() => setLbMode('bj')}>
              {t('casino.mode.bj')}
            </Button>
          </div>

          {lbEntries.length === 0 ? (
            <p className="text-sm text-muted">{t('casino.leaderboardEmpty')}</p>
          ) : (
            <div className="mt-2 flex flex-col gap-2">
              {lbEntries.map((entry, i) => {
                const rank = (lbPage - 1) * 50 + i + 1
                return (
                  <div key={entry.user_id} className="flex items-center gap-3 rounded border border-border p-2">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center font-bold text-muted">#{rank}</div>
                    {entry.avatar ? (
                      <img src={entry.avatar} alt="" className="h-8 w-8 shrink-0 rounded-full" />
                    ) : (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-hover">
                        <span className="text-xs font-bold text-muted">
                          {entry.username.slice(0, 2).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div className="flex flex-1 flex-col truncate">
                      <span className="truncate text-sm font-medium text-foreground">{entry.username}</span>
                      <span className="text-xs text-muted">{formatStats(entry)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          <div className="mt-2 flex items-center gap-2">
            <Button variant="secondary" disabled={lbPage === 1} onClick={() => setLbPage(Math.max(1, lbPage - 1))}>
              {t('casino.prevPage')}
            </Button>
            <span className="text-sm text-muted">{t('casino.page', { page: lbPage })}</span>
            <Button variant="secondary" disabled={lbEntries.length < 50} onClick={() => setLbPage(lbPage + 1)}>
              {t('casino.nextPage')}
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
