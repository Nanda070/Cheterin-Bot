import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupBot } from '../api/client'
import { CopyButton, DetailRow, ErrorBanner, Tag } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { isSnowflake } from '../lib/discord'
import { useLookupErrorMessage } from './UserPage'

export function BotPage() {
  const { id = '' } = useParams()
  const t = useT()
  const [data, setData] = useState<LookupBot | null>(null)
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
    void lookupFetch<LookupBot>(`/bot/${id}`)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }

  useEffect(load, [id])
  const errMsg = useLookupErrorMessage(error)

  if (loading) return <p className="text-muted">{t('common.loading')}</p>
  if (error || !data) return <ErrorBanner message={errMsg} onRetry={load} />

  const user = data.user
  const app = data.application

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-[16px] border border-border bg-surface">
        <div
          className="h-36 bg-primary-deep sm:h-44"
          style={
            user.banner_url
              ? { backgroundImage: `url(${user.banner_url})`, backgroundSize: 'cover', backgroundPosition: 'center' }
              : undefined
          }
        />
        <div className="relative px-5 pb-5 pt-12 sm:px-6">
          <img
            src={user.avatar_url}
            alt=""
            className="absolute -top-10 left-5 h-20 w-20 rounded-full border-4 border-surface object-cover"
          />
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">{app?.name || user.global_name || user.username}</h1>
              <p className="text-muted">@{user.username}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Tag>BOT</Tag>
                {(user.public_flags & (1 << 16)) !== 0 ? <Tag>{t('bot.verified')}</Tag> : null}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton value={user.id} />
              <Link to={`/user/${user.id}`} className="rounded-[8px] border border-border px-2 py-1 text-xs hover:bg-surface-hover">
                {t('user.title')}
              </Link>
              {data.permissions ? (
                <Link
                  to={`/permissions?permissions=${data.permissions}&client_id=${app?.id || user.id}`}
                  className="rounded-[8px] border border-border px-2 py-1 text-xs hover:bg-surface-hover"
                >
                  {t('bot.openPermissions')}
                </Link>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {data.degraded ? (
        <ErrorBanner message={t('bot.degraded')} />
      ) : null}

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-2 text-lg font-semibold">{t('bot.about')}</h2>
        <p className="text-sm leading-relaxed text-muted">
          {app?.description?.trim() || t('bot.noDescription')}
        </p>
        {data.application?.tags?.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {data.application.tags.map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </div>
        ) : null}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-[14px] border border-border bg-surface/80 p-5">
          <h2 className="mb-2 text-lg font-semibold">{t('bot.scopes')}</h2>
          {data.scopes.length ? (
            <div className="flex flex-wrap gap-2">
              {data.scopes.map((s) => (
                <Tag key={s}>{s}</Tag>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">{t('common.empty')}</p>
          )}
        </section>

        <section className="rounded-[14px] border border-border bg-surface/80 p-5">
          <h2 className="mb-2 text-lg font-semibold">{t('bot.permissions')}</h2>
          {data.permissions_names.length ? (
            <ul className="space-y-1 text-sm text-muted">
              {data.permissions_names.map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">{t('common.empty')}</p>
          )}
          {data.permissions ? (
            <p className="mt-3 font-mono text-xs text-foreground">{data.permissions}</p>
          ) : null}
        </section>
      </div>

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-2 text-lg font-semibold">{t('bot.intents')}</h2>
        {data.intents.length ? (
          <div className="flex flex-wrap gap-2">
            {data.intents.map((i) => (
              <Tag key={i}>{i}</Tag>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">{t('common.empty')}</p>
        )}
      </section>

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-2 text-lg font-semibold">{t('bot.details')}</h2>
        <dl>
          <DetailRow label={t('user.id')}>{user.id}</DetailRow>
          <DetailRow label={t('common.createdAt')}>{new Date(user.created_at).toUTCString()}</DetailRow>
          {app?.approximate_guild_count != null ? (
            <DetailRow label="Guilds (approx.)">{app.approximate_guild_count}</DetailRow>
          ) : null}
        </dl>
      </section>
    </div>
  )
}
