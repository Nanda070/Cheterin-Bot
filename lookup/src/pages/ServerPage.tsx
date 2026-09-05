import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupServer } from '../api/client'
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
import { useT } from '../context/LanguageContext'
import { normalizeInviteCode } from '../lib/discord'
import { useLookupErrorMessage } from '../lib/useLookup'

export function ServerPage() {
  const { code: rawCode = '' } = useParams()
  const t = useT()
  const { showCaptcha } = useLookupContext()
  const code = normalizeInviteCode(decodeURIComponent(rawCode)) || decodeURIComponent(rawCode)
  const [data, setData] = useState<LookupServer | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const loadRef = useRef<(() => void) | undefined>(undefined)

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
  }, [code])

  const errMsg = useLookupErrorMessage(error)

  if (loading) return <LoadingBlock rows={5} />
  if (error || !data) return <ErrorBanner message={errMsg} onRetry={load} />

  const guild = data.guild

  return (
    <div className="space-y-6 lookup-rise">
      <Panel className="overflow-hidden">
        <ProfileBanner imageUrl={guild.banner_url || guild.splash_url} />
        <div className="relative px-5 pb-6 pt-14 sm:px-6">
          {guild.icon_url ? (
            <img
              src={guild.icon_url}
              alt=""
              className="absolute -top-11 left-5 h-[5.5rem] w-[5.5rem] rounded-[20px] border-4 border-surface object-cover sm:left-6"
            />
          ) : (
            <div className="absolute -top-11 left-5 flex h-[5.5rem] w-[5.5rem] items-center justify-center rounded-[20px] border-4 border-surface bg-primary font-display text-2xl font-bold text-white sm:left-6">
              {guild.name.slice(0, 1)}
            </div>
          )}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-primary-hover">
                {t('server.inviteOnly')}
              </p>
              <h1 className="mt-1 font-display text-2xl font-bold tracking-tight sm:text-3xl">{guild.name}</h1>
              {guild.description ? (
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">{guild.description}</p>
              ) : null}
            </div>
            <CopyButton value={data.code} />
          </div>
        </div>
      </Panel>

      <p className="text-sm text-muted">{t('server.disclaimer')}</p>

      <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('server.details')}</SectionTitle>
          <dl>
            <DetailGrid>
              <DetailRow label={t('server.code')}>{data.code}</DetailRow>
              <DetailRow label={t('server.guild')}>
                {guild.name} <span className="text-muted">({guild.id})</span>
              </DetailRow>
              <DetailRow label={t('server.channel')}>
                {data.channel ? `#${data.channel.name}` : '—'}
              </DetailRow>
              <DetailRow label={t('server.inviter')}>
                {data.inviter ? (
                  <GhostLink to={`/user/${data.inviter.id}`}>
                    {data.inviter.global_name || data.inviter.username}
                  </GhostLink>
                ) : (
                  '—'
                )}
              </DetailRow>
              <DetailRow label={t('server.members')}>{data.approximate_member_count ?? '—'}</DetailRow>
              <DetailRow label={t('server.online')}>{data.approximate_presence_count ?? '—'}</DetailRow>
              <DetailRow label={t('server.expires')}>
                {data.expires_at ? new Date(data.expires_at).toUTCString() : t('server.never')}
              </DetailRow>
            </DetailGrid>
          </dl>
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('server.features')}</SectionTitle>
          {guild.features.length ? (
            <div className="flex flex-wrap gap-2">
              {guild.features.map((f) => (
                <Tag key={f}>{f}</Tag>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">{t('common.empty')}</p>
          )}
        </Panel>
      </div>
    </div>
  )
}
