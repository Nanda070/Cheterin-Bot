import {
  ChatsCircle,
  Confetti,
  GameController,
  Quotes,
  Smiley,
  type Icon,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  fetchFunSettings,
  fetchQuoteSettings,
  fetchWordleSettings,
  updateFunSettings,
  updateQuoteSettings,
  updateWordleSettings,
  type FunSettings,
  type QuoteSettings,
  type WordleSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { AutoReactionsPage } from './AutoReactions'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type FunTab = 'general' | 'autoEmoji' | 'wordle' | 'quote'

function parseFunTab(raw: string | null): FunTab {
  if (raw === 'autoEmoji' || raw === 'auto-reactions' || raw === 'autoReactions') return 'autoEmoji'
  if (raw === 'wordle' || raw === 'quote') return raw
  return 'general'
}

function TabBar({
  tab,
  setTab,
  t,
}: {
  tab: FunTab
  setTab: (t: FunTab) => void
  t: (key: string) => string
}) {
  const tabs: { key: FunTab; labelKey: string; icon: Icon }[] = [
    { key: 'general', labelKey: 'fun.tab.general', icon: GameController },
    { key: 'autoEmoji', labelKey: 'fun.tab.autoEmoji', icon: Smiley },
    { key: 'wordle', labelKey: 'fun.tab.wordle', icon: ChatsCircle },
    { key: 'quote', labelKey: 'fun.tab.quote', icon: Quotes },
  ]
  return (
    <div className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

function GeneralTab({
  settings,
  setSettings,
  error,
  saved,
  busy,
  onSave,
  t,
}: {
  settings: FunSettings
  setSettings: (s: FunSettings) => void
  error: string
  saved: string
  busy: boolean
  onSave: () => void
  t: (key: string) => string
}) {
  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-foreground">{t('fun.roulette.title')}</h2>
          <p className="mt-1 text-sm text-muted">{t('fun.intro')}</p>
        </div>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('common.moduleEnabled') : t('common.moduleDisabled')}
        />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <h3 className="font-semibold text-foreground">{t('fun.roulette.title')}</h3>
        <p className="text-sm text-muted">{t('fun.roulette.desc')}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-roulette-timeout">
              {t('fun.roulette.timeout')}
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
              {t('fun.roulette.cooldown')}
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
        <p className="text-xs text-muted">{t('fun.roulette.hint')}</p>
      </Card>

      <div>
        <Button variant="primary" onClick={onSave} disabled={busy}>
          {busy ? t('common.saving') : t('fun.saveFun')}
        </Button>
      </div>
    </div>
  )
}

function AutoEmojiTab({
  settings,
  setSettings,
  error,
  saved,
  busy,
  onSave,
  t,
}: {
  settings: FunSettings
  setSettings: (s: FunSettings) => void
  error: string
  saved: string
  busy: boolean
  onSave: () => void
  t: (key: string) => string
}) {
  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">{t('fun.autoEmoji.title')}</h2>
          <Toggle
            checked={settings.auto_emoji_enabled}
            onChange={(v) => setSettings({ ...settings, auto_emoji_enabled: v })}
            label={settings.auto_emoji_enabled ? t('fun.autoEmoji.on') : t('fun.autoEmoji.off')}
          />
        </div>
        <p className="text-sm text-muted">{t('fun.autoEmoji.desc')}</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-chance">
              {t('fun.autoEmoji.chance')}
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
              {t('fun.autoEmoji.interval')}
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
              {t('fun.autoEmoji.remove')}
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
        <div>
          <Button variant="primary" onClick={onSave} disabled={busy}>
            {busy ? t('common.saving') : t('fun.saveFun')}
          </Button>
        </div>
      </Card>

      <div className="border-t border-border pt-4">
        <AutoReactionsPage embedded />
      </div>
    </div>
  )
}

