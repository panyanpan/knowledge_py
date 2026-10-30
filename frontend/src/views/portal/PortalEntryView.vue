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
        <span>知识详情</span>
      </div>

      <div v-if="error" class="panel error">{{ error }}</div>

      <article v-else-if="entry" class="panel article">
        <h1 class="title">{{ entry.title }}</h1>
        <div class="meta">
          <el-tag v-for="t in entry.tags" :key="t.id" size="small" effect="plain">{{ t.name }}</el-tag>
          <span class="muted">{{ fmtTime(entry.created_at) }} · {{ entry.view_count }} 次浏览</span>
        </div>
        <p v-if="entry.summary" class="summary">{{ entry.summary }}</p>
        <!-- 正文已在后端经 nh3 白名单清洗，前端按已清洗 HTML 渲染 -->
        <div class="content" v-html="entry.content || '<p>（暂无正文）</p>'" />
        <div v-if="entry.attachments.length" class="att">
          <h4>附件</h4>
          <div v-for="a in entry.attachments" :key="a.id" class="att-item">
            <span>{{ a.file_name }}（{{ fmtSize(a.file_size) }}）</span>
            <el-button v-if="authed" link type="primary" @click="onDownload(a)">下载</el-button>
            <span v-else class="muted">登录后可下载</span>
          </div>
        </div>
      </article>

      <div v-else class="panel">加载中…</div>
    </main>

    <footer class="footer">知识库管理系统 · 门户详情</footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getPublicEntry } from '@/api/portal'
import type { EntryDetail, Attachment } from '@/api/entries'
import { downloadAttachment } from '@/api/attachments'
import { loadAuth } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authed = computed(() => !!loadAuth())
const keyword = ref('')
const entry = ref<EntryDetail | null>(null)
const error = ref('')

function fmtTime(s: string): string {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}
function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
function onSearch() {
  const kw = keyword.value.trim()
  router.push({ path: '/portal/search', query: kw ? { keyword: kw } : {} })
}
async function onDownload(a: Attachment) {
  await downloadAttachment(a)
}

onMounted(async () => {
  try {
    entry.value = await getPublicEntry(Number(route.params.id))
  } catch {
    error.value = '该知识不存在或未公开'
  }
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
  max-width: 900px;
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
  padding: 28px 32px;
}
.error {
  text-align: center;
  color: #909399;
  padding: 60px 0;
}
.title {
  margin: 0 0 12px;
  font-size: 24px;
  color: #303133;
  line-height: 1.4;
}
.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f2f3f5;
}
.muted {
  color: #c0c4cc;
  font-size: 12px;
}
.summary {
  color: #606266;
  background: #fafafa;
  border-left: 3px solid #dcdfe6;
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 13px;
  margin: 16px 0;
}
.content {
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
  word-break: break-word;
}
.content :deep(img) {
  max-width: 100%;
}
.content :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
.content :deep(table) {
  border-collapse: collapse;
}
.content :deep(td),
.content :deep(th) {
  border: 1px solid #ebeef5;
  padding: 6px 10px;
}
.att {
  margin-top: 28px;
  border-top: 1px dashed #ebeef5;
  padding-top: 16px;
}
.att h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #303133;
}
.att-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #606266;
  padding: 4px 0;
}
.footer {
  text-align: center;
  color: #a8abb2;
  font-size: 12px;
  padding: 18px 0 24px;
}
</style>
