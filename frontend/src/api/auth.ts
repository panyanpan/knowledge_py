export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  role_code: 'ADMIN' | 'USER'
  status: number
  created_at: string
}

export interface LoginResult {
  tokens: AuthTokens
  user: UserInfo
}

const AUTH_KEY = 'kb_auth'

export function loadAuth(): { tokens: AuthTokens; user: UserInfo } | null {
  const raw = localStorage.getItem(AUTH_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem(AUTH_KEY)
    return null
  }
}

export function saveAuth(tokens: AuthTokens, user: UserInfo): void {
  localStorage.setItem(AUTH_KEY, JSON.stringify({ tokens, user }))
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_KEY)
}

export function getAccessToken(): string | null {
  return loadAuth()?.tokens.access_token ?? null
}
