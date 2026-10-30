import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { getAccessToken, loadAuth } from '@/api/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  // 门户：匿名可访问，仅展示公开内容
  { path: '/portal', name: 'portal', component: () => import('@/views/portal/PortalHomeView.vue'), meta: { public: true } },
  {
    path: '/portal/search',
    name: 'portal-search',
    component: () => import('@/views/portal/PortalSearchView.vue'),
    meta: { public: true },
  },
  {
    path: '/portal/entries/:id',
    name: 'portal-entry',
    component: () => import('@/views/portal/PortalEntryView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: { name: 'home' } },
      { path: 'home', name: 'home', component: () => import('@/views/HomeView.vue') },
      { path: 'categories', name: 'categories', component: () => import('@/views/CategoryView.vue') },
      { path: 'knowledge', name: 'knowledge', component: () => import('@/views/KnowledgeView.vue') },
      { path: 'rules', name: 'rules', component: () => import('@/views/RuleView.vue') },
      { path: 'services', name: 'services', component: () => import('@/views/ServiceMarketView.vue') },
      { path: 'entries', name: 'entries', component: () => import('@/views/EntryListView.vue') },
      { path: 'entries/new', name: 'entry-new', component: () => import('@/views/EntryEditView.vue') },
      { path: 'entries/:id/edit', name: 'entry-edit', component: () => import('@/views/EntryEditView.vue') },
      { path: 'metadata', name: 'metadata', component: () => import('@/views/MetadataView.vue') },
      {
        path: 'announcements',
        name: 'announcements',
        component: () => import('@/views/AnnouncementView.vue'),
        meta: { roles: ['ADMIN'] },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'portal' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录访问受限页 → 登录页；已登录访问登录/注册页 → 首页；ADMIN 页面校验角色
router.beforeEach((to) => {
  const authed = !!getAccessToken()
  if (to.meta.public) {
    if (authed && (to.name === 'login' || to.name === 'register')) {
      return { name: 'home' }
    }
    return true
  }
  if (!authed) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  const roles = to.meta.roles as string[] | undefined
  if (roles?.length) {
    const role = loadAuth()?.user.role_code
    if (!role || !roles.includes(role)) return { name: 'home' }
  }
  return true
})

export default router
