import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupBot } from '../api/client'
import { useLookupContext } from '../App'
import {
  CopyButton,
  DetailRow,
  ErrorBanner,
  GhostLink,
  LoadingBlock,
  Panel,
  ProfileBanner,
  SectionTitle,
  Tag,
} from '../components/ui'
import { useT } from '../context/LanguageContext'
import { isSnowflake } from '../lib/discord'
import { useLookupErrorMessage } from '../lib/useLookup'

export function BotPage() {
  const { id = '' } = useParams()
  const t = useT()
  const { showCaptcha } = useLookupContext()
  const [data, setData] = useState<LookupBot | null>(null)
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
    void lookupFetch<LookupBot>(`/bot/${id}`)
      .then(setData)
      .catch((err: unknown) => {
        setError(err)
        if (err instanceof LookupApiError && err.code === 'captcha_required') {
          showCaptcha(() => loadRef.current?.())
        }
      })
      .finally(() => setLoading(false))
  }
  loadRef.current = load

  useEffect(load, [id])
  const errMsg = useLookupErrorMessage(error)

  if (loading) return <LoadingBlock rows={6} />
  if (error || !data) return <ErrorBanner message={errMsg} onRetry={load} />

  const user = data.user
  const app = data.application

  return (
    <div className="space-y-6 lookup-rise">
      <Panel className="overflow-hidden">
        <ProfileBanner imageUrl={user.banner_url} />
        <div className="relative px-5 pb-6 pt-14 sm:px-6">
          <img
            src={user.avatar_url}
            alt=""
            className="absolute -top-11 left-5 h-[5.5rem] w-[5.5rem] rounded-full border-4 border-surface object-cover sm:left-6"
          />
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
                {app?.name || user.global_name || user.username}
              </h1>
              <p className="mt-1 text-muted">@{user.username}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Tag tone="accent">BOT</Tag>
                {(user.public_flags & (1 << 16)) !== 0 ? <Tag>{t('bot.verified')}</Tag> : null}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton value={user.id} />
              <GhostLink to={`/user/${user.id}`}>{t('user.title')}</GhostLink>
              {data.permissions ? (
                <GhostLink to={`/permissions?permissions=${data.permissions}&client_id=${app?.id || user.id}`}>
                  {t('bot.openPermissions')}
                </GhostLink>
              ) : null}
            </div>
          </div>
        </div>
      </Panel>

      {data.degraded ? <ErrorBanner message={t('bot.degraded')} /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('bot.about')}</SectionTitle>
          <p className="text-sm leading-relaxed text-muted">
            {app?.description?.trim() || t('bot.noDescription')}
          </p>
          {data.application?.tags?.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {data.application.tags.map((tag) => (
                <Tag key={tag}>{tag}</Tag>
              ))}
            </div>
          ) : null}
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('bot.details')}</SectionTitle>
          <dl>
            <DetailRow label={t('user.id')}>
              <span className="font-mono text-[0.85rem]">{user.id}</span>
            </DetailRow>
            <DetailRow label={t('common.createdAt')}>{new Date(user.created_at).toUTCString()}</DetailRow>
            {app?.approximate_guild_count != null ? (
              <DetailRow label={t('bot.guildsApprox')}>{app.approximate_guild_count}</DetailRow>
            ) : null}
          </dl>
        </Panel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('bot.scopes')}</SectionTitle>
          {data.scopes.length ? (
            <div className="flex flex-wrap gap-2">
              {data.scopes.map((s) => (
                <Tag key={s}>{s}</Tag>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">{t('common.empty')}</p>
          )}
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('bot.permissions')}</SectionTitle>
          {data.permissions_names.length ? (
            <ul className="space-y-1.5 text-sm text-muted">
              {data.permissions_names.map((name) => (
                <li key={name} className="flex gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" aria-hidden />
                  {name}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">{t('common.empty')}</p>
          )}
          {data.permissions ? (
            <p className="mt-4 font-mono text-xs text-foreground/90">{data.permissions}</p>
          ) : null}
        </Panel>
      </div>

      <Panel className="p-5 sm:p-6">
        <SectionTitle>{t('bot.intents')}</SectionTitle>
        {data.intents.length ? (
          <div className="flex flex-wrap gap-2">
            {data.intents.map((i) => (
              <Tag key={i}>{i}</Tag>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">{t('common.empty')}</p>
        )}
      </Panel>
    </div>
  )
}
