import { GlobeHemisphereWest } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchLanguage, updateLanguage, type ServerLanguage } from '../api/client'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { useT } from '../context/LanguageContext'

const LANGUAGE_OPTIONS = [
  { value: 'ru', labelKey: 'settings.lang.ru' },
  { value: 'en', labelKey: 'settings.lang.en' },
] as const

export function ServerSettingsPage() {
  const t = useT()
  const [language, setLanguage] = useState<ServerLanguage['code']>('ru')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    fetchLanguage()
      .then((data) => setLanguage(data.code))
      .catch(() => setError(t('settings.errorLoad')))
      .finally(() => setLoading(false))
  }, [t])

  const handleSave = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const data = await updateLanguage(language)
      setLanguage(data.code)
      setSavedMessage(t('settings.saved'))
    } catch {
      setError(t('settings.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <GlobeHemisphereWest size={22} className="text-primary" />
          {t('settings.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('settings.intro')}</p>
      </div>

      {error && (
        <div className="rounded-control border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
      )}
      {savedMessage && (
        <div className="rounded-control border border-success/40 bg-success/10 px-4 py-3 text-sm text-success">
          {savedMessage}
        </div>
      )}

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div>
          <h2 className="font-medium text-foreground">{t('settings.botLanguage')}</h2>
          <p className="mt-1 text-sm text-muted">{t('settings.botLanguageHint')}</p>
        </div>
        <Select
          value={language}
          disabled={loading || busy}
          onChange={(id) => setLanguage(id as ServerLanguage['code'])}
          options={LANGUAGE_OPTIONS.map(({ value, labelKey }) => ({ id: value, name: t(labelKey) }))}
        />
        <div>
          <Button onClick={handleSave} disabled={loading || busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </section>
    </div>
  )
}
