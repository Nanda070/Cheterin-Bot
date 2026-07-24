import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

/**
 * Root gate: redirect logged-out visitors on `/` to the marketing landing;
 * dashboard shell when authenticated with an active guild.
 */
export function PublicLandingOrDashboard({ children }: { children: ReactNode }) {
  const { user, isLoading, accessDenied } = useAuth()
  const location = useLocation()
  const t = useT()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-muted">{t('common.loading')}</div>
    )
  }

  if (accessDenied) {
    return <Navigate to="/access-denied" replace />
  }

  if (!user) {
    if (location.pathname === '/') {
      return <Navigate to="/about" replace />
    }
    return <Navigate to="/login" replace />
  }

  if (user.active_guild_id == null) {
    return <Navigate to="/servers" replace />
  }

  return <>{children}</>
}
