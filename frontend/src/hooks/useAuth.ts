import { createContext, useContext, useState, useCallback } from 'react'
import type { User } from '../api/types'
import * as api from '../api/client'

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const TOKEN_KEY = 'wayos_token'
const USER_KEY = 'wayos_user'

function loadUser(): User | null {
  try {
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export function useAuthState(): AuthState {
  const [user, setUser] = useState<User | null>(loadUser)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAuth = useCallback(async (authFn: () => ReturnType<typeof api.login>) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await authFn()
      localStorage.setItem(TOKEN_KEY, res.access_token)
      const u: User = { user_id: res.user_id, email: res.email }
      localStorage.setItem(USER_KEY, JSON.stringify(u))
      setUser(u)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Authentication failed'
      setError(msg)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(
    (email: string, password: string) => handleAuth(() => api.login(email, password)),
    [handleAuth],
  )

  const register = useCallback(
    (email: string, password: string) => handleAuth(() => api.register(email, password)),
    [handleAuth],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }, [])

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
  }
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
