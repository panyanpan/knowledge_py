<template>
  <div class="svc-page">
    <div class="crumb">
      <span>知识管理</span>
      <span class="sep">›</span>
      <b>知识服务市场</b>
    </div>

    <div class="page-head">
      <div>
        <h2>知识服务市场</h2>
        <p class="page-desc">
          汇聚平台上可供各部门调用的知识服务能力，按部门授权后即可申请接入，支持接口文档查阅与服务全生命周期管理。
        </p>
      </div>
      <span class="page-sub">数据更新于 {{ updatedAt }}</span>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3><el-icon><Goods /></el-icon>知识服务市场</h3>
        <div class="tools">
          <span class="head-tip">
            已上架 <b class="num">{{ stats.online }}</b> 项服务 · 本月新增 <b class="num">{{ stats.month_new }}</b> 项 · 按部门授权后可申请调用
          </span>
          <el-input
            v-model="query.keyword"
            class="tool-search"
            placeholder="搜索服务名称 / 编码 / 部门"
            clearable
            :prefix-icon="Search"
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-select v-model="query.svc_type" class="tool-select" placeholder="全部服务类型" clearable @change="onSearch">
            <el-option v-for="t in options.svc_types" :key="t" :label="t" :value="t" />
          </el-select>
          <el-select v-model="query.status" class="tool-select" placeholder="全部状态" clearable @change="onSearch">
            <el-option v-for="s in options.statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
          <el-button class="btn-ghost" :icon="RefreshLeft" @click="onReset">重置</el-button>
          <el-button type="primary" :icon="Plus" :disabled="!isAdmin" @click="openCreate">新增服务</el-button>
        </div>
      </div>

      <div class="panel-body pad">
        <div v-loading="loading" class="svc-grid">
          <article v-for="row in rows" :key="row.id" class="svc-card" :class="{ offline: row.status === 0 }">
            <div class="sc-top">
              <span class="sc-ico" :class="typeIcoClass(row.svc_type)">
                <el-icon><component :is="typeIcon(row.svc_type)" /></el-icon>
              </span>
              <div class="sc-title">
                <b>{{ row.svc_name }}</b>
                <span>{{ row.provider_dept || '—' }}</span>
              </div>
              <em class="ntag" :class="typeTagClass(row.svc_type)">{{ row.svc_type }}</em>
            </div>
            <p class="sc-desc">{{ row.description || '—' }}</p>
            <div class="sc-tags">
              <span v-for="t in tagList(row.tags)" :key="t">{{ t }}</span>
            </div>
            <dl class="sc-meta">
              <div><dt>累计调用</dt><dd class="num">{{ row.call_count.toLocaleString() }}</dd></div>
              <div><dt>接口数</dt><dd class="num">{{ row.api_count }}</dd></div>
              <div><dt>更新</dt><dd class="num">{{ fmtDate(row.updated_at) }}</dd></div>
            </dl>
            <div class="sc-foot">
              <el-button type="primary" class="btn-flex" :icon="Pointer" :disabled="row.status !== 1" @click="openApply(row)">
                申请调用
              </el-button>
              <el-button class="btn-ghost btn-flex" :icon="Document" @click="openDoc(row)">接口文档</el-button>
            </div>
            <div v-if="isAdmin" class="sc-admin">
              <el-button
                link
                :type="row.status === 1 ? 'warning' : 'success'"
                :icon="row.status === 1 ? SortDown : SortUp"
                @click="onToggle(row)"
              >
                {{ row.status === 1 ? '下架' : '上架' }}
              </el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
              <span class="sc-state" :class="row.status === 1 ? 'ok' : 'off'">
                {{ row.status === 1 ? '已上架' : '已下架' }}
              </span>
            </div>
          </article>
        </div>

        <div v-if="!loading && !rows.length" class="empty-box">
          <el-icon><Files /></el-icon>
          <div>没有符合条件的服务，请调整检索条件</div>
        </div>

        <div class="pager">
          <span class="pager-info">共 {{ total }} 项服务 · 每页 {{ query.page_size }} 项</span>
          <el-pagination
            v-model:current-page="query.page"
            :page-size="query.page_size"
            layout="prev, pager, next"
            :total="total"
            @current-change="load"
          />
        </div>
      </div>
    </section>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="620px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px">
        <el-form-item label="服务名称" prop="svc_name">
          <el-input v-model="form.svc_name" maxlength="100" placeholder="如：政策法规智能问答服务" />
        </el-form-item>
        <el-form-item label="提供部门">
          <el-input v-model="form.provider_dept" maxlength="100" placeholder="如：市教育局 · 政策法规处" />
        </el-form-item>
        <el-form-item v-if="!dialog.id" label="服务编码">
          <el-input v-model="form.svc_code" placeholder="留空则自动生成，如 SVC-007" />
        </el-form-item>
        <el-form-item v-else label="服务编码">
          <el-input :model-value="dialog.code" disabled />
        </el-form-item>
        <el-form-item label="服务类型" prop="svc_type">
          <el-select v-model="form.svc_type" style="width: 100%">
            <el-option v-for="t in options.svc_types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="说明服务能力、适用场景与调用方式"
          />
        </el-form-item>
        <el-form-item label="能力标签">
          <el-input v-model="form.tags" maxlength="300" placeholder="多个标签用英文逗号分隔，如 QPS 50,返回条款原文,按部门授权" />
        </el-form-item>
        <el-form-item label="接口数">
          <el-input-number v-model="form.api_count" :min="0" :max="999" controls-position="right" />
        </el-form-item>
        <el-form-item label="文档版本">
          <el-input v-model="form.doc_version" maxlength="20" placeholder="如 v2.4" />
        </el-form-item>
        <el-form-item label="文档地址">
          <el-input v-model="form.doc_url" maxlength="300" placeholder="接口文档在线地址（预留，可留空）" />
        </el-form-item>
        <el-form-item v-if="dialog.id" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">已上架</el-radio>
            <el-radio :value="0">已下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="foot-left">
          <el-button v-if="dialog.id && form.status !== 1" class="btn-del" :icon="Delete" @click="onDelete">删除服务</el-button>
        </span>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 申请调用弹窗 -->
    <el-dialog v-model="applyDialog.visible" title="申请调用" width="520px" destroy-on-close>
      <div class="apply-svc">
        <span class="sc-ico" :class="typeIcoClass(applyDialog.svcType)"><el-icon><component :is="typeIcon(applyDialog.svcType)" /></el-icon></span>
        <div class="apply-svc-txt">
          <b>{{ applyDialog.svcName }}</b>
          <span>{{ applyDialog.svcCode }} · {{ applyDialog.providerDept }}</span>
        </div>
        <em class="ntag" :class="typeTagClass(applyDialog.svcType)">{{ applyDialog.svcType }}</em>
      </div>
      <el-form ref="applyFormRef" :model="applyForm" :rules="applyRules" label-width="96px">
        <el-form-item label="申请部门" prop="apply_dept">
          <el-input v-model="applyForm.apply_dept" maxlength="100" placeholder="如：某区政务服务中心" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="applyForm.contact" maxlength="50" placeholder="姓名 / 联系方式" />
        </el-form-item>
        <el-form-item label="申请用途">
          <el-input v-model="applyForm.reason" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="说明调用场景与数据范围" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="applyDialog.saving" @click="onApply">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- 接口文档抽屉（演示内容，待后续对接） -->
    <el-drawer v-model="docDrawer.visible" :title="`接口文档 · ${docDrawer.svcName}`" size="460px">
      <div class="doc-head">
        <em class="ntag" :class="typeTagClass(docDrawer.svcType)">{{ docDrawer.svcType }}</em>
        <code class="code">{{ docDrawer.svcCode }}</code>
        <span class="doc-ver">{{ docDrawer.docVersion || '未登记版本' }}</span>
      </div>
      <div class="doc-note">
        <el-icon><InfoFilled /></el-icon>
        以下为演示内容，正式接口文档将在 API 对接后自动关联展示。
      </div>
      <h4 class="doc-sec">接口清单（{{ docDrawer.apiCount }} 个）</h4>
      <ul class="doc-list">
        <li v-for="(it, i) in docDrawer.apis" :key="i">
          <code class="code">{{ it.method }}</code>
          <div class="doc-api">
            <b>{{ it.name }}</b>
            <span>{{ it.path }}</span>
          </div>
        </li>
      </ul>
      <h4 class="doc-sec">接入说明</h4>
      <ol class="doc-steps">
        <li>按部门提交调用申请，经服务提供方与数据资源处审批；</li>
        <li>审批通过后分配应用凭证（AppKey / AppSecret）；</li>
        <li>通过网关统一接入，调用计量与配额按月出账。</li>
      </ol>
      <div class="doc-foot-tip">文档版本 {{ docDrawer.docVersion || '—' }} · 更新于 {{ docDrawer.updatedAt }}</div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import type { Component } from 'vue'
