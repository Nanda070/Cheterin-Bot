import { Crown } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchSuperAdminGuilds, type SuperAdminGuild } from '../api/client'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

export function SuperAdminPage() {
  const t = useT()
  const [guilds, setGuilds] = useState<SuperAdminGuild[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchSuperAdminGuilds()
      .then(setGuilds)
      .catch(() => setError(t('superadmin.errorLoad')))
  }, [t])

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Crown size={22} className="text-primary" />
        {t('superadmin.title')}
      </h1>
      <p className="text-sm text-muted">{t('superadmin.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!error && !guilds && <p className="text-sm text-muted">{t('common.loading')}</p>}
      {guilds && guilds.length === 0 && <p className="text-sm text-muted">{t('superadmin.empty')}</p>}

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
                {t('superadmin.guildInfo', { id: guild.id, count: guild.member_count })}
                {guild.owner_id && t('superadmin.owner', { ownerId: guild.owner_id })}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
