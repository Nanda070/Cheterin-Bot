import { Crown } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchSuperAdminGuilds, type SuperAdminGuild } from '../api/client'
import { Card } from '../components/ui/Card'

export function SuperAdminPage() {
  const [guilds, setGuilds] = useState<SuperAdminGuild[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchSuperAdminGuilds()
      .then(setGuilds)
      .catch(() => setError('Не удалось загрузить список серверов — недостаточно прав.'))
  }, [])

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Crown size={22} className="text-primary" />
        Серверы бота
      </h1>
      <p className="text-sm text-muted">Список всех серверов, на которых сейчас присутствует бот.</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!error && !guilds && <p className="text-sm text-muted">Загрузка…</p>}
      {guilds && guilds.length === 0 && <p className="text-sm text-muted">Бот пока не состоит ни на одном сервере.</p>}

      <div className="flex flex-col gap-3">
        {guilds?.map((guild) => (
          <Card key={guild.id} className="flex items-center gap-3">
            {guild.icon ? (
              <img src={guild.icon} alt="" className="h-10 w-10 shrink-0 rounded-full" />
            ) : (
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-muted text-sm font-semibold text-primary">
                {guild.name.slice(0, 1).toUpperCase()}
              </span>
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">{guild.name}</p>
              <p className="text-xs text-muted">
                ID: {guild.id} · {guild.member_count} участников
                {guild.owner_id && <> · Владелец: {guild.owner_id}</>}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
