import { defineStore } from 'pinia'
import { ref } from 'vue'
import { clearAuth, loadAuth, saveAuth, type AuthTokens, type UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref<UserInfo | null>(null)
  const accessToken = ref('')

  // 从 localStorage 恢复（持久化，刷新页面保持登录）
  const saved = loadAuth()
  if (saved) {
    user.value = saved.user
    accessToken.value = saved.tokens.access_token
  }

  function setAuth(tokens: AuthTokens, info: UserInfo) {
    saveAuth(tokens, info)
    user.value = info
    accessToken.value = tokens.access_token
  }

  function setUser(info: UserInfo) {
    const saved = loadAuth()
    if (saved) saveAuth(saved.tokens, info)
    user.value = info
  }

  function clear() {
    clearAuth()
    user.value = null
    accessToken.value = ''
  }

  const isLoggedIn = () => !!accessToken.value
  const isAdmin = () => user.value?.role_code === 'ADMIN'

  return { user, accessToken, setAuth, setUser, clear, isLoggedIn, isAdmin }
})
