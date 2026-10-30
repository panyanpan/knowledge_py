<template>
  <div class="rule-page">
    <div class="crumb">
      <span>知识管理</span>
      <span class="sep">›</span>
      <b>知识规则管理</b>
    </div>

    <div class="page-head">
      <div>
        <h2>知识规则管理</h2>
        <p class="page-desc">
          维护知识质量规则的判定条件与适用范围，支持试运行验证规则效果，保障知识入库、更新与发布全流程的合规性。
        </p>
      </div>
      <span class="page-sub">数据更新于 {{ updatedAt }}</span>
    </div>

    <!-- 规则清单 -->
    <section class="panel">
      <div class="panel-head">
        <h3><el-icon><Setting /></el-icon>规则清单</h3>
        <div class="tools">
          <el-input
            v-model="query.keyword"
            class="tool-search"
            placeholder="搜索规则名称 / 编码"
            clearable
            :prefix-icon="Search"
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-select v-model="query.rule_type" class="tool-select" placeholder="全部规则类型" clearable @change="onSearch">
            <el-option v-for="t in options.rule_types" :key="t" :label="t" :value="t" />
          </el-select>
          <el-select v-model="query.status" class="tool-select" placeholder="全部状态" clearable @change="onSearch">
            <el-option v-for="s in options.statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
          <el-button class="btn-ghost" :icon="RefreshLeft" @click="onReset">重置</el-button>
          <el-button type="primary" :icon="Plus" :disabled="!isAdmin" @click="openCreate">新增规则</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" class="rule-table" row-key="id">
        <el-table-column label="序号" width="64" align="center">
          <template #default="{ $index }">
            <span class="cell-idx">{{ (query.page - 1) * query.page_size + $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="规则名称" min-width="230">
          <template #default="{ row }">
            <div class="cell-name">
              <b>{{ row.rule_name }}</b>
              <span class="sub">{{ row.description || '—' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="规则编码" width="96">
          <template #default="{ row }">
            <code class="code">{{ row.rule_code }}</code>
          </template>
        </el-table-column>

        <el-table-column label="规则类型" width="100">
          <template #default="{ row }">
            <em class="ntag" :class="typeClass(row.rule_type)">{{ row.rule_type }}</em>
          </template>
        </el-table-column>

        <el-table-column label="适用范围" min-width="130">
          <template #default="{ row }">
            <span class="plain">{{ row.scope_text || '全量知识' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="判定条件" min-width="250">
          <template #default="{ row }">
            <span class="cond-txt">{{ row.condition_text || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="本轮命中" width="90" align="center">
          <template #default="{ row }">
            <span class="cell-time" :class="{ 'hit-hot': row.hit_count > 0 }">{{ row.hit_count }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="86" align="center">
          <template #default="{ row }">
            <em class="ntag" :class="statusClass(row.status)">{{ statusLabel(row.status) }}</em>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <div class="op-gap">
              <el-button class="btn-op btn-op-sync" size="small" :icon="VideoPlay" @click="onRun(row)">试运行</el-button>
              <el-button class="btn-op btn-op-sync" size="small" :icon="Edit" :disabled="!isAdmin" @click="openEdit(row)">编辑</el-button>
              <el-button
                class="btn-op btn-op-play"
                size="small"
                :icon="row.status === 1 ? CircleClose : CircleCheck"
                :disabled="!isAdmin"
                @click="onToggle(row)"
              >
                {{ row.status === 1 ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty-box">
        <el-icon><Files /></el-icon>
        <div>没有符合条件的规则，请调整检索条件</div>
      </div>

      <div class="pager">
        <span class="pager-info">共 {{ total }} 条规则 · 每页 {{ query.page_size }} 条</span>
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.page_size"
          layout="prev, pager, next"
          :total="total"
          @current-change="load"
        />
      </div>
    </section>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px">
        <el-form-item label="规则名称" prop="rule_name">
          <el-input v-model="form.rule_name" maxlength="100" placeholder="如：政策时效校验" />
        </el-form-item>
        <el-form-item label="规则说明">
          <el-input v-model="form.description" maxlength="200" placeholder="一句话说明规则用途，展示在规则名称下方" />
        </el-form-item>
        <el-form-item v-if="!dialog.id" label="规则编码">
          <el-input v-model="form.rule_code" placeholder="留空则自动生成，如 R-041" />
        </el-form-item>
        <el-form-item v-else label="规则编码">
          <el-input :model-value="dialog.code" disabled />
        </el-form-item>
        <el-form-item label="规则类型" prop="rule_type">
          <el-select v-model="form.rule_type" style="width: 100%">
            <el-option v-for="t in options.rule_types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用范围">
          <el-input v-model="form.scope_text" maxlength="200" placeholder="如：政策类知识 / 全量知识 / 含附件知识" />
        </el-form-item>
        <el-form-item label="判定条件" prop="condition_text">
          <el-input
            v-model="form.condition_text"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="描述规则的判定逻辑，如：有效期 ≥ 当前日期 + 45 天，且政策依据未废止"
          />
        </el-form-item>
        <el-form-item v-if="dialog.id" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
            <el-radio :value="2">待复核</el-radio>
          </el-radio-group>
        </el-form-item>
        <div v-else class="create-tip">
          <el-icon><InfoFilled /></el-icon>
          新增规则保存后自动进入「待复核」状态，复核通过后方可启用执行。
        </div>
      </el-form>
      <template #footer>
        <span class="foot-left">
          <el-button
            v-if="dialog.id && form.status !== 1"
            class="btn-del"
            :icon="Delete"
            @click="onDelete"
          >
            删除规则
          </el-button>
        </span>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 试运行结果弹窗 -->
    <el-dialog v-model="runDialog.visible" title="规则试运行结果" width="520px">
      <div class="run-head">
        <code class="code">{{ runDialog.rule_code }}</code>
        <b>{{ runDialog.rule_name }}</b>
        <em class="ntag t-blue" style="margin-left: auto">试运行</em>
      </div>
      <div class="run-nums">
        <div class="rn">
          <span class="rn-num">{{ runDialog.scanned }}</span>
          <span class="rn-label">扫描知识（条）</span>
        </div>
        <div class="rn-arrow">→</div>
        <div class="rn">
          <span class="rn-num rn-hot">{{ runDialog.hits }}</span>
          <span class="rn-label">命中待核查（条）</span>
        </div>
      </div>
      <p class="run-msg">
        <el-icon><InfoFilled /></el-icon>
        {{ runDialog.message }}。试运行在只读副本上按当前规则版本判定，不产生整改工单。
      </p>
      <template #footer>
        <el-button type="primary" @click="runDialog.visible = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Setting,
  Search,
  RefreshLeft,
  Plus,
  Edit,
  Delete,
  VideoPlay,
  CircleCheck,
  CircleClose,
  Files,
  InfoFilled,
} from '@element-plus/icons-vue'
import {
  getRuleOptions,
  listRules,
  createRule,
  updateRule,
  deleteRule,
  toggleRule,
  runRule,
  type KbRule,
  type RuleOptions,
  type RulePayload,
  type RuleRunResult,
} from '@/api/rules'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const isAdmin = computed(() => store.user?.role_code === 'ADMIN')

const loading = ref(false)
const rows = ref<KbRule[]>([])
const total = ref(0)
const updatedAt = ref('')

const options = reactive<RuleOptions>({ rule_types: [], statuses: [] })

const query = reactive({
  keyword: '',
  rule_type: undefined as string | undefined,
  status: undefined as number | undefined,
  page: 1,
  page_size: 10,
})

const TYPE_CLASSES: Record<string, string> = {
  时效性: 't-red',
  完整性: 't-orange',
  一致性: 't-blue',
  重复度: 't-purple',
  安全合规: 't-red',
  规范性: 't-purple',
}

function typeClass(t: string): string {
  return TYPE_CLASSES[t] ?? 't-blue'
}
function statusLabel(s: number): string {
  return s === 1 ? '启用' : s === 0 ? '停用' : '待复核'
}
function statusClass(s: number): string {
  return s === 1 ? 't-green' : s === 0 ? 't-orange' : 't-purple'
}

async function load() {
  loading.value = true
  try {
    const page = await listRules({
      keyword: query.keyword.trim() || undefined,
      rule_type: query.rule_type,
      status: query.status,
      page: query.page,
      page_size: query.page_size,
    })
    rows.value = page.list
    total.value = page.total
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
  query.rule_type = undefined
  query.status = undefined
  query.page = 1
  load()
  ElMessage.success('筛选条件已重置')
}

// ---------- 新增 / 编辑 ----------
const dialog = reactive({ visible: false, saving: false, title: '', id: 0, code: '' })
const formRef = ref<FormInstance>()
const form = reactive({
  rule_name: '',
  description: '',
  rule_code: '',
  rule_type: '完整性',
  scope_text: '',
  condition_text: '',
  status: 1,
})

const formRules: FormRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  condition_text: [{ required: true, message: '请输入判定条件', trigger: 'blur' }],
}

function openCreate() {
  dialog.id = 0
  dialog.title = '新增规则'
  dialog.code = ''
  Object.assign(form, {
    rule_name: '',
    description: '',
    rule_code: '',
    rule_type: '完整性',
    scope_text: '全量知识',
    condition_text: '',
    status: 2,
  })
  dialog.visible = true
}

function openEdit(row: KbRule) {
  dialog.id = row.id
  dialog.title = '编辑规则'
  dialog.code = row.rule_code
  Object.assign(form, {
    rule_name: row.rule_name,
    description: row.description ?? '',
    rule_code: row.rule_code,
    rule_type: row.rule_type,
    scope_text: row.scope_text ?? '',
    condition_text: row.condition_text ?? '',
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
      const payload: Partial<RulePayload> = {
        rule_name: form.rule_name.trim(),
        description: form.description || null,
        rule_type: form.rule_type,
        scope_text: form.scope_text || null,
        condition_text: form.condition_text || null,
        status: form.status,
      }
      await updateRule(dialog.id, payload)
      ElMessage.success('更新成功')
    } else {
      const payload: RulePayload = {
        rule_code: form.rule_code.trim() || null,
        rule_name: form.rule_name.trim(),
        description: form.description || null,
        rule_type: form.rule_type,
        scope_text: form.scope_text || null,
        condition_text: form.condition_text || null,
      }
      const created = await createRule(payload)
      ElMessage.success(`创建成功，规则编码 ${created.rule_code} 已进入待复核状态`)
      query.keyword = created.rule_code
      query.rule_type = undefined
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
      `确定删除规则「${form.rule_name}」（${dialog.code}）吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteRule(dialog.id)
  ElMessage.success('删除成功')
  dialog.visible = false
  if (query.keyword.trim() === dialog.code) query.keyword = ''
  if (rows.value.length === 1 && query.page > 1) query.page -= 1
  await load()
}

// ---------- 启停 ----------
async function onToggle(row: KbRule) {
  const toEnable = row.status !== 1
  try {
    await ElMessageBox.confirm(
      toEnable
        ? row.status === 2
          ? `规则「${row.rule_name}」当前为待复核状态，启用视为复核通过，确定启用吗？`
          : `确定启用规则「${row.rule_name}」吗？`
        : `确定停用规则「${row.rule_name}」吗？停用后该规则不再参与知识校验。`,
      '状态变更确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  const updated = await toggleRule(row.id)
  row.status = updated.status
  ElMessage.success(`规则已${updated.status === 1 ? '启用' : '停用'}`)
}

// ---------- 试运行 ----------
const runDialog = reactive<RuleRunResult & { visible: boolean }>({
  visible: false,
  rule_code: '',
  rule_name: '',
  scanned: 0,
  hits: 0,
  ran_at: '',
  message: '',
})

async function onRun(row: KbRule) {
  const res: RuleRunResult = await runRule(row.id)
  Object.assign(runDialog, res, { visible: true })
  // 回写本轮命中数
  row.hit_count = res.hits
  row.last_run_at = res.ran_at
}

onMounted(async () => {
  const opts = await getRuleOptions()
  Object.assign(options, opts)
  await load()
})
</script>

<style scoped>
/* 政务蓝设计令牌（对齐元数据/知识管理页） */
.rule-page {
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
}
.page-sub {
  font-size: 12px;
  color: var(--text-3);
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
  width: 230px;
}
.tool-select {
  width: 150px;
}
.btn-ghost {
  height: 32px;
}

/* 表格 */
.rule-table {
  width: 100%;
  --el-table-border-color: var(--border-2);
  font-size: 13.5px;
}
.rule-table :deep(th.el-table__cell) {
  background: var(--panel-2) !important;
  color: var(--text-2);
  font-weight: 600;
  font-size: 12.5px;
  letter-spacing: 0.3px;
  height: 44px;
}
.rule-table :deep(td.el-table__cell) {
  padding: 10px 0;
}
.rule-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--panel-2);
}
.cell-idx {
  color: var(--text-3);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.cell-name b {
  font-weight: 600;
  letter-spacing: 0.2px;
  color: var(--text);
}
.cell-name .sub {
  display: block;
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
.plain {
  color: var(--text-2);
  font-size: 13px;
}
.cond-txt {
  font-size: 12.5px;
  color: var(--text-2);
  line-height: 1.5;
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
.t-red {
  color: var(--danger);
  background: rgba(201, 64, 63, 0.1);
}
.cell-time {
  color: var(--text-2);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.hit-hot {
  color: var(--danger);
}
.op-gap {
  display: flex;
  gap: 8px;
  align-items: center;
}
.btn-op {
  height: 30px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 500;
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

/* 弹窗内 */
.create-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 0 96px;
  font-size: 12px;
  color: var(--warn);
  background: rgba(193, 125, 22, 0.08);
  border: 1px dashed rgba(193, 125, 22, 0.35);
  border-radius: 6px;
  padding: 7px 10px;
}
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
.run-head {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 14px;
}
.run-head b {
  font-weight: 600;
}
.run-nums {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  margin: 20px 0 14px;
  padding: 18px 12px;
  background: var(--panel-2);
  border-radius: 10px;
}
.rn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.rn-num {
  font-size: 26px;
  font-weight: 700;
  color: var(--blue);
  font-variant-numeric: tabular-nums;
}
.rn-hot {
  color: var(--danger);
}
.rn-label {
  font-size: 12px;
  color: var(--text-3);
}
.rn-arrow {
  font-size: 18px;
  color: var(--text-3);
}
.run-msg {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  font-size: 12.5px;
  color: var(--text-3);
  line-height: 1.7;
}
.run-msg .el-icon {
  margin-top: 3px;
  color: var(--warn);
}

@media (max-width: 1200px) {
  .tool-search,
  .tool-select {
    width: 100%;
  }
}
</style>
