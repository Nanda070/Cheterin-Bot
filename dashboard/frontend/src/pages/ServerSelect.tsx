import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DiscordLogo, Plus, SignOut, Sparkle } from '@phosphor-icons/react'
import {
  fetchInviteUrl,
  fetchManageableGuilds,
  logout,
  selectGuild,
  type ManageableGuild,
} from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Card } from '../components/ui/Card'

function guildIconUrl(guild: ManageableGuild): string | null {
  if (!guild.icon) return null
  return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=64`
}

export function ServerSelectPage() {
  const { refresh } = useAuth()
  const navigate = useNavigate()
  const [guilds, setGuilds] = useState<ManageableGuild[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchManageableGuilds()
      .then((data) => {
        if (!cancelled) setGuilds(data)
      })
      .catch(() => {
        if (!cancelled) setError('Не удалось загрузить список серверов. Попробуйте позже.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleSelect = async (guild: ManageableGuild) => {
    setPendingId(guild.id)
    setError(null)
    try {
      await selectGuild(guild.id)
      await refresh()
      navigate('/', { replace: true })
    } catch {
      setError('Не удалось выбрать сервер — проверьте, что у вас есть право «Управление сервером».')
      setPendingId(null)
    }
  }

  const handleInvite = async (guild: ManageableGuild) => {
    setPendingId(guild.id)
    try {
      const url = await fetchInviteUrl(guild.id)
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch {
      setError('Не удалось получить ссылку приглашения.')
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
    } catch {
      setError('Не удалось получить ссылку приглашения.')
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
      <div className="flex w-full max-w-2xl items-center justify-between">
        <div className="flex items-center gap-2 text-foreground">
          <Sparkle size={22} weight="fill" className="text-primary" />
          <span className="text-lg font-semibold">Cheterin</span>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-foreground"
        >
          <SignOut size={16} />
          Выйти
        </button>
      </div>

      <div className="flex w-full max-w-2xl flex-col gap-2 text-center">
        <h1 className="text-xl font-semibold text-foreground">Выберите сервер</h1>
        <p className="text-sm text-muted">
          Управлять можно серверами, где у вас есть право «Управление сервером».
        </p>
      </div>

      {error && (
        <div className="w-full max-w-2xl rounded-control border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="flex w-full max-w-2xl flex-col gap-3">
        {guilds === null && !error && <p className="text-center text-sm text-muted">Загрузка серверов…</p>}
        {guilds !== null && guilds.length === 0 && (
          <Card className="text-center text-sm text-muted">
            Нет серверов, которыми вы можете управлять.
          </Card>
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
                {pendingId === guild.id ? 'Открываем…' : 'Выбрать'}
              </button>
            ) : (
              <button
                type="button"
                disabled={pendingId === guild.id}
                onClick={() => handleInvite(guild)}
                className="inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-control border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-hover disabled:opacity-60"
              >
                <Plus size={16} />
                Добавить бота
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
            {pendingId === 'new' ? 'Открываем Discord…' : 'Добавить бота на другой сервер'}
          </button>
        )}
      </div>

      <div className="flex items-center gap-1.5 text-xs text-muted">
        <DiscordLogo size={14} weight="fill" />
        Вход выполнен через Discord
      </div>
    </div>
  )
}
