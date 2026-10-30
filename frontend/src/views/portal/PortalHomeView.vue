<template>
  <div class="portal">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand" @click="router.push('/portal')">📚 知识库门户</div>
        <div class="search-box">
          <el-input
            v-model="keyword"
            placeholder="搜索知识标题或内容…"
            size="large"
            clearable
            @keyup.enter="onSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="onSearch">搜索</el-button>
            </template>
          </el-input>
        </div>
        <div class="topbar-right">
          <template v-if="authed">
            <span class="hello">你好，{{ user?.nickname || user?.username }}</span>
            <el-button type="primary" plain @click="router.push('/home')">进入工作台</el-button>
          </template>
          <template v-else>
            <el-button text @click="router.push('/register')">注册</el-button>
            <el-button type="primary" @click="router.push('/login')">登录</el-button>
          </template>
        </div>
      </div>
    </header>

    <main class="body">
      <!-- 轮播 / 主视觉 -->
      <section class="hero">
        <el-carousel v-if="data.banners.length" height="220px" :interval="5000" class="carousel">
          <el-carousel-item v-for="b in data.banners" :key="b.id">
            <div class="banner" @click="openBanner(b)">
              <img v-if="b.image_url" :src="b.image_url" :alt="b.title" />
              <div v-else class="banner-fallback">
                <h3>{{ b.title }}</h3>
                <p>{{ b.content || '知识沉淀 · 共享共进' }}</p>
              </div>
            </div>
          </el-carousel-item>
        </el-carousel>
        <div v-else class="hero-fallback">
          <h1>企业知识库</h1>
          <p>沉淀经验、共享知识、让每一次检索都有答案</p>
          <div class="hero-stats">
            <div class="stat"><b>{{ data.stats.public_entries }}</b><span>公开知识</span></div>
            <div class="stat"><b>{{ categoryTotal }}</b><span>知识分类</span></div>
            <div class="stat"><b>{{ data.notices.length }}</b><span>公告</span></div>
          </div>
        </div>
      </section>

      <!-- 公告栏 -->
      <section v-if="data.notices.length" class="notice-bar">
        <el-icon class="notice-icon"><Bell /></el-icon>
        <span class="notice-label">公告</span>
        <div class="notice-list">
          <span v-for="n in data.notices.slice(0, 3)" :key="n.id" class="notice-item" @click="openNotice(n)">
            {{ n.title }}
          </span>
        </div>
      </section>

      <div class="grid">
        <!-- 分类导航 -->
        <aside class="panel nav-panel">
          <h3 class="panel-title">知识分类</h3>
          <div class="cat-all" :class="{ active: !activeCat }" @click="goCategory(undefined)">
            全部知识 <span class="count">{{ data.stats.public_entries }}</span>
          </div>
          <el-tree
            :data="data.categories"
            node-key="id"
            :props="{ label: 'name', children: 'children' }"
            :expand-on-click-node="false"
            default-expand-all
            @node-click="(n: PortalCategory) => goCategory(n)"
          >
            <template #default="{ data: node }">
              <span class="cat-node" :class="{ active: activeCat === node.id }">
                {{ node.name }}
                <span class="count">{{ node.entry_count }}</span>
              </span>
            </template>
          </el-tree>
        </aside>

        <!-- 最新知识 -->
        <section class="panel main-panel">
          <div class="panel-head">
            <h3 class="panel-title">最新知识</h3>
            <el-link type="primary" :underline="false" @click="router.push('/portal/search')">查看全部</el-link>
          </div>
          <div v-if="!data.latest.length" class="empty">暂无公开知识</div>
          <ul class="entry-list">
            <li v-for="e in data.latest" :key="e.id" class="entry-item" @click="openEntry(e.id)">
              <div class="entry-main">
                <span class="entry-title">{{ e.title }}</span>
                <span class="entry-summary">{{ e.summary || '—' }}</span>
              </div>
              <div class="entry-meta">
                <el-tag v-for="t in e.tags" :key="t.id" size="small" effect="plain">{{ t.name }}</el-tag>
                <span class="muted">{{ fmtDate(e.created_at) }}</span>
              </div>
            </li>
          </ul>
        </section>

        <!-- 热门排行 -->
        <aside class="panel hot-panel">
          <h3 class="panel-title">热门排行</h3>
          <div v-if="!data.hot.length" class="empty">暂无数据</div>
          <ol class="hot-list">
            <li v-for="(e, i) in data.hot" :key="e.id" class="hot-item" @click="openEntry(e.id)">
              <span class="rank" :class="`rank-${i + 1}`">{{ i + 1 }}</span>
              <span class="hot-title">{{ e.title }}</span>
              <span class="views">{{ e.view_count }} 次</span>
            </li>
          </ol>
        </aside>
      </div>
    </main>

    <footer class="footer">知识库管理系统 · 门户首页（匿名可访问，仅展示公开内容）</footer>

    <el-dialog v-model="dialog.visible" :title="dialog.title" width="560px">
      <div class="dialog-body">{{ dialog.content }}</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Bell } from '@element-plus/icons-vue'
import {
  getPortalHome,
  type PortalHome,
  type PortalCategory,
  type Announcement,
} from '@/api/portal'
import { loadAuth } from '@/api/auth'

