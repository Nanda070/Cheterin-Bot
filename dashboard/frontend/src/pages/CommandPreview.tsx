import { Eye } from '@phosphor-icons/react'
import { useState } from 'react'
import { previewTemplate, type TemplatePreviewResult } from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function CommandPreviewPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [content, setContent] = useState('Welcome, {mention}! You joined {guild_name}.')
  const [embedTitle, setEmbedTitle] = useState('Hello {name}')
  const [embedDesc, setEmbedDesc] = useState('Welcome to {guild_name}')
  const [useEmbed, setUseEmbed] = useState(false)
  const [result, setResult] = useState<TemplatePreviewResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async () => {
    setBusy(true)
    setError('')
    try {
      const payload: {
        content?: string
        embed?: Record<string, unknown>
      } = {}
      if (content.trim()) payload.content = content
      if (useEmbed) {
        payload.embed = { title: embedTitle, description: embedDesc, color: '#D44556' }
      }
      setResult(await previewTemplate(payload))
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        {embedded ? (
          <h2 className="flex items-center gap-2 font-semibold text-foreground">
            <Eye size={20} className="text-primary" />
            {t('preview.title')}
          </h2>
        ) : (
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Eye size={22} className="text-primary" />
            {t('preview.title')}
          </h1>
        )}
        <p className="mt-1 text-sm text-muted">{t('preview.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('preview.content')}</label>
          <textarea rows={4} value={content} onChange={(e) => setContent(e.target.value)} className={inputClass} />
        </div>
        <Toggle checked={useEmbed} onChange={setUseEmbed} label={t('preview.includeEmbed')} disabled={busy} />
        {useEmbed && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{t('preview.embedTitle')}</label>
              <input value={embedTitle} onChange={(e) => setEmbedTitle(e.target.value)} className={inputClass} />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{t('preview.embedDesc')}</label>
              <textarea rows={2} value={embedDesc} onChange={(e) => setEmbedDesc(e.target.value)} className={inputClass} />
            </div>
          </>
        )}
        <div className="flex justify-end">
          <Button variant="primary" onClick={run} disabled={busy || (!content.trim() && !useEmbed)}>
            {busy ? t('common.loading') : t('preview.run')}
          </Button>
        </div>
      </Card>

      {result && (
        <Card className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-foreground">{t('preview.result')}</h2>
          <pre className="whitespace-pre-wrap rounded-control border border-border bg-background p-3 text-sm text-foreground">
            {result.content ?? ''}
            {result.embed ? `\n\n${JSON.stringify(result.embed, null, 2)}` : ''}
          </pre>
        </Card>
      )}
    </div>
  )
}
