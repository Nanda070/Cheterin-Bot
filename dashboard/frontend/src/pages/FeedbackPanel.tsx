import { useEffect, useState } from 'react'
import {
  fetchFeedbackPanelSettings,
  updateFeedbackPanelSettings,
  type FeedbackPanelSettings,
} from '../api/client'
import { EMPTY_EMBED_SPEC, EmbedEditor } from '../components/EmbedEditor'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

export function FeedbackPanelPage() {
  const t = useT()
  const [settings, setSettings] = useState<FeedbackPanelSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchFeedbackPanelSettings()
      .then((data) =>
        setSettings({
          content: data.content,
          embed: { ...EMPTY_EMBED_SPEC, ...data.embed },
          banner_url: data.banner_url || '',
        }),
      )
      .catch(() => setError(t('common.errorLoad')))
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateFeedbackPanelSettings(settings)
      setSettings({
        content: updated.content,
        embed: { ...EMPTY_EMBED_SPEC, ...updated.embed },
        banner_url: updated.banner_url || '',
      })
      setSaved(t('common.saved'))
    } catch {
      setError(t('common.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-5xl flex-col gap-4">
      <Card className="flex flex-col gap-2">
        <h2 className="font-semibold text-foreground">{t('messageCustomizer.feedbackPanelTitle')}</h2>
        <p className="text-sm text-muted">{t('messageCustomizer.feedbackPanelIntro')}</p>
        <label className="text-sm text-muted" htmlFor="feedback-banner-url">
          {t('messageCustomizer.feedbackBannerUrl')}
        </label>
        <input
          id="feedback-banner-url"
          value={settings.banner_url}
          onChange={(e) => setSettings({ ...settings, banner_url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          placeholder={t('messageCustomizer.feedbackBannerPlaceholder')}
        />
      </Card>
      <EmbedEditor
        content={settings.content}
        onContentChange={(content) => setSettings({ ...settings, content })}
        embed={settings.embed}
        onEmbedChange={(embed) => setSettings({ ...settings, embed })}
        showFields={false}
      />
      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}
      <Button variant="primary" onClick={save} disabled={busy}>
        {busy ? t('common.saving') : t('common.save')}
      </Button>
    </div>
  )
}
