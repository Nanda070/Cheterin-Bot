import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, DiscordLogo, Plus, SignOut } from '@phosphor-icons/react'
import {
  fetchInviteUrl,
  fetchManageableGuilds,
  logout,
  selectGuild,
  type ManageableGuild,
} from '../api/client'
import { formatApiError, isForbiddenError } from '../api/errors'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'
import { BrandMark } from '../components/BrandMark'
import { LanguageToggle } from '../components/LanguageToggle'
import { Card } from '../components/ui/Card'

const SUPPORT_INVITE = 'https://discord.gg/cheterin'

function guildIconUrl(guild: ManageableGuild): string | null {
  if (!guild.icon) return null
  return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=64`
}

export function ServerSelectPage() {
  const { refresh } = useAuth()
  const t = useT()
  const navigate = useNavigate()
  const [guilds, setGuilds] = useState<ManageableGuild[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [awaitingInviteReturn, setAwaitingInviteReturn] = useState(false)

  const loadGuilds = useCallback(
    (opts?: { silent?: boolean }) => {
      if (!opts?.silent) setError(null)
      return fetchManageableGuilds()
        .then((data) => {
          setGuilds(data)
          return data
        })
        .catch((err) => {
          setError(formatApiError(err, t, 'servers.errorLoad'))
          return null
        })
    },
    [t],
  )

  useEffect(() => {
    let cancelled = false
    loadGuilds().then(() => {
      if (cancelled) return
    })
    return () => {
      cancelled = true
    }
  }, [loadGuilds])

  useEffect(() => {
    if (!awaitingInviteReturn) return
    const refreshOnReturn = () => {
      if (document.visibilityState === 'visible') {
        void loadGuilds({ silent: true }).then(() => setAwaitingInviteReturn(false))
      }
    }
    const onFocus = () => {
      void loadGuilds({ silent: true }).then(() => setAwaitingInviteReturn(false))
    }
    document.addEventListener('visibilitychange', refreshOnReturn)
    window.addEventListener('focus', onFocus)
    return () => {
      document.removeEventListener('visibilitychange', refreshOnReturn)
      window.removeEventListener('focus', onFocus)
    }
  }, [awaitingInviteReturn, loadGuilds])

  const handleSelect = async (guild: ManageableGuild) => {
    setPendingId(guild.id)
    setError(null)
    try {
      await selectGuild(guild.id)
      await refresh()
      navigate('/', { replace: true })
    } catch (err) {
      if (isForbiddenError(err)) {
        navigate('/access-denied', { replace: true })
        return
      }
      setError(formatApiError(err, t, 'servers.errorSelect'))
      setPendingId(null)
    }
  }

  const handleInvite = async (guild: ManageableGuild) => {
    setPendingId(guild.id)
    try {
      const url = await fetchInviteUrl(guild.id)
      window.open(url, '_blank', 'noopener,noreferrer')
      setAwaitingInviteReturn(true)
    } catch (err) {
      setError(formatApiError(err, t, 'servers.errorInvite'))
    } finally {
      setPendingId(null)
    }
  }

  const handleInviteNew = async () => {
    setPendingId('new')
    setError(null)
    try {
      const url = await fetchInviteUrl()
      window.open(url, '_blank', 'noopener,noreferrer')
      setAwaitingInviteReturn(true)
    } catch (err) {
      setError(formatApiError(err, t, 'servers.errorInvite'))
    } finally {
      setPendingId(null)
    }
  }

  const handleLogout = async () => {
    await logout()
    await refresh()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-dvh flex-col items-center gap-8 px-4 py-10">
      <div className="flex w-full max-w-2xl items-center justify-between gap-3">
        <BrandMark to="/about" iconSize={22} labelClassName="text-lg font-semibold" />
        <div className="flex items-center gap-3">
          <LanguageToggle />
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-foreground"
          >
            <SignOut size={16} />
            {t('nav.logout')}
          </button>
        </div>
      </div>

      <div className="flex w-full max-w-2xl flex-col gap-2 text-center">
        <h1 className="text-xl font-semibold text-foreground">{t('servers.title')}</h1>
        <p className="text-sm text-muted">{t('servers.subtitle')}</p>
      </div>

      {error && (
        <div className="w-full max-w-2xl rounded-control border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="flex w-full max-w-2xl flex-col gap-3">
        {guilds === null && !error && <p className="text-center text-sm text-muted">{t('servers.loading')}</p>}
        {guilds !== null && guilds.length === 0 && (
          <Card className="text-center text-sm text-muted">{t('servers.empty')}</Card>
        )}
        {guilds?.map((guild) => (
          <Card key={guild.id} className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              {guildIconUrl(guild) ? (
                <img src={guildIconUrl(guild)!} alt="" className="h-10 w-10 rounded-full" />
              ) : (
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-muted text-sm font-semibold text-primary">
                  {guild.name.slice(0, 1).toUpperCase()}
                </span>
              )}
              <span className="truncate text-sm font-medium text-foreground">{guild.name}</span>
            </div>
            {guild.has_bot ? (
              <button
                type="button"
                disabled={pendingId === guild.id}
                onClick={() => handleSelect(guild)}
                className="inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-control bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
              >
                {pendingId === guild.id ? t('servers.selecting') : t('servers.select')}
              </button>
            ) : (
              <button
                type="button"
                disabled={pendingId === guild.id}
                onClick={() => handleInvite(guild)}
                className="inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-control border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-hover disabled:opacity-60"
              >
                <Plus size={16} />
                {t('servers.addBot')}
              </button>
            )}
          </Card>
        ))}

        {guilds !== null && (
          <button
            type="button"
            disabled={pendingId === 'new'}
            onClick={handleInviteNew}
            className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-control border border-dashed border-border px-4 py-3 text-sm font-medium text-muted transition-colors hover:border-primary hover:bg-surface-hover hover:text-foreground disabled:opacity-60"
          >
            <Plus size={18} weight="bold" />
            {pendingId === 'new' ? t('servers.addBotOpening') : t('servers.addBotOther')}
          </button>
        )}
      </div>

      <div className="flex flex-col items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-muted">
          <DiscordLogo size={14} weight="fill" />
          {t('servers.discordLogin')}
        </div>
        <nav
          className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-sm"
          aria-label={t('servers.footerLinks')}
        >
          <Link to="/docs" className="flex items-center gap-1 text-muted transition-colors hover:text-foreground">
            <BookOpen size={16} />
            {t('nav.docs')}
          </Link>
          <Link to="/credits" className="text-muted transition-colors hover:text-foreground">
            {t('nav.credits')}
          </Link>
          <Link to="/terms" className="text-muted transition-colors hover:text-foreground">
            {t('nav.terms')}
          </Link>
          <Link to="/privacy" className="text-muted transition-colors hover:text-foreground">
            {t('nav.privacy')}
          </Link>
          <Link to="/cookies" className="text-muted transition-colors hover:text-foreground">
            {t('nav.cookies')}
          </Link>
          <Link to="/disclaimer" className="text-muted transition-colors hover:text-foreground">
            {t('nav.disclaimer')}
          </Link>
          <a
            href={SUPPORT_INVITE}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-muted transition-colors hover:text-foreground"
          >
            <DiscordLogo size={16} weight="fill" />
            {t('servers.support')}
          </a>
        </nav>
      </div>
    </div>
  )
}