import {
  Goods,
  Search,
  RefreshLeft,
  Plus,
  Edit,
  Delete,
  Pointer,
  Document,
  SortUp,
  SortDown,
  Files,
  InfoFilled,
  Share,
  DataAnalysis,
  Bell,
  Upload,
  Refresh,
} from '@element-plus/icons-vue'
import {
  getServiceOptions,
  getServiceStats,
  listServices,
  createService,
  updateService,
  deleteService,
  toggleService,
  applyService,
  type KbService,
  type ServiceOptions,
  type ServiceStats,
  type ServicePayload,
  type ServiceApplyResult,
} from '@/api/svcs'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const isAdmin = computed(() => store.user?.role_code === 'ADMIN')

const loading = ref(false)
const rows = ref<KbService[]>([])
const total = ref(0)
const updatedAt = ref('')

const options = reactive<ServiceOptions>({ svc_types: [], statuses: [] })
const stats = reactive<ServiceStats>({ total: 0, online: 0, month_new: 0, total_calls: 0, by_type: {} })

const query = reactive({
  keyword: '',
  svc_type: undefined as string | undefined,
  status: undefined as number | undefined,
  page: 1,
  page_size: 12,
})

// 类型 → 图标 / 配色
const TYPE_ICONS: Record<string, Component> = {
  API: markRaw(Document),
  图谱: markRaw(Share),
  匹配: markRaw(DataAnalysis),
  订阅: markRaw(Bell),
  工具: markRaw(Upload),
  交换: markRaw(Refresh),
}
function typeIcon(t: string): Component {
  return TYPE_ICONS[t] ?? Document
}
function typeIcoClass(t: string): string {
  return t === '图谱' || t === '交换' ? 'ico-purple' : t === '匹配' ? 'ico-orange' : t === '订阅' ? 'ico-green' : 'ico-blue'
}
function typeTagClass(t: string): string {
  return t === '图谱' || t === '交换' ? 't-purple' : t === '匹配' ? 't-orange' : t === '订阅' ? 't-green' : 't-blue'
}