const router = useRouter()
const keyword = ref('')
const activeCat = ref<number | undefined>()

const data = reactive<PortalHome>({
  banners: [],
  notices: [],
  latest: [],
  hot: [],
  categories: [],
  stats: { public_entries: 0 },
})

// 门户首页为公开页，直接读本地缓存判断登录态（不发请求）
const auth = loadAuth()
const authed = computed(() => !!auth)
const user = computed(() => auth?.user)

const categoryTotal = computed(() => {
  let n = 0
  const walk = (list: PortalCategory[]) => list.forEach((c) => { n++; walk(c.children) })
  walk(data.categories)
  return n
})

const dialog = reactive({ visible: false, title: '', content: '' })

function fmtDate(s: string): string {
  return s ? s.slice(0, 10) : ''
}

function onSearch() {
  const kw = keyword.value.trim()
  router.push({ path: '/portal/search', query: kw ? { keyword: kw } : {} })
}

function goCategory(cat?: PortalCategory) {
  activeCat.value = cat?.id
  router.push({ path: '/portal/search', query: cat ? { category_id: cat.id, name: cat.name } : {} })
}

function openEntry(id: number) {
  router.push(`/portal/entries/${id}`)
}

function openNotice(n: Announcement) {
  dialog.title = n.title
  dialog.content = n.content || '（无正文）'
  dialog.visible = true
}

function openBanner(b: Announcement) {
  if (b.link_url) {
    window.open(b.link_url, '_blank', 'noopener,noreferrer')
  } else {
    openNotice(b)
  }
}

onMounted(async () => {
  const home = await getPortalHome()
  Object.assign(data, home)
})
</script>

<style scoped>
.portal {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}
.topbar {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  position: sticky;
  top: 0;
  z-index: 10;
}
.topbar-inner {
  max-width: 1180px;
  margin: 0 auto;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 0 16px;
}
.brand {
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.search-box {
  flex: 1;
  max-width: 520px;
}
.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.hello {
  color: #606266;
  font-size: 13px;
  margin-right: 4px;
}
.body {
  flex: 1;
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  padding: 20px 16px 32px;
  box-sizing: border-box;
}
.hero {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
}
.carousel {
  border-radius: 10px;
  overflow: hidden;
}
.banner {
  height: 100%;
  cursor: pointer;
  background: #409eff;
}
.banner img {
  width: 100%;
  height: 220px;
  object-fit: cover;
}
.banner-fallback {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(120deg, #3a8ee6, #6f42c1);
}
.banner-fallback h3 {
  font-size: 24px;
  margin: 0 0 8px;
}
.hero-fallback {
  border-radius: 10px;
  padding: 40px 32px;
  color: #fff;
  background: linear-gradient(120deg, #3a8ee6, #6f42c1);
}
.hero-fallback h1 {
  margin: 0 0 10px;
  font-size: 30px;
}
.hero-fallback p {
  margin: 0 0 22px;
  opacity: 0.92;
}
.hero-stats {
  display: flex;
  gap: 40px;
}
.stat b {
  font-size: 24px;
  margin-right: 6px;
}
.stat span {
  opacity: 0.9;
  font-size: 13px;
}
.notice-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-left: 3px solid #e6a23c;
}
.notice-icon {
  color: #e6a23c;
}
.notice-label {
  font-weight: 600;
  color: #e6a23c;
  font-size: 13px;
}
.notice-list {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
}
.notice-item {
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notice-item:hover {
  color: #409eff;
}
.grid {
  display: grid;
  grid-template-columns: 240px 1fr 280px;
  gap: 16px;
  align-items: start;
}
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.panel-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-head .panel-title {
  margin-bottom: 12px;
}
.cat-all {
  display: flex;
  justify-content: space-between;
  padding: 7px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
}
.cat-all:hover,
.cat-all.active {
  background: #ecf5ff;
  color: #409eff;
}
.cat-node {
  flex: 1;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
  padding-right: 6px;
}
.cat-node.active {
  color: #409eff;
  font-weight: 600;
}
.count {
  color: #a8abb2;
  font-size: 12px;
}
.entry-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.entry-item {
  padding: 12px 8px;
  border-bottom: 1px dashed #ebeef5;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.entry-item:last-child {
  border-bottom: none;
}
.entry-item:hover .entry-title {
  color: #409eff;
}
.entry-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.entry-title {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}
.entry-summary {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 460px;
}
.entry-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.muted {
  color: #c0c4cc;
  font-size: 12px;
}
.hot-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.hot-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 4px;
  cursor: pointer;
  border-bottom: 1px dashed #f2f3f5;
}
.hot-item:last-child {
  border-bottom: none;
}
.hot-item:hover .hot-title {
  color: #409eff;
}
.rank {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  background: #f0f2f5;
  color: #909399;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rank-1 {
  background: #f56c6c;
  color: #fff;
}
.rank-2 {
  background: #e6a23c;
  color: #fff;
}
.rank-3 {
  background: #409eff;
  color: #fff;
}
.hot-title {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.views {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.empty {
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 24px 0;
}
.footer {
  text-align: center;
  color: #a8abb2;
  font-size: 12px;
  padding: 18px 0 24px;
}
.dialog-body {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #606266;
}
@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
