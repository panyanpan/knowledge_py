<template>
  <div class="portal">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand" @click="router.push('/portal')">📚 知识库门户</div>
        <div class="search-box">
          <el-input v-model="keyword" placeholder="搜索知识标题或内容…" size="large" clearable @keyup.enter="onSearch">
            <template #append>
              <el-button :icon="Search" @click="onSearch">搜索</el-button>
            </template>
          </el-input>
        </div>
        <div class="topbar-right">
          <el-button v-if="authed" type="primary" plain @click="router.push('/home')">进入工作台</el-button>
          <el-button v-else type="primary" @click="router.push('/login')">登录</el-button>
        </div>
      </div>
    </header>

    <main class="body">
      <div class="crumb">
        <el-link :underline="false" @click="router.push('/portal')">门户首页</el-link>
        <span class="sep">/</span>
        <span>{{ resultTitle }}</span>
      </div>

      <div class="panel">
        <div class="result-head">
          <h2 class="result-title">{{ resultTitle }}</h2>
          <span class="muted">共 {{ total }} 条公开知识</span>
        </div>

        <div v-if="loading" class="empty">加载中…</div>
        <div v-else-if="!rows.length" class="empty">没有找到匹配的公开知识</div>
        <ul v-else class="result-list">
          <li v-for="e in rows" :key="e.id" class="result-item" @click="router.push(`/portal/entries/${e.id}`)">
            <h3 class="item-title">{{ e.title }}</h3>
            <p class="item-summary">{{ e.summary || '（无摘要）' }}</p>
            <div class="item-meta">
              <el-tag v-for="t in e.tags" :key="t.id" size="small" effect="plain">{{ t.name }}</el-tag>
              <span class="muted">{{ fmtTime(e.created_at) }} · {{ e.view_count }} 次浏览</span>
            </div>
          </li>
        </ul>

        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          class="pager"
          layout="prev, pager, next, total"
          :total="total"
          @current-change="load"
        />
      </div>
    </main>

    <footer class="footer">知识库管理系统 · 门户搜索</footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { listPublicEntries } from '@/api/portal'
import type { EntryBrief } from '@/api/entries'
import { loadAuth } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authed = computed(() => !!loadAuth())

const keyword = ref(String(route.query.keyword ?? ''))
const categoryId = ref<number | undefined>(
  route.query.category_id ? Number(route.query.category_id) : undefined,
)
const categoryName = ref(String(route.query.name ?? ''))
const rows = ref<EntryBrief[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

const resultTitle = computed(() => {
  if (keyword.value) return `搜索「${keyword.value}」`
  if (categoryId.value) return `分类：${categoryName.value || categoryId.value}`
  return '全部公开知识'
})

function fmtTime(s: string): string {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const data = await listPublicEntries({
      keyword: keyword.value.trim() || undefined,
      category_id: categoryId.value,
      page: page.value,
      page_size: pageSize,
    })
    rows.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  router.replace({
    path: '/portal/search',
    query: keyword.value.trim() ? { keyword: keyword.value.trim() } : {},
  })
  load()
}

// 同一路由下 query 变化（首页分类/搜索跳转）时同步
watch(
  () => route.query,
  (q) => {
    keyword.value = String(q.keyword ?? '')
    categoryId.value = q.category_id ? Number(q.category_id) : undefined
    categoryName.value = String(q.name ?? '')
    page.value = 1
    load()
  },
)

onMounted(load)
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
}
.body {
  flex: 1;
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  padding: 16px 16px 32px;
  box-sizing: border-box;
}
.crumb {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}
.sep {
  margin: 0 6px;
}
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px 24px;
}
.result-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}
.result-title {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
.muted {
  color: #909399;
  font-size: 12px;
}
.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.result-item {
  padding: 16px 6px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
}
.result-item:hover .item-title {
  color: #409eff;
}
.item-title {
  margin: 0 0 6px;
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}
.item-summary {
  margin: 0 0 8px;
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.empty {
  text-align: center;
  color: #c0c4cc;
  padding: 40px 0;
  font-size: 13px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
.footer {
  text-align: center;
  color: #a8abb2;
  font-size: 12px;
  padding: 18px 0 24px;
}
</style>
