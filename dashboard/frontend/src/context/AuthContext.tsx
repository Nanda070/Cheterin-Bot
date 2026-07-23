import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchCurrentUser, type DashboardUser } from '../api/client'

interface AuthContextValue {
  user: DashboardUser | null
  isLoading: boolean
  accessDenied: boolean
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DashboardUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [accessDenied, setAccessDenied] = useState(false)

  const refresh = async () => {
    setIsLoading(true)
    try {
      setUser(await fetchCurrentUser())
      setAccessDenied(false)
    } catch (error) {
      if (error instanceof Error && error.name === 'AccessDeniedError') {
        setAccessDenied(true)
        setUser(null)
      } else {
        console.error('Failed to refresh user session:', error)
        setAccessDenied(false)
        setUser(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, accessDenied, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
