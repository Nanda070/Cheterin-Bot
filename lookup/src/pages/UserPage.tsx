import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupUser } from '../api/client'
import { useLookupContext } from '../App'
import {
  CopyButton,
  DetailGrid,
  DetailRow,
  ErrorBanner,
  GhostLink,
  LoadingBlock,
  Panel,
  ProfileBanner,
  SectionTitle,
  Tag,
} from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'
import { cdnAvatarUrl, cdnBannerUrl, isSnowflake } from '../lib/discord'
import { badgesFromFlags } from '../lib/badges'
import { useLookupErrorMessage } from '../lib/useLookup'

export function UserPage() {
  const { id = '' } = useParams()
  const t = useT()
  const { lang } = useLanguage()
  const { showCaptcha } = useLookupContext()
  const [user, setUser] = useState<LookupUser | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const loadRef = useRef<(() => void) | undefined>(undefined)

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
      .catch((err: unknown) => {
        setError(err)
        if (err instanceof LookupApiError && err.code === 'captcha_required') {
          showCaptcha(() => loadRef.current?.())
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadRef.current = load
  })

  useEffect(() => {
    load()
  }, [id])

  const errMsg = useLookupErrorMessage(error)

  if (loading) return <LoadingBlock rows={5} />
  if (error || !user) return <ErrorBanner message={errMsg} onRetry={load} />

  const badges = badgesFromFlags(user.public_flags)
  const accent =
    user.accent_color != null ? `#${user.accent_color.toString(16).padStart(6, '0')}` : null

  return (
    <div className="space-y-6 lookup-rise">
      <Panel className="overflow-hidden">
        <ProfileBanner imageUrl={user.banner_url} accent={accent} />
        <div className="relative px-5 pb-6 pt-14 sm:px-6">
          <img
            src={user.avatar_url}
            alt=""
            className="absolute -top-11 left-5 h-[5.5rem] w-[5.5rem] rounded-full border-4 border-surface bg-background object-cover sm:left-6"
          />
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
                {user.global_name || user.username}
              </h1>
              <p className="mt-1 text-muted">
                @{user.username}
                {user.discriminator && user.discriminator !== '0' ? `#${user.discriminator}` : ''}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {user.bot ? <Tag tone="accent">BOT</Tag> : null}
                {user.system ? <Tag>SYSTEM</Tag> : null}
                {badges.map((b) => (
                  <span
                    key={b.key}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-hover/80 px-2.5 py-1 text-xs text-foreground"
                    title={lang === 'ru' ? b.nameRu : b.nameEn}
                  >
                    <img src={b.icon} alt="" width={16} height={16} className="h-4 w-4 object-contain" />
                    {lang === 'ru' ? b.nameRu : b.nameEn}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton value={user.id} />
              {user.bot ? <GhostLink to={`/bot/${user.id}`}>{t('user.openBot')}</GhostLink> : null}
              <GhostLink to={`/plugins/snowflake/${user.id}`}>{t('user.openSnowflake')}</GhostLink>
            </div>
          </div>
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('user.details')}</SectionTitle>
          <dl>
            <DetailGrid>
              <DetailRow label={t('user.id')}>
                <span className="font-mono text-[0.85rem]">{user.id}</span>
              </DetailRow>
              <DetailRow label={t('user.username')}>{user.username}</DetailRow>
              <DetailRow label={t('user.globalName')}>{user.global_name || '—'}</DetailRow>
              <DetailRow label={t('common.createdAt')}>{new Date(user.created_at).toUTCString()}</DetailRow>
              <DetailRow label={t('user.bot')}>{user.bot ? t('common.yes') : t('common.no')}</DetailRow>
              <DetailRow label={t('user.accent')}>
                {accent ? (
                  <span className="inline-flex items-center gap-2">
                    <span className="inline-block h-3.5 w-3.5 rounded-full border border-border" style={{ background: accent }} />
                    {accent}
                  </span>
                ) : (
                  '—'
                )}
              </DetailRow>
              <DetailRow label={t('user.flags')}>{user.public_flags}</DetailRow>
            </DetailGrid>
          </dl>
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('user.assets')}</SectionTitle>
          <div className="space-y-3">
            <AssetRow
              label={t('user.avatar')}
              url={user.avatar ? cdnAvatarUrl(user.id, user.avatar, 512) : user.avatar_url}
              proxyKind="avatar"
              id={user.id}
              hash={user.avatar}
              rounded
            />
            {user.banner ? (
              <AssetRow
                label={t('user.banner')}
                url={cdnBannerUrl(user.id, user.banner, 1024)}
                proxyKind="banner"
                id={user.id}
                hash={user.banner}
              />
            ) : (
              <p className="rounded-[12px] border border-dashed border-border bg-background-deep px-3 py-4 text-sm text-muted">
                {t('user.noBanner')}
              </p>
            )}
          </div>
        </Panel>
      </div>
    </div>
  )
}

function AssetRow({
  label,
  url,
  proxyKind,
  id,
  hash,
  rounded = false,
}: {
  label: string
  url: string
  proxyKind: 'avatar' | 'banner'
  id: string
  hash: string | null
  rounded?: boolean
}) {
  const t = useT()
  const proxy =
    hash != null ? `/api/lookup/cdn/${proxyKind}/${id}/${hash}?size=512` : null

  return (
    <div className="rounded-[12px] border border-border bg-background-deep p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{label}</p>
        <div className="flex flex-wrap gap-2 text-xs">
          <a href={url} target="_blank" rel="noreferrer" className="font-medium text-primary-hover hover:underline">
            {t('common.download')}
          </a>
          {proxy ? (
            <a href={proxy} className="text-muted hover:text-foreground hover:underline">
              {t('common.proxyDownload')}
            </a>
          ) : null}
        </div>
      </div>
      <img
        src={url}
        alt=""
        className={`max-h-36 w-full object-cover ${rounded ? 'rounded-full max-w-[8rem]' : 'rounded-lg'}`}
      />
    </div>
  )
}
