import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'
import { LandingPage } from '../pages/Landing'

/**
 * Root gate: public marketing landing on `/` when logged out;
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
      return <LandingPage />
    }
    return <Navigate to="/login" replace />
  }

  if (user.active_guild_id == null) {
    return <Navigate to="/servers" replace />
  }

  return <>{children}</>
}