function tagList(tags: string | null): string[] {
  return (tags || '').split(',').map((s) => s.trim()).filter(Boolean)
}
function fmtDate(s: string | null): string {
  return s ? s.replace('T', ' ').slice(5, 10) : '—'
}

async function load() {
  loading.value = true
  try {
    const [page, s] = await Promise.all([
      listServices({
        keyword: query.keyword.trim() || undefined,
        svc_type: query.svc_type,
        status: query.status,
        page: query.page,
        page_size: query.page_size,
      }),
      getServiceStats(),
    ])
    rows.value = page.list
    total.value = page.total
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

function onReset() {
  query.keyword = ''
  query.svc_type = undefined
  query.status = undefined
  query.page = 1
  load()
  ElMessage.success('筛选条件已重置')
}

// ---------- 新增 / 编辑 ----------
const dialog = reactive({ visible: false, saving: false, title: '', id: 0, code: '' })
const formRef = ref<FormInstance>()
const form = reactive({
  svc_name: '',
  provider_dept: '',
  svc_code: '',
  svc_type: 'API',
  description: '',
  tags: '',
  api_count: 1,
  doc_version: '',
  doc_url: '',
  status: 1,
})

const formRules: FormRules = {
  svc_name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
  svc_type: [{ required: true, message: '请选择服务类型', trigger: 'change' }],
}

function openCreate() {
  dialog.id = 0
  dialog.title = '新增服务'
  dialog.code = ''
  Object.assign(form, {
    svc_name: '',
    provider_dept: '',
    svc_code: '',
    svc_type: 'API',
    description: '',
    tags: '',
    api_count: 1,
    doc_version: '',
    doc_url: '',
    status: 1,
  })
  dialog.visible = true
}

function openEdit(row: KbService) {
  dialog.id = row.id
  dialog.title = '编辑服务'
  dialog.code = row.svc_code
  Object.assign(form, {
    svc_name: row.svc_name,
    provider_dept: row.provider_dept ?? '',
    svc_code: row.svc_code,
    svc_type: row.svc_type,
    description: row.description ?? '',
    tags: row.tags ?? '',
    api_count: row.api_count,
    doc_version: row.doc_version ?? '',
    doc_url: row.doc_url ?? '',
    status: row.status,
  })
  dialog.visible = true
}

async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  dialog.saving = true
  try {
    if (dialog.id) {
      const payload: Partial<ServicePayload> = {
        svc_name: form.svc_name.trim(),
        provider_dept: form.provider_dept || null,
        svc_type: form.svc_type,
        description: form.description || null,
        tags: form.tags || null,
        api_count: form.api_count,
        doc_version: form.doc_version || null,
        doc_url: form.doc_url || null,
        status: form.status,
      }
      await updateService(dialog.id, payload)
      ElMessage.success('更新成功')
    } else {
      const payload: ServicePayload = {
        svc_code: form.svc_code.trim() || null,
        svc_name: form.svc_name.trim(),
        provider_dept: form.provider_dept || null,
        svc_type: form.svc_type,
        description: form.description || null,
        tags: form.tags || null,
        api_count: form.api_count,
        doc_version: form.doc_version || null,
        doc_url: form.doc_url || null,
      }
      const created = await createService(payload)
      ElMessage.success(`创建成功，服务编码 ${created.svc_code}`)
      query.keyword = created.svc_code
      query.svc_type = undefined
      query.status = undefined
      query.page = 1
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete() {
  try {
    await ElMessageBox.confirm(
      `确定删除服务「${form.svc_name}」（${dialog.code}）吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteService(dialog.id)
  ElMessage.success('删除成功')
  dialog.visible = false
  if (query.keyword.trim() === dialog.code) query.keyword = ''
  if (rows.value.length === 1 && query.page > 1) query.page -= 1
  await load()
}

// ---------- 上下架 ----------
async function onToggle(row: KbService) {
  const toOffline = row.status === 1
  try {
    await ElMessageBox.confirm(
      toOffline
        ? `确定下架服务「${row.svc_name}」吗？下架后各部门将无法申请调用。`
        : `确定上架服务「${row.svc_name}」吗？上架后立即进入服务市场可申请列表。`,
      '状态变更确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  const updated = await toggleService(row.id)
  row.status = updated.status
  ElMessage.success(`服务已${updated.status === 1 ? '上架' : '下架'}`)
}

// ---------- 申请调用 ----------
const applyDialog = reactive({
  visible: false,
  saving: false,
  serviceId: 0,
  svcName: '',
  svcCode: '',
  svcType: '',
  providerDept: '',
})
const applyFormRef = ref<FormInstance>()
const applyForm = reactive({ apply_dept: '', contact: '', reason: '' })
const applyRules: FormRules = {
  apply_dept: [{ required: true, message: '请输入申请部门', trigger: 'blur' }],
}

function openApply(row: KbService) {
  applyDialog.serviceId = row.id
  applyDialog.svcName = row.svc_name
  applyDialog.svcCode = row.svc_code
  applyDialog.svcType = row.svc_type
  applyDialog.providerDept = row.provider_dept ?? ''
  Object.assign(applyForm, { apply_dept: '', contact: '', reason: '' })
  applyDialog.visible = true
}

async function onApply() {
  const valid = await applyFormRef.value?.validate().catch(() => false)
  if (!valid) return
  applyDialog.saving = true
  try {
    const res: ServiceApplyResult = await applyService({
      service_id: applyDialog.serviceId,
      apply_dept: applyForm.apply_dept.trim(),
      contact: applyForm.contact || null,
      reason: applyForm.reason || null,
    })
    applyDialog.visible = false
    ElMessageBox.alert(
      `${res.message}`,
      '申请已受理',
      { confirmButtonText: '知道了', type: 'success' },
    )
  } finally {
    applyDialog.saving = false
  }
}

// ---------- 接口文档抽屉（演示内容） ----------
const docDrawer = reactive({
  visible: false,
  svcName: '',
  svcCode: '',
  svcType: '',
  docVersion: '',
  apiCount: 0,
  updatedAt: '',
  apis: [] as { method: string; name: string; path: string }[],
})

function openDoc(row: KbService) {
  docDrawer.svcName = row.svc_name
  docDrawer.svcCode = row.svc_code
  docDrawer.svcType = row.svc_type
  docDrawer.docVersion = row.doc_version ?? ''
  docDrawer.apiCount = row.api_count
  docDrawer.updatedAt = fmtDate(row.updated_at)
  // 演示接口清单：按接口数生成占位，待 API 对接后替换
  const methods = ['POST', 'GET', 'POST', 'GET', 'POST', 'GET']
  const names = ['检索查询', '详情获取', '提交计算', '结果轮询', '批量处理', '状态回执']
  docDrawer.apis = Array.from({ length: Math.max(row.api_count, 1) }, (_, i) => ({
    method: methods[i % methods.length],
    name: `${names[i % names.length]}接口 ${i + 1}`,
    path: `/api/v1/svc/${row.svc_code.toLowerCase()}/endpoint-${i + 1}`,
  }))
  docDrawer.visible = true
}

onMounted(async () => {
  const opts = await getServiceOptions()
  Object.assign(options, opts)
  await load()
})
</script>

<style scoped>
/* 政务蓝设计令牌（对齐元数据/知识/规则管理页） */
.svc-page {
  --blue: #1a5fb4;
  --blue-2: #0e4a96;
  --blue-soft: #eaf2fd;
  --blue-line: #cfe0f7;
  --panel: #fff;
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
}
.page-sub {
  font-size: 12px;
  color: var(--text-3);
}

/* 面板 */
.panel {
  background: var(--panel);
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
.head-tip {
  font-size: 12.5px;
  color: var(--text-3);
  white-space: nowrap;
}
.head-tip .num {
  color: var(--blue);
  font-weight: 700;
  font-style: normal;
  font-variant-numeric: tabular-nums;
}
.tool-search {
  width: 220px;
}
.tool-select {
  width: 140px;
}
.btn-ghost {
  height: 32px;
}

.panel-body.pad {
  padding: 16px;
}

/* 服务卡片网格（对齐 demo .svc-grid/.svc-card） */
.svc-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.svc-card {
  display: flex;
  flex-direction: column;
  gap: 11px;
  padding: 15px 16px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 9px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}
.svc-card:hover {
  background: var(--panel);
  border-color: var(--blue-line);
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(16, 42, 74, 0.13);
}
.svc-card.offline {
  opacity: 0.72;
}
.sc-top {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.sc-ico {
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 9px;
  display: grid;
  place-items: center;
  font-size: 19px;
}
.ico-blue {
  background: var(--blue-soft);
  color: var(--blue);
}
.ico-purple {
  background: rgba(99, 80, 196, 0.13);
  color: var(--purple);
}
.ico-orange {
  background: rgba(193, 125, 22, 0.14);
  color: var(--warn);
}
.ico-green {
  background: rgba(26, 138, 90, 0.13);
  color: var(--ok);
}
.sc-title {
  flex: 1;
  min-width: 0;
}
.sc-title b {
  display: block;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.45;
}
.sc-title span {
  display: block;
  margin-top: 3px;
  font-size: 11.5px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
.sc-desc {
  flex: 1;
  margin: 0;
  font-size: 12.5px;
  color: var(--text-2);
  line-height: 1.75;
}
.sc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sc-tags span {
  font-size: 11.5px;
  color: var(--text-2);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 3px 7px;
}
.sc-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 8px 10px;
}
.sc-meta dt {
  font-size: 11px;
  color: var(--text-3);
}
.sc-meta dd {
  margin: 2px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}
.sc-foot {
  display: flex;
  gap: 8px;
}
.btn-flex {
  flex: 1;
}
.sc-admin {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 9px;
  border-top: 1px dashed var(--border);
}
.sc-admin .el-button + .el-button {
  margin-left: 0;
}
.sc-state {
  margin-left: auto;
  font-size: 11.5px;
}
.sc-state.ok {
  color: var(--ok);
}
.sc-state.off {
  color: var(--warn);
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
  padding: 14px 0 0;
  flex-wrap: wrap;
}
.pager-info {
  font-size: 12.5px;
  color: var(--text-3);
}

/* 弹窗 / 抽屉 */
.foot-left {
  float: left;
}
.btn-del {
  color: var(--danger);
  border-color: rgba(201, 64, 63, 0.35);
}
.btn-del:hover {
  background: var(--danger);
  color: #fff;
  border-color: var(--danger);
}
.apply-svc {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
}
.apply-svc-txt {
  flex: 1;
  min-width: 0;
}
.apply-svc-txt b {
  display: block;
  font-size: 13.5px;
}
.apply-svc-txt span {
  display: block;
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--text-3);
}
.code {
  font-family: Consolas, 'SFMono-Regular', Menlo, monospace;
  font-size: 12px;
  color: var(--text-2);
  background: var(--panel-2);
  border: 1px solid var(--border);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}
.doc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.doc-ver {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-3);
}
.doc-note {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: var(--warn);
  background: rgba(193, 125, 22, 0.08);
  border: 1px dashed rgba(193, 125, 22, 0.35);
  border-radius: 6px;
  padding: 8px 10px;
  line-height: 1.6;
}
.doc-note .el-icon {
  margin-top: 2px;
}
.doc-sec {
  margin: 16px 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
.doc-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.doc-list li {
  display: flex;
  align-items: flex-start;
  gap: 9px;
}
.doc-api b {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
}
.doc-api span {
  display: block;
  margin-top: 1px;
  font-size: 11.5px;
  color: var(--text-3);
  font-family: Consolas, 'SFMono-Regular', Menlo, monospace;
  word-break: break-all;
}
.doc-steps {
  margin: 0;
  padding-left: 18px;
  font-size: 12.5px;
  color: var(--text-2);
  line-height: 2;
}
.doc-foot-tip {
  margin-top: 18px;
  padding-top: 10px;
  border-top: 1px solid var(--border-2);
  font-size: 11.5px;
  color: var(--text-3);
}

@media (max-width: 1200px) {
  .svc-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .tool-search,
  .tool-select {
    width: 100%;
  }
}
@media (max-width: 900px) {
  .svc-grid {
    grid-template-columns: 1fr;
  }
}
</style>
