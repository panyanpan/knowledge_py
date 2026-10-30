import http from './http'
import type { LoginResult, UserInfo } from './auth'

export interface RegisterPayload {
  username: string
  password: string
  email: string
  nickname?: string
}

export function registerApi(payload: RegisterPayload): Promise<UserInfo> {
  return http.post('/auth/register', payload)
}

export function loginApi(username: string, password: string): Promise<LoginResult> {
  return http.post('/auth/login', { username, password })
}

export function logoutApi(): Promise<null> {
  return http.post('/auth/logout')
}

export function meApi(): Promise<UserInfo> {
  return http.get('/auth/me')
}
