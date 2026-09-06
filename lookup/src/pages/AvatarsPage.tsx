import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LookupApiError, lookupFetch, type LookupBot, type LookupUser } from '../api/client'
import { useLookupContext } from '../App'
import { ErrorBanner, LoadingBlock, PageHeader, Panel, SectionTitle, controlClass } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { cdnAvatarUrl, cdnBannerUrl, isSnowflake } from '../lib/discord'
import { useLookupErrorMessage } from '../lib/useLookup'

type Kind = 'avatar' | 'banner'

type Resolved = {
  id: string
  source: 'manual' | 'api'
  manualHash: string | null
  avatarHash: string | null
  bannerHash: string | null
}

function SearchArrowIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M5 12h12m0 0-5-5m5 5-5 5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ClearIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

async function fetchProfile(id: string): Promise<LookupUser> {
  try {
    return await lookupFetch<LookupUser>(`/user/${id}`)
  } catch (err) {
    if (!(err instanceof LookupApiError) || err.status !== 404) throw err
    const bot = await lookupFetch<LookupBot>(`/bot/${id}`)
    return bot.user
  }
}

export function AvatarsPage() {
  const t = useT()
  const { showCaptcha } = useLookupContext()
  const [params] = useSearchParams()
  const [userId, setUserId] = useState(params.get('id') || '')
  const [hash, setHash] = useState(params.get('hash') || '')
  const [kind, setKind] = useState<Kind>((params.get('kind') as Kind) || 'avatar')
  const [size, setSize] = useState(512)
  const [format, setFormat] = useState('')
  const [resolved, setResolved] = useState<Resolved | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const submitRef = useRef<(() => void) | undefined>(undefined)
  const autoRan = useRef(false)

  const activeHash = useMemo(() => {
    if (!resolved) return null
    if (resolved.source === 'manual') return resolved.manualHash
    return kind === 'banner' ? resolved.bannerHash : resolved.avatarHash
  }, [resolved, kind])

  const url = useMemo(() => {
    if (!resolved || !isSnowflake(resolved.id)) return null
    if (kind === 'banner') {
      if (!activeHash) return null
      return cdnBannerUrl(resolved.id, activeHash, size, format || undefined)
    }
    return cdnAvatarUrl(resolved.id, activeHash, size, format || undefined)
  }, [resolved, kind, activeHash, size, format])

  const proxy =
    url && activeHash
      ? `/api/lookup/cdn/${kind}/${resolved!.id}/${activeHash}?size=${size}${format ? `&format=${format}` : ''}`
      : null

  const lookupErr = useLookupErrorMessage(error)
  const errMsg =
    error instanceof Error && error.message === 'invalid'
      ? t('avatars.needId')
      : error instanceof Error && error.message === 'no_asset'
        ? t('avatars.noBanner')
        : lookupErr

  const runLookup = () => {
    const id = userId.trim()
    const manualHash = hash.trim()

    if (!isSnowflake(id)) {
      setFormError(t('avatars.needId'))
      setResolved(null)
      setError(null)
      return
    }

    setFormError(null)

    if (manualHash) {
      setLoading(false)
      setError(null)
      setResolved({
        id,
        source: 'manual',
        manualHash,
        avatarHash: null,
        bannerHash: null,
      })
      return
    }

    setLoading(true)
    setError(null)
    setResolved(null)

    void fetchProfile(id)
      .then((user) => {
        if (kind === 'banner' && !user.banner) {
          setError(new Error('no_asset'))
          setResolved(null)
          return
        }
        setResolved({
          id: user.id,
          source: 'api',
          manualHash: null,
          avatarHash: user.avatar,
          bannerHash: user.banner,
        })
      })
      .catch((err: unknown) => {
        setError(err)
        setResolved(null)
        if (err instanceof LookupApiError && err.code === 'captcha_required') {
          showCaptcha(() => submitRef.current?.())
        }
      })
      .finally(() => setLoading(false))
  }

  submitRef.current = runLookup

  useEffect(() => {
    if (autoRan.current) return
    if (!params.get('id')) return
    autoRan.current = true
    runLookup()
    // Intentionally once on mount when URL already has an id
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    runLookup()
  }

  const onClear = () => {
    setUserId('')
    setHash('')
    setResolved(null)
    setError(null)
    setFormError(null)
    setLoading(false)
  }

  const hasQuery = Boolean(userId.trim() || hash.trim() || resolved)

  return (
    <div className="mx-auto max-w-3xl space-y-6 lookup-rise">
      <PageHeader title={t('avatars.title')} lead={t('avatars.lead')} />

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="lookup-search-ring flex items-center gap-2 rounded-[999px] border border-border bg-surface p-1.5 pl-4 sm:pl-5">
          <label className="sr-only" htmlFor="avatars-user-id">
            {t('avatars.userId')}
          </label>
          <input
            id="avatars-user-id"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder={t('avatars.placeholder')}
            autoComplete="off"
            spellCheck={false}
            className="min-h-11 min-w-0 flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-muted sm:min-h-12"
          />
          {hasQuery ? (
            <button
              type="button"
              onClick={onClear}
              className="flex h-10 w-10 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
              aria-label={t('avatars.clear')}
              title={t('avatars.clear')}
            >
              <ClearIcon />
            </button>
          ) : null}
          <button
            type="submit"
            disabled={loading}
            className="flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-full bg-primary text-white transition-colors hover:bg-primary-hover disabled:cursor-wait disabled:opacity-70 sm:h-12 sm:w-12"
            aria-label={t('avatars.submit')}
            title={t('avatars.submit')}
          >
            <SearchArrowIcon />
          </button>
        </div>

        <Panel className="grid gap-4 p-5 sm:grid-cols-2 sm:p-6">
          <label className="text-sm sm:col-span-2">
            <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('avatars.hash')}
            </span>
            <input
              value={hash}
              onChange={(e) => setHash(e.target.value)}
              placeholder={t('avatars.hashHint')}
              className={`mt-1.5 ${controlClass}`}
            />
          </label>
          <label className="text-sm">
            <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('avatars.kind')}
            </span>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as Kind)}
              className={`mt-1.5 ${controlClass}`}
            >
              <option value="avatar">{t('avatars.kind.avatar')}</option>
              <option value="banner">{t('avatars.kind.banner')}</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('avatars.size')}
            </span>
            <select value={size} onChange={(e) => setSize(Number(e.target.value))} className={`mt-1.5 ${controlClass}`}>
              {[64, 128, 256, 512, 1024, 2048, 4096].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('avatars.format')}
            </span>
            <select value={format} onChange={(e) => setFormat(e.target.value)} className={`mt-1.5 ${controlClass}`}>
              <option value="">auto</option>
              <option value="png">png</option>
              <option value="jpg">jpg</option>
              <option value="webp">webp</option>
              <option value="gif">gif</option>
            </select>
          </label>
        </Panel>

        <p className="text-sm text-muted">{t('avatars.needFields')}</p>
        {formError ? (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        ) : null}
      </form>

      {loading ? <LoadingBlock rows={3} /> : null}
      {!loading && error ? <ErrorBanner message={errMsg} onRetry={runLookup} /> : null}

      {!loading && !error && resolved && url ? (
        <Panel className="p-5 sm:p-6">
          <SectionTitle>{t('avatars.preview')}</SectionTitle>
          <div className="mt-1 overflow-hidden rounded-[12px] border border-border bg-background-deep p-4">
            <img src={url} alt="" className="mx-auto max-h-72 object-contain" />
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <p className="break-all font-mono text-xs text-muted">
              {t('avatars.cdn')}: {url}
            </p>
            <div className="flex flex-wrap gap-3">
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
        </Panel>
      ) : null}

      {!loading && !error && resolved && kind === 'banner' && !activeHash ? (
        <ErrorBanner message={t('avatars.noBanner')} />
      ) : null}
    </div>
  )
}
