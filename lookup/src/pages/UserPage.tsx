import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupUser } from '../api/client'
import { CopyButton, DetailRow, ErrorBanner, Tag } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'
import { badgesFromFlags } from '../lib/permissions'
import { cdnAvatarUrl, cdnBannerUrl, isSnowflake } from '../lib/discord'

function useLookupErrorMessage(err: unknown): string {
  const t = useT()
  if (!(err instanceof LookupApiError)) return t('error.network')
  if (err.status === 429) {
    return t('common.rateLimited', { seconds: err.retryAfter ?? 60 })
  }
  if (err.code === 'captcha_required') return t('common.captchaRequired')
  if (err.status === 404) return t('error.404')
  if (err.status === 400) return t('error.400')
  if (err.status === 503) return t('error.503')
  if (err.status >= 500) return t('error.502')
  return err.message || t('common.error')
}

export function UserPage() {
  const { id = '' } = useParams()
  const t = useT()
  const { lang } = useLanguage()
  const [user, setUser] = useState<LookupUser | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    if (!isSnowflake(id)) {
      setError(new LookupApiError(400, 'invalid'))
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    void lookupFetch<LookupUser>(`/user/${id}`)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false))
  }

  useEffect(load, [id])

  const errMsg = useLookupErrorMessage(error)

  if (loading) return <p className="text-muted">{t('common.loading')}</p>
  if (error || !user) return <ErrorBanner message={errMsg} onRetry={load} />

  const badges = badgesFromFlags(user.public_flags)
  const accent =
    user.accent_color != null ? `#${user.accent_color.toString(16).padStart(6, '0')}` : null

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-[16px] border border-border bg-surface">
        <div
          className="h-36 bg-primary-deep sm:h-44"
          style={
            user.banner_url
              ? { backgroundImage: `url(${user.banner_url})`, backgroundSize: 'cover', backgroundPosition: 'center' }
              : accent
                ? { backgroundColor: accent }
                : undefined
          }
        />
        <div className="relative px-5 pb-5 pt-12 sm:px-6">
          <img
            src={user.avatar_url}
            alt=""
            className="absolute -top-10 left-5 h-20 w-20 rounded-full border-4 border-surface bg-background object-cover sm:left-6"
          />
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">{user.global_name || user.username}</h1>
              <p className="text-muted">
                @{user.username}
                {user.discriminator && user.discriminator !== '0' ? `#${user.discriminator}` : ''}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {user.bot ? <Tag>BOT</Tag> : null}
                {user.system ? <Tag>SYSTEM</Tag> : null}
                {badges.map((b) => (
                  <Tag key={b.key}>{lang === 'ru' ? b.nameRu : b.nameEn}</Tag>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton value={user.id} />
              {user.bot ? (
                <Link to={`/bot/${user.id}`} className="rounded-[8px] border border-border px-2 py-1 text-xs hover:bg-surface-hover">
                  {t('user.openBot')}
                </Link>
              ) : null}
              <Link to={`/snowflake/${user.id}`} className="rounded-[8px] border border-border px-2 py-1 text-xs hover:bg-surface-hover">
                {t('user.openSnowflake')}
              </Link>
            </div>
          </div>
        </div>
      </div>

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-2 text-lg font-semibold">{t('user.details')}</h2>
        <dl>
          <DetailRow label={t('user.id')}>{user.id}</DetailRow>
          <DetailRow label={t('user.username')}>{user.username}</DetailRow>
          <DetailRow label={t('user.globalName')}>{user.global_name || '—'}</DetailRow>
          <DetailRow label={t('common.createdAt')}>{new Date(user.created_at).toUTCString()}</DetailRow>
          <DetailRow label={t('user.bot')}>{user.bot ? t('common.yes') : t('common.no')}</DetailRow>
          <DetailRow label={t('user.accent')}>{accent || '—'}</DetailRow>
          <DetailRow label={t('user.flags')}>{user.public_flags}</DetailRow>
        </dl>
      </section>

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-3 text-lg font-semibold">{t('user.assets')}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <AssetCard
            label={t('user.avatar')}
            url={user.avatar ? cdnAvatarUrl(user.id, user.avatar, 512) : user.avatar_url}
            proxyKind="avatar"
            id={user.id}
            hash={user.avatar}
          />
          {user.banner ? (
            <AssetCard
              label={t('user.banner')}
              url={cdnBannerUrl(user.id, user.banner, 1024)}
              proxyKind="banner"
              id={user.id}
              hash={user.banner}
            />
          ) : (
            <p className="text-sm text-muted">{t('user.noBanner')}</p>
          )}
        </div>
      </section>
    </div>
  )
}

function AssetCard({
  label,
  url,
  proxyKind,
  id,
  hash,
}: {
  label: string
  url: string
  proxyKind: 'avatar' | 'banner'
  id: string
  hash: string | null
}) {
  const t = useT()
  const proxy =
    hash != null
      ? `/api/lookup/cdn/${proxyKind}/${id}/${hash}?size=512`
      : null

  return (
    <div className="rounded-[12px] border border-border bg-background-deep p-3">
      <p className="mb-2 text-sm text-muted">{label}</p>
      <img src={url} alt="" className="max-h-40 rounded-lg object-cover" />
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
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
  )
}

export { useLookupErrorMessage }
