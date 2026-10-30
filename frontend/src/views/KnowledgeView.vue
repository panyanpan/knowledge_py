<template>
  <div class="kb-page">
    <div class="crumb">
      <span>知识管理</span>
      <span class="sep">›</span>
      <b>知识库</b>
    </div>

    <div class="page-head">
      <div>
        <h2>知识管理</h2>
        <p class="page-desc">
          统一收录政务服务事项、政策法规、高效办成一件事等业务知识，支撑知识加工、发布与门户检索，做到一数一源、动态更新。
        </p>
      </div>
      <span class="page-sub">数据更新于 {{ updatedAt }}</span>
    </div>

    <!-- 统计条 -->
    <section class="stat-row">
      <div class="stat">
        <span class="stat-ico ico-blue"><el-icon><Collection /></el-icon></span>
        <dl class="stat-txt">
          <dt>知识总量</dt>
          <dd>{{ stats.total }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-green"><el-icon><CircleCheck /></el-icon></span>
        <dl class="stat-txt">
          <dt>已发布知识</dt>
          <dd>{{ stats.published }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-orange"><el-icon><Clock /></el-icon></span>
        <dl class="stat-txt">
          <dt>待发布 / 已下线</dt>
          <dd>{{ stats.draft + stats.offline }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-purple"><el-icon><TrendCharts /></el-icon></span>
        <dl class="stat-txt">
          <dt>本月新增</dt>
          <dd>{{ stats.month_new }}<small>条</small></dd>
        </dl>
      </div>
    </section>

    <!-- 知识清单 -->
    <section class="panel">
      <div class="panel-head">
        <h3><el-icon><Reading /></el-icon>知识清单</h3>
        <div class="tools">
          <el-input
            v-model="query.keyword"
            class="tool-search"
            placeholder="按标题 / 摘要 / 关键词检索"
            clearable
            :prefix-icon="Search"
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-select v-model="query.knowledge_type" class="tool-select" placeholder="全部知识类型" clearable @change="onSearch">
            <el-option v-for="t in options.knowledge_types" :key="t" :label="t" :value="t" />
          </el-select>
          <el-tree-select
            v-model="query.category_id"
            class="tool-select"
            :data="categoryTree"
            check-strictly
            clearable
            placeholder="全部知识分类"
            @change="onSearch"
          />
          <el-select v-model="query.status" class="tool-select tool-select-sm" placeholder="全部状态" clearable @change="onSearch">
            <el-option label="已发布" :value="1" />
            <el-option label="草稿" :value="0" />
            <el-option label="已下线" :value="2" />
          </el-select>
          <el-button class="btn-ghost" :icon="RefreshLeft" @click="onReset">重置</el-button>
          <el-button class="btn-ghost" :icon="Download" @click="onExport">导出</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增知识</el-button>
        </div>
      </div>

      <!-- 类型分布（点击即筛选） -->
      <div class="type-strip">
        <button class="type-chip" :class="{ active: !query.knowledge_type }" @click="pickType(undefined)">
          全部知识<em>{{ stats.total }}</em>
        </button>
        <button
          v-for="t in options.knowledge_types"
          :key="t"
          class="type-chip"
          :class="{ active: query.knowledge_type === t }"
          @click="pickType(t)"
        >
          {{ t }}<em>{{ stats.by_type[t] || 0 }}</em>
        </button>
      </div>

      <el-table v-loading="loading" :data="rows" class="kb-table" row-key="id">
        <el-table-column label="序号" width="70" align="center">
          <template #default="{ $index }">
            <span class="cell-idx">{{ (query.page - 1) * query.page_size + $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="知识名称" min-width="330">
          <template #default="{ row }">
            <div class="cell-name">
              <b class="title-link" @click="openDetail(row)">{{ row.title }}</b>
              <em class="ntag" :class="typeClass(row.knowledge_type)">{{ row.knowledge_type }}</em>
              <span class="sub">{{ row.summary || '—' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="所属分类" width="150">
          <template #default="{ row }">
            <span class="plain">{{ row.category_name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="来源部门" width="190">
          <template #default="{ row }">
            <span class="plain dept">{{ row.source_dept || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="浏览量" width="96" align="right">
          <template #default="{ row }">
            <span class="cell-num">{{ row.view_count }}</span>
          </template>
        </el-table-column>

        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">
            <span class="cell-time">{{ fmtTime(row.updated_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="96" align="center">
          <template #default="{ row }">
            <em class="ntag" :class="stateClass(row.status)">{{ row.status_label }}</em>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="252" fixed="right">
          <template #default="{ row }">
            <div class="op-gap">
              <el-button class="btn-op btn-op-plain" size="small" :icon="View" @click="openDetail(row)">查看</el-button>
              <el-button
                class="btn-op btn-op-sync"
                size="small"
                :icon="Edit"
                :disabled="!canManage(row)"
                @click="openEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                class="btn-op"
                :class="row.status === 1 ? 'btn-op-off' : 'btn-op-play'"
                size="small"
                :icon="row.status === 1 ? Bottom : Promotion"
                :disabled="!canManage(row)"
                @click="onToggleStatus(row)"
              >
                {{ row.status === 1 ? '下架' : '发布' }}
              </el-button>
              <el-button
                class="btn-op btn-op-del"
                size="small"
                :icon="Delete"
                :disabled="!isAdmin"
                @click="onDelete(row)"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty-box">
        <el-icon><Files /></el-icon>
        <div>未检索到符合条件的知识</div>
      </div>

      <div class="pager">
        <span class="pager-info">共 {{ total }} 条记录，每页 {{ query.page_size }} 条</span>
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.page_size"
          layout="prev, pager, next"
          :total="total"
          @current-change="load"
        />
      </div>
    </section>

    <!-- 知识详情抽屉 -->
    <el-drawer v-model="detail.visible" size="760px" :with-header="false" class="kb-drawer">
      <div v-loading="detail.loading" class="detail-wrap">
        <div class="detail-head">
          <div class="detail-tags">
            <em class="ntag" :class="typeClass(detail.data?.knowledge_type || '')">{{ detail.data?.knowledge_type }}</em>
            <em class="ntag" :class="stateClass(detail.data?.status ?? 1)">{{ detail.data?.status_label }}</em>
            <span class="detail-cat">{{ detail.data?.category_name }}</span>
          </div>
          <h3>{{ detail.data?.title }}</h3>
          <p class="detail-dept">
            来源部门：{{ detail.data?.source_dept || '—' }}　|　关键词：{{ detail.data?.keywords || '—' }}
          </p>
        </div>

        <div class="meta-grid">
          <div><span>发布时间</span><b>{{ fmtTime(detail.data?.publish_at) || '未发布' }}</b></div>
          <div><span>更新时间</span><b>{{ fmtTime(detail.data?.updated_at) }}</b></div>
          <div><span>浏览量</span><b>{{ detail.data?.view_count ?? 0 }}</b></div>
          <div><span>知识编号</span><b>KB-{{ String(detail.data?.id ?? 0).padStart(5, '0') }}</b></div>
        </div>

        <blockquote v-if="detail.data?.summary" class="summary-box">{{ detail.data?.summary }}</blockquote>

        <div class="detail-content" v-html="detail.data?.content || '<p class=&quot;muted&quot;>暂无正文内容</p>'" />

        <div v-if="detail.data?.tags?.length" class="tag-row">
          <span class="tag-label">知识标签</span>
          <em v-for="t in detail.data.tags" :key="t.id" class="tag-item">{{ t.name }}</em>
        </div>

        <div class="drawer-foot">
          <el-button @click="detail.visible = false">关闭</el-button>
          <el-button v-if="detail.data && canManage(detail.data)" type="primary" :icon="Edit" @click="openEdit(detail.data)">
            编辑该知识
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.title"
      width="860px"
      top="6vh"
      destroy-on-close
      @closed="onDialogClosed"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="知识标题" prop="title">
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="如：企业开办“一件事”集成办理知识" />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="知识类型" prop="knowledge_type" class="row-item">
            <el-select v-model="form.knowledge_type" style="width: 100%">
              <el-option v-for="t in options.knowledge_types" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属分类" prop="category_id" class="row-item">
            <el-tree-select
              v-model="form.category_id"
              :data="categoryTree"
              check-strictly
              placeholder="请选择分类"
              style="width: 100%"
            />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="来源部门" class="row-item">
            <el-input v-model="form.source_dept" maxlength="100" placeholder="如：省政务服务和数据管理局" />
          </el-form-item>
          <el-form-item label="关键词" class="row-item">
            <el-input v-model="form.keywords" maxlength="255" placeholder="英文逗号分隔，如：一件事,企业开办" />
          </el-form-item>
        </div>
        <el-form-item label="知识摘要">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="2"
            maxlength="500"
            show-word-limit
            placeholder="一句话概括知识要点，列表与门户检索结果展示"
          />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">已发布（同步至知识门户）</el-radio>
            <el-radio :value="0">草稿（仅管理端可见）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="知识正文">
          <div class="editor-wrap">
            <Toolbar class="editor-toolbar" :editor="editorRef" :default-config="toolbarConfig" />
            <Editor
              v-model="form.content"
              class="editor-content"
              :default-config="editorConfig"
              @on-created="onEditorCreated"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Collection,
  CircleCheck,
  Clock,
  TrendCharts,
  Reading,
  Search,
  RefreshLeft,
  Download,
  Plus,
  Edit,
  Delete,
  View,
  Files,
  Promotion,
  Bottom,
} from '@element-plus/icons-vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import '@wangeditor/editor/dist/css/style.css'
import type { IDomEditor } from '@wangeditor/editor'

import {
  getKnowledgeOptions,
  getKnowledgeStats,
  listKnowledge,
  getKnowledge,
  createKnowledge,
  updateKnowledge,
  changeKnowledgeStatus,
  deleteKnowledge,
  exportKnowledge,
  type KnowledgeItem,
  type KnowledgeDetail,
  type KnowledgeStats,
  type KnowledgeOptions,
  type CategoryOption,
} from '@/api/knowledge'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const isAdmin = computed(() => store.user?.role_code === 'ADMIN')
function canManage(row: { author_id: number }): boolean {
  return isAdmin.value || row.author_id === store.user?.id
}

const loading = ref(false)
const rows = ref<KnowledgeItem[]>([])
const total = ref(0)
const updatedAt = ref('')

const stats = reactive<KnowledgeStats>({
  total: 0,
  published: 0,
  draft: 0,
  offline: 0,
  month_new: 0,
  total_views: 0,
  by_type: {},
  by_dept: {},
})
const options = reactive<KnowledgeOptions>({ knowledge_types: [], statuses: {}, categories: [] })

const query = reactive({
  keyword: '',
  knowledge_type: undefined as string | undefined,
  category_id: undefined as number | undefined,
  status: undefined as number | undefined,
  page: 1,
  page_size: 10,
})

// 分类扁平列表 → 树（path 形如 20/21，父路径用于挂载）
interface TreeNode {
  value: number
  label: string
  children: TreeNode[]
}
const categoryTree = computed<TreeNode[]>(() => {
  const sorted: CategoryOption[] = [...options.categories].sort((a, b) => a.level - b.level)
  const byPath = new Map<string, TreeNode>()
  const roots: TreeNode[] = []
  for (const c of sorted) {
    const node: TreeNode = { value: c.id, label: c.name, children: [] }
    byPath.set(c.path, node)
    const idx = c.path.lastIndexOf('/')
    const parent = idx > 0 ? byPath.get(c.path.slice(0, idx)) : undefined
    if (parent) parent.children.push(node)
    else roots.push(node)
  }
  return roots
})

const TYPE_CLASS: Record<string, string> = {
  事项知识: 't-blue',
  政策法规: 't-purple',
  一件事知识: 't-green',
  办事指南: 't-orange',
  常见问答: 't-cyan',
  数据标准: 't-rose',
}
function typeClass(t: string): string {
  return TYPE_CLASS[t] ?? 't-blue'
}
function stateClass(s: number): string {
  return s === 1 ? 't-green' : s === 0 ? 't-orange' : 't-gray'
}
function fmtTime(s?: string | null): string {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const [pageData, s] = await Promise.all([
      listKnowledge({
        keyword: query.keyword.trim() || undefined,
        knowledge_type: query.knowledge_type,
        category_id: query.category_id,
        status: query.status,
        page: query.page,
        page_size: query.page_size,
      }),
      getKnowledgeStats(),
    ])
    rows.value = pageData.list
    total.value = pageData.total
    Object.assign(stats, s)
    updatedAt.value = new Date().toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  load()
}

function pickType(t: string | undefined) {
  query.knowledge_type = t
  query.page = 1
  load()
}

function onReset() {
  query.keyword = ''
  query.knowledge_type = undefined
  query.category_id = undefined
  query.status = undefined
  query.page = 1
  load()
  ElMessage.success('筛选条件已重置')
}

async function onExport() {
  await exportKnowledge({ knowledge_type: query.knowledge_type, status: query.status })
  ElMessage.success('已导出知识清单')
}

// ---------- 详情 ----------
const detail = reactive({
  visible: false,
  loading: false,
  data: null as KnowledgeDetail | null,
})

async function openDetail(row: KnowledgeItem) {
  detail.visible = true
  detail.loading = true
  detail.data = null
  try {
    detail.data = await getKnowledge(row.id)
  } finally {
    detail.loading = false
  }
}

// ---------- 弹窗 ----------
const dialog = reactive({ visible: false, saving: false, title: '', id: 0 })
const formRef = ref<FormInstance>()
const form = reactive({
  title: '',
  knowledge_type: '事项知识',
  category_id: undefined as number | undefined,
  source_dept: '',
  keywords: '',
  summary: '',
  content: '',
  status: 1,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入知识标题', trigger: 'blur' }],
  knowledge_type: [{ required: true, message: '请选择知识类型', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择所属分类', trigger: 'change' }],
}

// ---- 富文本 ----
const editorRef = shallowRef<IDomEditor>()
const toolbarConfig = {}
const editorConfig = { placeholder: '按“概述 / 办理要素 / 知识要点”组织正文…' }
function onEditorCreated(editor: IDomEditor) {
  editorRef.value = editor
}
function onDialogClosed() {
  editorRef.value?.destroy()
  editorRef.value = undefined
}
onBeforeUnmount(() => editorRef.value?.destroy())

function openCreate() {
  dialog.id = 0
  dialog.title = '新增知识'
  Object.assign(form, {
    title: '',
    knowledge_type: query.knowledge_type ?? '事项知识',
    category_id: query.category_id,
    source_dept: '',
    keywords: '',
    summary: '',
    content: '',
    status: 1,
  })
  dialog.visible = true
}

async function openEdit(row: KnowledgeItem | KnowledgeDetail) {
  dialog.id = row.id
  dialog.title = '编辑知识'
  const full: KnowledgeDetail = 'content' in row && row.content !== undefined ? row : await getKnowledge(row.id)
  Object.assign(form, {
    title: full.title,
    knowledge_type: full.knowledge_type,
    category_id: full.category_id,
    source_dept: full.source_dept,
    keywords: full.keywords,
    summary: full.summary ?? '',
    content: full.content ?? '',
    status: full.status === 2 ? 0 : full.status,
  })
  dialog.visible = true
}

async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  dialog.saving = true
  try {
    const payload = {
      title: form.title.trim(),
      category_id: form.category_id!,
      knowledge_type: form.knowledge_type,
      source_dept: form.source_dept.trim(),
      keywords: form.keywords.trim(),
      summary: form.summary.trim() || null,
      content: form.content || null,
      status: form.status,
    }
    if (dialog.id) {
      await updateKnowledge(dialog.id, payload)
      ElMessage.success('保存成功')
    } else {
      const created = await createKnowledge(payload)
      ElMessage.success('创建成功')
      query.keyword = created.title
      query.knowledge_type = undefined
      query.category_id = undefined
      query.status = undefined
      query.page = 1
    }
    dialog.visible = false
    await load()
    if (detail.visible) detail.data = await getKnowledge(dialog.id || detail.data!.id)
  } finally {
    dialog.saving = false
  }
}

async function onToggleStatus(row: KnowledgeItem) {
  const toPublish = row.status !== 1
  try {
    await ElMessageBox.confirm(
      toPublish
        ? `确定发布「${row.title}」吗？发布后将同步展示在知识门户。`
        : `确定下架「${row.title}」吗？下架后门户不再展示该知识。`,
      toPublish ? '发布确认' : '下架确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await changeKnowledgeStatus(row.id, toPublish ? 1 : 2)
  ElMessage.success(toPublish ? '已发布' : '已下架')
  await load()
}

async function onDelete(row: KnowledgeItem) {
  try {
    await ElMessageBox.confirm(`确定删除知识「${row.title}」吗？删除后不可恢复。`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  await deleteKnowledge(row.id)
  ElMessage.success('删除成功')
  if (query.keyword.trim() === row.title) query.keyword = ''
  if (rows.value.length === 1 && query.page > 1) query.page -= 1
  await load()
}

onMounted(async () => {
  const opts = await getKnowledgeOptions()
  Object.assign(options, opts)
  await load()
})
</script>

<style scoped>
/* 政务蓝设计令牌（与知识元数据管理页保持一致） */
.kb-page {
  --blue: #1a5fb4;
  --blue-2: #0e4a96;
  --blue-soft: #eaf2fd;
  --blue-line: #cfe0f7;
  --panel-2: #f7f9fc;
  --text: #18222e;
  --text-2: #5b6b7d;
  --text-3: #8b99a8;
  --border: #e3e9f1;
  --border-2: #eef2f7;
  --ok: #1a8a5a;
  --warn: #c17d16;
  --purple: #6350c4;
  --danger: #c9403f;
  margin: -20px;
  padding: 18px 22px 24px;
  min-height: calc(100vh - 60px);
  background: #eef2f7;
  box-sizing: border-box;
  color: var(--text);
}
.crumb {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 10px;
  display: flex;
  gap: 6px;
  align-items: center;
}
.crumb b {
  color: var(--text-2);
  font-weight: 600;
}
.sep {
  color: var(--text-3);
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 14px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.page-head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
  position: relative;
  padding-left: 11px;
}
.page-head h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background: var(--blue);
}
.page-desc {
  margin: 5px 0 0;
  padding-left: 11px;
  font-size: 12.5px;
  color: var(--text-3);
  max-width: 900px;
}
.page-sub {
  font-size: 12px;
  color: var(--text-3);
}

/* 统计条 */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(16, 42, 74, 0.05), 0 6px 18px rgba(16, 42, 74, 0.06);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 13px;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}
.stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(16, 42, 74, 0.13);
  border-color: var(--blue-line);
}
.stat-ico {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  flex: none;
  display: grid;
  place-items: center;
  font-size: 20px;
}
.ico-blue {
  background: var(--blue-soft);
  color: var(--blue);
}
.ico-green {
  background: rgba(26, 138, 90, 0.13);
  color: var(--ok);
}
.ico-purple {
  background: rgba(99, 80, 196, 0.13);
  color: var(--purple);
}
.ico-orange {
  background: rgba(193, 125, 22, 0.14);
  color: var(--warn);
}
.stat-txt {
  margin: 0;
  min-width: 0;
}
.stat-txt dt {
  font-size: 12px;
  color: var(--text-3);
  white-space: nowrap;
}
.stat-txt dd {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  font-variant-numeric: tabular-nums;
}
.stat-txt dd small {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-3);
  margin-left: 3px;
}

/* 面板 */
.panel {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(16, 42, 74, 0.05), 0 6px 18px rgba(16, 42, 74, 0.06);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 16px;
  border-bottom: 1px solid var(--border-2);
  flex-wrap: wrap;
}
.panel-head h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.4px;
}
.panel-head h3 .el-icon {
  color: var(--blue);
  font-size: 17px;
}
.tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.tool-search {
  width: 240px;
}
.tool-select {
  width: 168px;
}
.tool-select-sm {
  width: 128px;
}
.btn-ghost {
  height: 32px;
}

/* 类型分布 */
.type-strip {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-2);
  flex-wrap: wrap;
}
.type-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 11px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--panel-2);
  color: var(--text-2);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.type-chip em {
  font-style: normal;
  font-size: 11px;
  color: var(--text-3);
  background: #fff;
  border-radius: 8px;
  padding: 0 6px;
  line-height: 16px;
}
.type-chip:hover {
  border-color: var(--blue-line);
  color: var(--blue);
}
.type-chip.active {
  background: var(--blue);
  border-color: var(--blue);
  color: #fff;
  box-shadow: 0 2px 8px rgba(26, 95, 180, 0.25);
}
.type-chip.active em {
  color: var(--blue);
  background: #fff;
}

/* 表格 */
.kb-table {
  width: 100%;
  --el-table-border-color: var(--border-2);
  font-size: 13.5px;
}
.kb-table :deep(th.el-table__cell) {
  background: var(--panel-2) !important;
  color: var(--text-2);
  font-weight: 600;
  font-size: 12.5px;
  letter-spacing: 0.3px;
  height: 44px;
}
.kb-table :deep(td.el-table__cell) {
  padding: 10px 0;
}
.kb-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--panel-2);
}
.cell-idx {
  color: var(--text-3);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.cell-name {
  display: flex;
  align-items: center;
  gap: 9px;
  flex-wrap: wrap;
}
.title-link {
  font-weight: 600;
  letter-spacing: 0.2px;
  color: var(--text);
  cursor: pointer;
  transition: color 0.16s ease;
}
.title-link:hover {
  color: var(--blue);
}
.cell-name .sub {
  width: 100%;
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.plain {
  color: var(--text-2);
  font-size: 13px;
}
.dept {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.cell-num {
  color: var(--text-2);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.cell-time {
  color: var(--text-2);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.ntag {
  font-style: normal;
  font-size: 11px;
  line-height: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 4px;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.t-blue {
  color: var(--blue);
  background: var(--blue-soft);
}
.t-green {
  color: var(--ok);
  background: rgba(26, 138, 90, 0.12);
}
.t-orange {
  color: var(--warn);
  background: rgba(193, 125, 22, 0.13);
}
.t-purple {
  color: var(--purple);
  background: rgba(99, 80, 196, 0.12);
}
.t-cyan {
  color: #0f7f8c;
  background: rgba(15, 127, 140, 0.12);
}
.t-rose {
  color: #b8437a;
  background: rgba(184, 67, 122, 0.12);
}
.t-gray {
  color: var(--text-3);
  background: var(--panel-2);
  border: 1px solid var(--border);
}
.op-gap {
  display: flex;
  gap: 6px;
  align-items: center;
}
.btn-op {
  height: 30px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 500;
  padding: 0 9px;
}
.btn-op-plain {
  background: #fff;
  color: var(--text-2);
  border-color: var(--border);
}
.btn-op-plain:hover {
  color: var(--blue);
  border-color: var(--blue-line);
  background: var(--blue-soft);
}
.btn-op-sync {
  background: var(--blue-soft);
  color: var(--blue);
  border-color: var(--blue-line);
}
.btn-op-sync:hover {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
}
.btn-op-play {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
  box-shadow: 0 2px 6px rgba(26, 95, 180, 0.2);
}
.btn-op-play:hover {
  background: var(--blue-2);
  color: #fff;
}
.btn-op-off {
  background: #fff;
  color: var(--warn);
  border-color: rgba(193, 125, 22, 0.35);
}
.btn-op-off:hover {
  background: var(--warn);
  color: #fff;
}
.btn-op-del {
  background: #fff;
  color: var(--danger);
  border-color: rgba(201, 64, 63, 0.35);
  width: 30px;
  padding: 0;
}
.btn-op-del:hover {
  background: var(--danger);
  color: #fff;
}

.empty-box {
  padding: 52px 16px;
  text-align: center;
  color: var(--text-3);
  font-size: 13px;
}
.empty-box .el-icon {
  font-size: 34px;
  color: var(--border);
  margin-bottom: 8px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-2);
  flex-wrap: wrap;
}
.pager-info {
  font-size: 12.5px;
  color: var(--text-3);
}

/* 详情抽屉 */
.detail-wrap {
  padding: 4px 2px 8px;
  min-height: 320px;
}
.detail-head {
  border-bottom: 1px solid var(--border-2);
  padding-bottom: 12px;
}
.detail-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}
.detail-cat {
  font-size: 12px;
  color: var(--text-3);
}
.detail-head h3 {
  margin: 10px 0 6px;
  font-size: 18px;
  line-height: 1.45;
  font-weight: 700;
  color: var(--text);
}
.detail-dept {
  margin: 0;
  font-size: 12.5px;
  color: var(--text-3);
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
  padding: 12px 14px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.meta-grid div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meta-grid span {
  font-size: 11.5px;
  color: var(--text-3);
}
.meta-grid b {
  font-size: 13px;
  color: var(--text);
  font-weight: 600;
}
.summary-box {
  margin: 0 0 14px;
  padding: 10px 14px;
  border-left: 3px solid var(--blue);
  background: var(--blue-soft);
  border-radius: 0 8px 8px 0;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.75;
}
.detail-content {
  font-size: 13.5px;
  line-height: 1.85;
  color: var(--text);
}
.detail-content :deep(h3) {
  font-size: 14px;
  margin: 16px 0 6px;
  padding-left: 9px;
  position: relative;
  color: var(--text);
}
.detail-content :deep(h3)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 13px;
  border-radius: 2px;
  background: var(--blue);
}
.detail-content :deep(p) {
  margin: 6px 0;
  color: var(--text-2);
}
.detail-content :deep(ul),
.detail-content :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
  color: var(--text-2);
}
.detail-content :deep(li) {
  margin: 3px 0;
}
.detail-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}
.detail-content :deep(th),
.detail-content :deep(td) {
  border: 1px solid var(--border);
  padding: 6px 10px;
  font-size: 12.5px;
}
.detail-content :deep(.muted) {
  color: var(--text-3);
}
.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
}
.tag-label {
  font-size: 12px;
  color: var(--text-3);
}
.tag-item {
  font-style: normal;
  font-size: 11.5px;
  padding: 2px 9px;
  border-radius: 10px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  color: var(--text-2);
}
.drawer-foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
  padding-top: 14px;
  border-top: 1px solid var(--border-2);
}

/* 弹窗表单 */
.form-row {
  display: flex;
  gap: 12px;
}
.row-item {
  flex: 1;
}
.editor-wrap {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  z-index: 1;
}
.editor-toolbar {
  border-bottom: 1px solid var(--border);
}
.editor-content {
  height: 260px;
  overflow-y: auto;
}

@media (max-width: 1400px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 900px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
  .tool-search,
  .tool-select,
  .tool-select-sm {
    width: 100%;
  }
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