export function FunPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseFunTab(searchParams.get('tab'))
  const setTab = (next: FunTab) => {
    if (next === 'general') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  const [settings, setSettings] = useState<FunSettings | null>(null)
  const [wordle, setWordle] = useState<WordleSettings | null>(null)
  const [quote, setQuote] = useState<QuoteSettings | null>(null)
  const [wordleError, setWordleError] = useState('')
  const [quoteError, setQuoteError] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [wordleSaved, setWordleSaved] = useState('')
  const [quoteSaved, setQuoteSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [wordleBusy, setWordleBusy] = useState(false)
  const [quoteBusy, setQuoteBusy] = useState(false)

  useEffect(() => {
    fetchFunSettings()
      .then(setSettings)
      .catch((err) => setError(formatApiError(err, t, 'fun.errorLoad')))
    fetchWordleSettings()
      .then(setWordle)
      .catch((err) => setWordleError(formatApiError(err, t, 'fun.errorLoadWordle')))
    fetchQuoteSettings()
      .then(setQuote)
      .catch((err) => setQuoteError(formatApiError(err, t, 'fun.errorLoadQuote')))
  }, [t])

  const saveFun = async () => {
    if (!settings) return
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateFunSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'fun.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const saveWordle = async () => {
    if (!wordle) return
    setWordleBusy(true)
    setWordleError('')
    setWordleSaved('')
    try {
      const updatedWordle = await updateWordleSettings(wordle)
      setWordle(updatedWordle)
      setWordleSaved(t('common.saved'))
    } catch (err) {
      setWordleError(formatApiError(err, t, 'fun.errorSaveWordle'))
    } finally {
      setWordleBusy(false)
    }
  }

  const saveQuote = async () => {
    if (!quote) return
    setQuoteBusy(true)
    setQuoteError('')
    setQuoteSaved('')
    try {
      const updated = await updateQuoteSettings(quote)
      setQuote(updated)
      setQuoteSaved(t('common.saved'))
    } catch (err) {
      setQuoteError(formatApiError(err, t, 'fun.errorSaveQuote'))
    } finally {
      setQuoteBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Confetti size={22} className="text-primary" />
          {t('fun.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('fun.intro')}</p>
      </div>

      <TabBar tab={tab} setTab={setTab} t={t} />

      {!settings && tab !== 'wordle' && tab !== 'quote' && (
        <p className="text-sm text-muted">{error || t('common.loading')}</p>
      )}

      {tab === 'general' && settings && (
        <GeneralTab
          settings={settings}
          setSettings={setSettings}
          error={error}
          saved={saved}
          busy={busy}
          onSave={saveFun}
          t={t}
        />
      )}

      {tab === 'autoEmoji' && settings && (
        <AutoEmojiTab
          settings={settings}
          setSettings={setSettings}
          error={error}
          saved={saved}
          busy={busy}
          onSave={saveFun}
          t={t}
        />
      )}

      {tab === 'wordle' && (
        <div className="flex max-w-3xl flex-col gap-5 pb-4">
          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('fun.wordle.title')}</h2>
              {wordle && (
                <Toggle
                  checked={wordle.enabled}
                  onChange={(v) => setWordle({ ...wordle, enabled: v })}
                  label={wordle.enabled ? t('fun.wordle.enabled') : t('fun.wordle.disabled')}
                />
              )}
            </div>
            <p className="text-sm text-muted">{t('fun.wordle.desc')}</p>
            {wordleError && <p className="text-sm text-danger">{wordleError}</p>}
            {wordleSaved && <p className="text-sm text-primary">{wordleSaved}</p>}
            {!wordle && !wordleError && <p className="text-sm text-muted">{t('common.loading')}</p>}
            {wordle && (
              <>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-muted" htmlFor="wordle-channel">
                      {t('fun.wordle.channel')}
                    </label>
                    <input
                      id="wordle-channel"
                      type="text"
                      inputMode="numeric"
                      placeholder={t('fun.wordle.channelPlaceholder')}
                      value={wordle.channel_id}
                      onChange={(e) => setWordle({ ...wordle, channel_id: e.target.value.replace(/\D/g, '') })}
                      className={inputClass}
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-muted" htmlFor="wordle-time">
                      {t('fun.wordle.time')}
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
                <p className="text-xs text-muted">{t('fun.wordle.hint')}</p>
                <div>
                  <Button variant="primary" onClick={saveWordle} disabled={wordleBusy}>
                    {wordleBusy ? t('common.saving') : t('fun.saveWordle')}
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>
      )}

      {tab === 'quote' && (
        <div className="flex max-w-3xl flex-col gap-5 pb-4">
          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('fun.quote.title')}</h2>
              {quote && (
                <Toggle
                  checked={quote.enabled}
                  onChange={(v) => setQuote({ ...quote, enabled: v })}
                  label={quote.enabled ? t('fun.quote.enabled') : t('fun.quote.disabled')}
                />
              )}
            </div>
            <p className="text-sm text-muted">{t('fun.quote.desc')}</p>
            {quoteError && <p className="text-sm text-danger">{quoteError}</p>}
            {quoteSaved && <p className="text-sm text-primary">{quoteSaved}</p>}
            {!quote && !quoteError && <p className="text-sm text-muted">{t('common.loading')}</p>}
            {quote && (
              <>
                <Toggle
                  checked={quote.delete_trigger}
                  onChange={(v) => setQuote({ ...quote, delete_trigger: v })}
                  label={t('fun.quote.deleteTrigger')}
                />
                <p className="text-xs text-muted">{t('fun.quote.hint')}</p>
                <div>
                  <Button variant="primary" onClick={saveQuote} disabled={quoteBusy}>
                    {quoteBusy ? t('common.saving') : t('fun.saveQuote')}
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
