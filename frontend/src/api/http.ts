import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { clearAuth, getAccessToken, loadAuth, saveAuth, type AuthTokens } from './auth'

interface ApiBody<T = unknown> {
  code: number
  message: string
  data: T
}

const http = axios.create({ baseURL: '/api/v1', timeout: 15000 })

// 请求拦截：自动携带 token
http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 刷新排队：并发 401 共享同一次刷新（refresh token 为旋转策略，旧刷新令牌一次性）
let refreshing: Promise<string | null> | null = null

async function tryRefresh(): Promise<string | null> {
  if (refreshing) return refreshing
  refreshing = (async () => {
    const auth = loadAuth()
    if (!auth) return null
    try {
      const resp = await axios.post<ApiBody<{ tokens: AuthTokens }>>(
        '/api/v1/auth/refresh',
        { refresh_token: auth.tokens.refresh_token },
        { timeout: 15000 },
      )
      const body = resp.data
      if (body.code !== 0) return null
      saveAuth(body.data.tokens, auth.user)
      return body.data.tokens.access_token
    } catch {
      return null
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

// 响应拦截：统一解包 { code, message, data }；401(code=1003) 自动刷新重放
http.interceptors.response.use(
  // 解包后返回业务 data，类型上不再是 AxiosResponse，统一断言以简化调用方泛型
  (resp): any => {
    const body = resp.data as ApiBody
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(body)
    }
    return body
  },
  async (err: AxiosError<ApiBody>) => {
    const { response, config } = err
    const bizCode = response?.data?.code
    const body = response?.data as ApiBody | undefined

    if (response?.status === 401 && bizCode === 1003) {
      const cfg = config as AxiosRequestConfig & { _retried?: boolean }
      if (!cfg._retried) {
        cfg._retried = true
        const newToken = await tryRefresh()
        if (newToken) {
          cfg.headers = { ...cfg.headers, Authorization: `Bearer ${newToken}` }
          return http.request(cfg)
        }
      }
      clearAuth()
      ElMessage.error('登录已失效，请重新登录')
      const current = window.location.pathname + window.location.search
      if (!current.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      }
      return Promise.reject(err)
    }

    ElMessage.error(body?.message || err.message || '网络错误')
    return Promise.reject(err)
  },
)

export default http
