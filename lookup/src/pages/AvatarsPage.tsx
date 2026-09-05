import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { cdnAvatarUrl, cdnBannerUrl, isSnowflake } from '../lib/discord'

export function AvatarsPage() {
  const t = useT()
  const [params] = useSearchParams()
  const [userId, setUserId] = useState(params.get('id') || '')
  const [hash, setHash] = useState(params.get('hash') || '')
  const [kind, setKind] = useState<'avatar' | 'banner'>((params.get('kind') as 'avatar' | 'banner') || 'avatar')
  const [size, setSize] = useState(512)
  const [format, setFormat] = useState('')

  const url = useMemo(() => {
    if (!isSnowflake(userId.trim()) || !hash.trim()) return null
    if (kind === 'banner') return cdnBannerUrl(userId.trim(), hash.trim(), size, format || undefined)
    return cdnAvatarUrl(userId.trim(), hash.trim(), size, format || undefined)
  }, [userId, hash, kind, size, format])

  const proxy = url
    ? `/api/lookup/cdn/${kind}/${userId.trim()}/${hash.trim()}?size=${size}${format ? `&format=${format}` : ''}`
    : null

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold">{t('avatars.title')}</h1>
        <p className="mt-2 text-muted">{t('avatars.lead')}</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          <span className="text-muted">{t('avatars.userId')}</span>
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="mt-1 w-full rounded-[10px] border border-border bg-surface px-3 py-2 outline-none focus:border-primary"
          />
        </label>
        <label className="text-sm">
          <span className="text-muted">{t('avatars.hash')}</span>
          <input
            value={hash}
            onChange={(e) => setHash(e.target.value)}
            className="mt-1 w-full rounded-[10px] border border-border bg-surface px-3 py-2 outline-none focus:border-primary"
          />
        </label>
        <label className="text-sm">
          <span className="text-muted">{t('avatars.kind')}</span>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as 'avatar' | 'banner')}
            className="mt-1 w-full rounded-[10px] border border-border bg-surface px-3 py-2"
          >
            <option value="avatar">{t('avatars.kind.avatar')}</option>
            <option value="banner">{t('avatars.kind.banner')}</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="text-muted">{t('avatars.size')}</span>
          <select
            value={size}
            onChange={(e) => setSize(Number(e.target.value))}
            className="mt-1 w-full rounded-[10px] border border-border bg-surface px-3 py-2"
          >
            {[64, 128, 256, 512, 1024, 2048, 4096].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm sm:col-span-2">
          <span className="text-muted">{t('avatars.format')}</span>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="mt-1 w-full rounded-[10px] border border-border bg-surface px-3 py-2"
          >
            <option value="">auto</option>
            <option value="png">png</option>
            <option value="jpg">jpg</option>
            <option value="webp">webp</option>
            <option value="gif">gif</option>
          </select>
        </label>
      </div>

      {!url ? <p className="text-sm text-muted">{t('avatars.needFields')}</p> : null}

      {url ? (
        <section className="rounded-[14px] border border-border bg-surface/80 p-4">
          <h2 className="text-sm font-semibold">{t('avatars.preview')}</h2>
          <img src={url} alt="" className="mt-3 max-h-64 rounded-lg object-contain" />
          <div className="mt-3 space-y-2 text-sm">
            <p className="break-all font-mono text-xs text-muted">
              {t('avatars.cdn')}: {url}
            </p>
            <div className="flex flex-wrap gap-3">
              <a href={url} target="_blank" rel="noreferrer" className="text-primary-hover hover:underline">
                {t('common.download')}
              </a>
              {proxy ? (
                <a href={proxy} className="text-muted hover:text-foreground hover:underline">
                  {t('common.proxyDownload')}
                </a>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  )
}
