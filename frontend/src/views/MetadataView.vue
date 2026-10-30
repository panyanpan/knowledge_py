<template>
  <div class="md-page">
    <div class="crumb">
      <span>知识管理</span>
      <span class="sep">›</span>
      <b>知识元数据管理</b>
    </div>

    <div class="page-head">
      <div>
        <h2>知识元数据管理</h2>
        <p class="page-desc">
          统一维护知识条目的元数据字段定义、取值规范与校验规则，保障知识在采集、加工、发布各环节的一致性与可溯源性。
        </p>
      </div>
      <span class="page-sub">数据更新于 {{ updatedAt }}</span>
    </div>

    <!-- 统计条 -->
    <section class="stat-row">
      <div class="stat">
        <span class="stat-ico ico-blue"><el-icon><Collection /></el-icon></span>
        <dl class="stat-txt">
          <dt>元数据字段总数</dt>
          <dd>{{ stats.total }}<small>个</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-green"><el-icon><CircleCheck /></el-icon></span>
        <dl class="stat-txt">
          <dt>已启用字段</dt>
          <dd>{{ stats.enabled }}<small>个</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-purple"><el-icon><Star /></el-icon></span>
        <dl class="stat-txt">
          <dt>必填字段</dt>
          <dd>{{ stats.required }}<small>个</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-orange"><el-icon><Warning /></el-icon></span>
        <dl class="stat-txt">
          <dt>待校验字段</dt>
          <dd>{{ stats.pending }}<small>项</small></dd>
        </dl>
      </div>
    </section>

    <!-- 字段清单 -->
    <section class="panel">
      <div class="panel-head">
        <h3><el-icon><Grid /></el-icon>元数据字段清单</h3>
        <div class="tools">
          <el-input
            v-model="query.keyword"
            class="tool-search"
            placeholder="按字段名称 / 字段编码检索"
            clearable
            :prefix-icon="Search"
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-select v-model="query.domain" class="tool-select" placeholder="全部元数据域" clearable @change="onSearch">
            <el-option v-for="d in options.domains" :key="d" :label="d + '属性'" :value="d" />
          </el-select>
          <el-select v-model="query.status" class="tool-select" placeholder="全部状态" clearable @change="onSearch">
            <el-option label="已启用" :value="1" />
            <el-option label="已停用" :value="0" />
          </el-select>
          <el-button class="btn-ghost" :icon="RefreshLeft" @click="onReset">重置</el-button>
          <el-button class="btn-ghost" :icon="Download" @click="onExport">导出</el-button>
          <el-button type="primary" :icon="Plus" :disabled="!isAdmin" @click="openCreate">新增字段</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" class="meta-table" row-key="id">
        <el-table-column label="序号" width="70" align="center">
          <template #default="{ $index }">
            <span class="cell-idx">{{ (query.page - 1) * query.page_size + $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="字段名称" min-width="280">
          <template #default="{ row }">
            <div class="cell-name">
              <b>{{ row.field_name }}</b>
              <em class="ntag" :class="row.status === 1 ? 't-green' : 't-orange'">
                {{ row.status === 1 ? '已启用' : '已停用' }}
              </em>
              <span class="sub">{{ row.description || '—' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="字段编码" width="200">
          <template #default="{ row }">
            <code class="code">{{ row.field_code }}</code>
          </template>
        </el-table-column>

        <el-table-column label="数据类型" width="110">
          <template #default="{ row }">
            <span class="plain">{{ typeLabel(row.data_type) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="所属元数据域" width="130">
          <template #default="{ row }">
            <em class="ntag" :class="domainClass(row.domain)">{{ row.domain }}属性</em>
          </template>
        </el-table-column>

        <el-table-column label="是否必填" width="100" align="center">
          <template #default="{ row }">
            <span class="req" :class="row.is_required === 1 ? 'req-yes' : 'req-no'">
              {{ row.is_required === 1 ? '必填' : '选填' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="校验规则" width="120">
          <template #default="{ row }">
            <span v-if="row.rule_type" class="rule-tag">{{ ruleLabel(row.rule_type) }}</span>
            <span v-else class="rule-none">未配置</span>
          </template>
        </el-table-column>

        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">
            <span class="cell-time">{{ fmtTime(row.updated_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <div class="op-gap">
              <el-button class="btn-op btn-op-sync" size="small" :icon="Edit" :disabled="!isAdmin" @click="openEdit(row)">
                编辑
              </el-button>
              <el-button
                class="btn-op btn-op-play"
                size="small"
                :icon="CircleCheck"
                :loading="checkingId === row.id"
                @click="onCheckRule(row)"
              >
                校验规则
              </el-button>
              <el-button class="btn-op btn-op-del" size="small" :icon="Delete" :disabled="!isAdmin" @click="onDelete(row)" />
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !rows.length" class="empty-box">
        <el-icon><Files /></el-icon>
        <div>未检索到符合条件的元数据字段</div>
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

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="620px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="字段名称" prop="field_name">
          <el-input v-model="form.field_name" maxlength="100" placeholder="如：知识标题" />
        </el-form-item>
        <el-form-item label="字段编码" prop="field_code">
          <el-input
            v-model="form.field_code"
            :disabled="!!dialog.id"
            placeholder="小写字母开头，仅字母/数字/下划线，如 knowledge_title"
          />
        </el-form-item>
        <el-form-item label="数据类型" prop="data_type">
          <el-select v-model="form.data_type" style="width: 100%">
            <el-option v-for="t in options.data_types" :key="t" :label="typeLabel(t)" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="元数据域" prop="domain">
          <el-select v-model="form.domain" style="width: 100%">
            <el-option v-for="d in options.domains" :key="d" :label="d + '属性'" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否必填">
          <el-radio-group v-model="form.is_required">
            <el-radio :value="1">必填</el-radio>
            <el-radio :value="0">选填</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="字段说明">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="用途、取值来源等说明" />
        </el-form-item>
        <el-form-item label="校验规则">
          <el-select v-model="form.rule_type" style="width: 100%" @change="onRuleTypeChange">
            <el-option label="不配置" value="none" />
            <el-option label="长度区间（length）" value="length" />
            <el-option label="正则匹配（regex）" value="regex" />
            <el-option label="枚举取值（enum）" value="enum" />
            <el-option label="数值区间（range）" value="range" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="form.rule_type === 'length'" label="长度区间">
          <el-input-number v-model="rule.length.min" :min="0" :max="100000" controls-position="right" />
          <span class="dash">~</span>
          <el-input-number v-model="rule.length.max" :min="1" :max="100000" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="form.rule_type === 'regex'" label="正则表达式">
          <el-input v-model="rule.regex.pattern" placeholder="如 ^[0-9]{18}$" />
        </el-form-item>
        <el-form-item v-if="form.rule_type === 'enum'" label="枚举取值">
          <el-input v-model="rule.enumText" placeholder="多个取值用英文逗号分隔，如 公开,内部,受限" />
        </el-form-item>
        <el-form-item v-if="form.rule_type === 'range'" label="数值区间">
          <el-input-number v-model="rule.range.min" controls-position="right" />
          <span class="dash">~</span>
          <el-input-number v-model="rule.range.max" controls-position="right" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          <span class="hint">数值越大越靠前</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 校验结果抽屉 -->
    <el-dialog v-model="checkDialog.visible" title="校验规则检查结果" width="520px">
      <div class="check-result" :class="checkDialog.passed ? 'ok' : 'warn'">
        <el-icon><component :is="checkDialog.passed ? CircleCheck : Warning" /></el-icon>
        <span>{{ checkDialog.fieldName }}：{{ checkDialog.passed ? '规则有效' : '存在问题' }}</span>
      </div>
      <ul class="issue-list">
        <li v-for="(i, idx) in checkDialog.issues" :key="idx">{{ i }}</li>
      </ul>
      <p class="check-msg">{{ checkDialog.message }}</p>
      <template #footer>
        <el-button type="primary" @click="checkDialog.visible = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Collection,
  CircleCheck,
  Star,
  Warning,
  Grid,
  Search,
  RefreshLeft,
  Download,
  Plus,
  Edit,
  Delete,
  Files,
} from '@element-plus/icons-vue'
import {
  getOptions,
  getStats,
  listFields,
  createField,
  updateField,
  deleteField,
  checkRule,
  exportFields,
  type MetadataField,
  type MetadataStats,
  type MetadataOptions,
  type MetadataPayload,
} from '@/api/metadata'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const isAdmin = computed(() => store.user?.role_code === 'ADMIN')

const loading = ref(false)
const rows = ref<MetadataField[]>([])
const total = ref(0)
const checkingId = ref<number | null>(null)
const updatedAt = ref('')

const stats = reactive<MetadataStats>({
  total: 0,
  enabled: 0,
  disabled: 0,
  required: 0,
  pending: 0,
  domains: {},
})
const options = reactive<MetadataOptions>({ data_types: [], domains: [], rule_types: [] })

const query = reactive({
  keyword: '',
  domain: undefined as string | undefined,
  status: undefined as number | undefined,
  page: 1,
  page_size: 10,
})

const TYPE_LABELS: Record<string, string> = {
  string: '字符串',
  enum: '枚举',
  text: '长文本',
  number: '数值',
  date: '日期',
  bool: '布尔',
}
const RULE_LABELS: Record<string, string> = {
  length: '长度区间',
  regex: '正则匹配',
  enum: '枚举取值',
  range: '数值区间',
  none: '未配置',
}

function typeLabel(t: string): string {
  return TYPE_LABELS[t] ?? t
}
function ruleLabel(t: string): string {
  return RULE_LABELS[t] ?? t
}
function domainClass(d: string): string {
  return d === '业务' ? 't-purple' : d === '管理' ? 't-green' : d === '技术' ? 't-orange' : 't-blue'
}
function fmtTime(s: string): string {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const [pageData, s] = await Promise.all([
      listFields({
        keyword: query.keyword.trim() || undefined,
        domain: query.domain,
        status: query.status,
        page: query.page,
        page_size: query.page_size,
      }),
      getStats(),
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

function onReset() {
  query.keyword = ''
  query.domain = undefined
  query.status = undefined
  query.page = 1
  load()
  ElMessage.success('筛选条件已重置')
}

async function onExport() {
  await exportFields(query.domain)
  ElMessage.success('已导出元数据字段清单')
}

// ---------- 弹窗 ----------
const dialog = reactive({ visible: false, saving: false, title: '', id: 0 })
const formRef = ref<FormInstance>()
const form = reactive({
  field_name: '',
  field_code: '',
  data_type: 'string',
  domain: '基础',
  is_required: 0,
  status: 1,
  description: '',
  rule_type: 'none',
  sort_order: 0,
})
const rule = reactive({
  length: { min: 2, max: 120 },
  regex: { pattern: '' },
  range: { min: 0, max: 100 },
  enumText: '',
})

const rules: FormRules = {
  field_name: [{ required: true, message: '请输入字段名称', trigger: 'blur' }],
  field_code: [
    { required: true, message: '请输入字段编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '小写字母开头，仅限小写字母/数字/下划线', trigger: 'blur' },
  ],
  data_type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  domain: [{ required: true, message: '请选择元数据域', trigger: 'change' }],
}

function resetRuleInputs() {
  rule.length = { min: 2, max: 120 }
  rule.regex = { pattern: '' }
  rule.range = { min: 0, max: 100 }
  rule.enumText = ''
}

function onRuleTypeChange(val: string) {
  if (val === 'none') resetRuleInputs()
}

function parseRuleConfig(row: MetadataField) {
  resetRuleInputs()
  if (!row.rule_config) return
  try {
    const cfg = JSON.parse(row.rule_config)
    if (row.rule_type === 'length') rule.length = { min: cfg.min ?? 0, max: cfg.max ?? 120 }
    if (row.rule_type === 'regex') rule.regex = { pattern: cfg.pattern ?? '' }
    if (row.rule_type === 'range') rule.range = { min: cfg.min ?? 0, max: cfg.max ?? 100 }
    if (row.rule_type === 'enum') {
      rule.enumText = Array.isArray(cfg.options) ? cfg.options.join(',') : cfg.source ?? ''
    }
  } catch {
    // 历史数据规则参数非 JSON 时忽略，交由校验规则功能提示
  }
}

function buildRuleConfig(): string | null {
  switch (form.rule_type) {
    case 'length':
      return JSON.stringify({ min: rule.length.min, max: rule.length.max })
    case 'regex':
      return JSON.stringify({ pattern: rule.regex.pattern })
    case 'range':
      return JSON.stringify({ min: rule.range.min, max: rule.range.max })
    case 'enum': {
      const opts = rule.enumText.split(',').map((s) => s.trim()).filter(Boolean)
      return JSON.stringify({ options: opts })
    }
    default:
      return null
  }
}

function openCreate() {
  dialog.id = 0
  dialog.title = '新增元数据字段'
  Object.assign(form, {
    field_name: '',
    field_code: '',
    data_type: 'string',
    domain: '基础',
    is_required: 0,
    status: 1,
    description: '',
    rule_type: 'none',
    sort_order: 0,
  })
  resetRuleInputs()
  dialog.visible = true
}

function openEdit(row: MetadataField) {
  dialog.id = row.id
  dialog.title = '编辑元数据字段'
  Object.assign(form, {
    field_name: row.field_name,
    field_code: row.field_code,
    data_type: row.data_type,
    domain: row.domain,
    is_required: row.is_required,
    status: row.status,
    description: row.description ?? '',
    rule_type: row.rule_type || 'none',
    sort_order: row.sort_order,
  })
  parseRuleConfig(row)
  dialog.visible = true
}

async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  dialog.saving = true
  try {
    const payload: MetadataPayload = {
      field_name: form.field_name.trim(),
      field_code: form.field_code.trim(),
      data_type: form.data_type,
      domain: form.domain,
      is_required: form.is_required,
      status: form.status,
      description: form.description || null,
      rule_type: form.rule_type === 'none' ? null : form.rule_type,
      rule_config: buildRuleConfig(),
      sort_order: form.sort_order,
    }
    if (dialog.id) {
      const { field_code: _code, ...rest } = payload
      await updateField(dialog.id, rest)
      ElMessage.success('更新成功')
    } else {
      await createField(payload)
      ElMessage.success('创建成功')
      // 新字段排序值通常较小，落到末页；直接用编码定位，保证用户立刻看到
      query.keyword = payload.field_code
      query.domain = undefined
      query.status = undefined
      query.page = 1
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: MetadataField) {
  try {
    await ElMessageBox.confirm(`确定删除字段「${row.field_name}」吗？删除后不影响已存在的知识数据。`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  await deleteField(row.id)
  ElMessage.success('删除成功')
  if (query.keyword.trim() === row.field_code) query.keyword = ''
  if (rows.value.length === 1 && query.page > 1) query.page -= 1
  await load()
}

// ---------- 校验规则 ----------
const checkDialog = reactive({
  visible: false,
  passed: false,
  fieldName: '',
  issues: [] as string[],
  message: '',
})

async function onCheckRule(row: MetadataField) {
  checkingId.value = row.id
  try {
    const res = await checkRule(row.id)
    checkDialog.visible = true
    checkDialog.passed = res.passed
    checkDialog.fieldName = row.field_name
    checkDialog.issues = res.issues.length ? res.issues : ['未发现规则冲突']
    checkDialog.message = res.message
  } finally {
    checkingId.value = null
  }
}

onMounted(async () => {
  const opts = await getOptions()
  Object.assign(options, opts)
  await load()
})
</script>

<style scoped>
/* 政务蓝设计令牌（对齐 demo） */
.md-page {
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
  width: 230px;
}
.tool-select {
  width: 150px;
}
.btn-ghost {
  height: 32px;
}

/* 表格 */
.meta-table {
  width: 100%;
  --el-table-border-color: var(--border-2);
  font-size: 13.5px;
}
.meta-table :deep(th.el-table__cell) {
  background: var(--panel-2) !important;
  color: var(--text-2);
  font-weight: 600;
  font-size: 12.5px;
  letter-spacing: 0.3px;
  height: 44px;
}
.meta-table :deep(td.el-table__cell) {
  padding: 10px 0;
}
.meta-table :deep(.el-table__row:hover > td.el-table__cell) {
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
.cell-name b {
  font-weight: 600;
  letter-spacing: 0.2px;
  color: var(--text);
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
.req {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 11px;
  font-size: 11.5px;
}
.req-yes {
  color: var(--blue);
  border: 1px solid var(--blue-line);
  background: var(--blue-soft);
  font-weight: 600;
}
.req-no {
  color: var(--text-3);
  border: 1px solid var(--border);
  background: var(--panel-2);
}
.rule-tag {
  font-size: 12px;
  color: var(--text-2);
}
.rule-none {
  font-size: 12px;
  color: var(--warn);
}
.cell-time {
  color: var(--text-2);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
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

/* 弹窗内 */
.dash {
  margin: 0 8px;
  color: var(--text-3);
}
.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--text-3);
}
.check-result {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 12px;
  border-radius: 8px;
}
.check-result.ok {
  color: var(--ok);
  background: rgba(26, 138, 90, 0.1);
}
.check-result.warn {
  color: var(--warn);
  background: rgba(193, 125, 22, 0.12);
}
.issue-list {
  margin: 12px 0 0;
  padding-left: 20px;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.9;
}
.check-msg {
  margin: 10px 0 0;
  font-size: 12.5px;
  color: var(--text-3);
}

@media (max-width: 1200px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
  .tool-search,
  .tool-select {
    width: 100%;
  }
}
</style>
