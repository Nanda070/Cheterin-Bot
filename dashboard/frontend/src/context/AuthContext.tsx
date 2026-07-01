import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchCurrentUser, type DashboardUser } from '../api/client'

interface AuthContextValue {
  user: DashboardUser | null
  isLoading: boolean
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DashboardUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = async () => {
    setIsLoading(true)
    try {
      setUser(await fetchCurrentUser())
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return <AuthContext.Provider value={{ user, isLoading, refresh }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
