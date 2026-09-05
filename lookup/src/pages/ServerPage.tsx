import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupServer } from '../api/client'
import { CopyButton, DetailRow, ErrorBanner, Tag } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { normalizeInviteCode } from '../lib/discord'
import { useLookupErrorMessage } from './UserPage'

export function ServerPage() {
  const { code: rawCode = '' } = useParams()
  const t = useT()
  const code = normalizeInviteCode(decodeURIComponent(rawCode)) || decodeURIComponent(rawCode)
  const [data, setData] = useState<LookupServer | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    const normalized = normalizeInviteCode(code)
    if (!normalized) {
      setError(new LookupApiError(400, 'invalid'))
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    void lookupFetch<LookupServer>(`/server/${encodeURIComponent(normalized)}`)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }

  useEffect(load, [code])
  const errMsg = useLookupErrorMessage(error)

  if (loading) return <p className="text-muted">{t('common.loading')}</p>
  if (error || !data) return <ErrorBanner message={errMsg} onRetry={load} />

  const guild = data.guild

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-[16px] border border-border bg-surface">
        <div
          className="h-36 bg-primary-deep sm:h-44"
          style={
            guild.banner_url || guild.splash_url
              ? {
                  backgroundImage: `url(${guild.banner_url || guild.splash_url})`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }
              : undefined
          }
        />
        <div className="relative px-5 pb-5 pt-12 sm:px-6">
          {guild.icon_url ? (
            <img
              src={guild.icon_url}
              alt=""
              className="absolute -top-10 left-5 h-20 w-20 rounded-[18px] border-4 border-surface object-cover"
            />
          ) : (
            <div className="absolute -top-10 left-5 flex h-20 w-20 items-center justify-center rounded-[18px] border-4 border-surface bg-primary text-2xl font-bold text-white">
              {guild.name.slice(0, 1)}
            </div>
          )}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted">{t('server.inviteOnly')}</p>
              <h1 className="text-2xl font-bold">{guild.name}</h1>
              {guild.description ? <p className="mt-2 max-w-2xl text-sm text-muted">{guild.description}</p> : null}
            </div>
            <CopyButton value={data.code} />
          </div>
        </div>
      </div>

      <p className="text-sm text-muted">{t('server.disclaimer')}</p>

      <section className="rounded-[14px] border border-border bg-surface/80 p-5">
        <h2 className="mb-2 text-lg font-semibold">{t('server.details')}</h2>
        <dl>
          <DetailRow label={t('server.code')}>{data.code}</DetailRow>
          <DetailRow label={t('server.guild')}>
            {guild.name} <span className="text-muted">({guild.id})</span>
          </DetailRow>
          <DetailRow label={t('server.channel')}>
            {data.channel ? `#${data.channel.name}` : '—'}
          </DetailRow>
          <DetailRow label={t('server.inviter')}>
            {data.inviter ? (
              <Link to={`/user/${data.inviter.id}`} className="text-primary-hover hover:underline">
                {data.inviter.global_name || data.inviter.username}
              </Link>
            ) : (
              '—'
            )}
          </DetailRow>
          <DetailRow label={t('server.members')}>{data.approximate_member_count ?? '—'}</DetailRow>
          <DetailRow label={t('server.online')}>{data.approximate_presence_count ?? '—'}</DetailRow>
          <DetailRow label={t('server.expires')}>
            {data.expires_at ? new Date(data.expires_at).toUTCString() : t('server.never')}
          </DetailRow>
        </dl>
      </section>

      {guild.features.length ? (
        <section className="rounded-[14px] border border-border bg-surface/80 p-5">
          <h2 className="mb-3 text-lg font-semibold">{t('server.features')}</h2>
          <div className="flex flex-wrap gap-2">
            {guild.features.map((f) => (
              <Tag key={f}>{f}</Tag>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
