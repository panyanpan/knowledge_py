<template>
  <div class="trace-page">
    <div class="crumb">
      <span>知识运营</span>
      <span class="sep">›</span>
      <b>知识溯源</b>
    </div>

    <div class="page-head">
      <div>
        <h2>知识溯源</h2>
        <p class="page-desc">
          按知识条目、业务场景或文档编号追溯知识全生命周期：数据来源、加工环节、校验规则、发布审批与引用记录，做到「来源可查、去向可追、责任可究」。
        </p>
      </div>
      <span class="page-sub">数据更新于 {{ updatedAt }}</span>
    </div>

    <!-- 统计条 -->
    <section class="stat-row">
      <div class="stat">
        <span class="stat-ico ico-blue"><el-icon><Collection /></el-icon></span>
        <dl class="stat-txt">
          <dt>已纳管知识条目</dt>
          <dd class="num">{{ stats.managed_entries }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-green"><el-icon><Guide /></el-icon></span>
        <dl class="stat-txt">
          <dt>链路完整可溯源</dt>
          <dd class="num">{{ stats.chain_complete }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-warn"><el-icon><Clock /></el-icon></span>
        <dl class="stat-txt">
          <dt>链路缺失待补录</dt>
          <dd class="num">{{ stats.chain_missing }}<small>条</small></dd>
        </dl>
      </div>
      <div class="stat">
        <span class="stat-ico ico-purple"><el-icon><Search /></el-icon></span>
        <dl class="stat-txt">
          <dt>近 30 日溯源查询</dt>
          <dd class="num">{{ stats.queries_30d }}<small>次</small></dd>
        </dl>
      </div>
    </section>

    <!-- 溯源查询 -->
    <section class="panel trace-search">
      <div class="ts-row">
        <el-input
          v-model="keyword"
          class="ts-input"
          placeholder="输入知识条目名称、知识编号、业务场景或文档编号"
          clearable
          :prefix-icon="Search"
          @keyup.enter="onTrace"
        />
        <el-button type="primary" class="ts-btn" :loading="tracing" :icon="Position" @click="onTrace">
          开始溯源
        </el-button>
      </div>
      <div class="ts-chips">
        <span class="ts-label">快捷溯源：</span>
        <button
          v-for="c in options.chips"
          :key="c.id"
          class="chip"
          :class="{ on: current?.id === c.id }"
          @click="traceById(c.id)"
        >
          {{ c.title }}
        </button>
      </div>

      <div v-if="current" class="meta-strip">
        <div class="ms-item"><span>知识编号</span><b class="num">{{ current.entry_no }}</b></div>
        <div class="ms-item"><span>所属分类</span><b>{{ current.category }}</b></div>
        <div class="ms-item"><span>当前版本</span><b class="num">{{ current.version }}</b></div>
        <div class="ms-item"><span>责任部门</span><b>{{ current.dept }}</b></div>
        <div class="ms-item"><span>密级</span><b><em class="ntag" :class="secretClass(current.secret_level)">{{ current.secret_level }}</em></b></div>
        <div class="ms-item"><span>链路状态</span><b><em class="ntag" :class="current.chain_status === 1 ? 't-green' : 't-warn'">{{ current.chain_status === 1 ? '完整可溯源' : '缺失待补录' }}</em></b></div>
      </div>
    </section>

    <!-- 溯源链路 -->
    <section class="panel" style="margin-top: 16px">
      <div class="panel-head">
        <h3><el-icon><Guide /></el-icon>溯源链路</h3>
        <div class="tools">
          <span class="head-tip">共 <b class="num">{{ nodes.length }}</b> 个环节 · 点击环节查看明细</span>
          <el-button class="btn-ghost" :icon="Upload" @click="exportReport">导出溯源报告</el-button>
        </div>
      </div>
      <div class="panel-body pad">
        <div v-if="nodes.length" class="chain">
          <template v-for="(n, i) in nodes" :key="n.id">
            <div class="chain-node" :class="{ on: activeStep === i, warn: n.result_level === 'warn' }" @click="locateNode(i)">
              <span class="cn-idx num">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="cn-ico"><el-icon><component :is="stepIcon(i)" /></el-icon></span>
              <b>{{ n.name }}</b>
              <em class="cn-sub">{{ n.sub }}</em>
              <span class="cn-time num">{{ fmtTime(n.occurred_at) }}</span>
              <em class="cn-tag" :class="tagClass(n.result_level)">{{ n.result }}</em>
            </div>
            <span v-if="i < nodes.length - 1" class="chain-link"><el-icon><Right /></el-icon></span>
          </template>
        </div>
        <div v-else class="empty-hint">在上方输入知识条目名称或点击快捷主题开始溯源</div>

        <div class="chain-note">
          <el-icon><Lock /></el-icon>
          <span>链路节点由系统自动记存，任何环节的修改均生成不可篡改的留痕记录；如发现来源缺失，可在「知识治理」中提交整改。</span>
        </div>
      </div>
    </section>

    <!-- 溯源环节明细 -->
    <section class="panel" style="margin-top: 16px">
      <div class="panel-head">
        <h3><el-icon><Document /></el-icon>溯源环节明细</h3>
        <div class="tools">
          <el-input
            v-model="detailKw"
            class="tool-search"
            placeholder="按环节 / 操作主体检索"
            clearable
            :prefix-icon="Search"
          />
          <el-button class="btn-ghost" :icon="RefreshLeft" @click="detailKw = ''">重置</el-button>
        </div>
      </div>
      <div class="panel-body">
        <el-table
          v-loading="tracing"
          :data="filteredNodes"
          class="kb-table trace-table"
          :row-class-name="rowClass"
        >
          <el-table-column type="index" label="序号" width="64" align="center" :index="(i: number) => i + 1" />
          <el-table-column label="环节名称" min-width="220">
            <template #default="{ row }">
              <div class="cell-name">
                <b>{{ row.name }}</b>
                <span class="sub">{{ row.sub }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="发生时间" width="160">
            <template #default="{ row }"><span class="cell-time">{{ fmtTime(row.occurred_at) }}</span></template>
          </el-table-column>
          <el-table-column prop="actor" label="操作主体" min-width="170" />
          <el-table-column label="来源依据（系统 / 文件 / 单据）" min-width="240">
            <template #default="{ row }"><code class="code">{{ row.source_ref }}</code></template>
          </el-table-column>
          <el-table-column label="校验结果" width="110" align="center">
            <template #default="{ row }"><em class="ntag" :class="tagClass(row.result_level)">{{ row.result }}</em></template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button class="btn-op-plain" link type="primary" :icon="Document" @click="showEvidence(row)">查看凭证</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-hint">未检索到符合条件的溯源环节</div>
          </template>
        </el-table>
      </div>
    </section>

    <!-- 存证凭证（演示） -->
    <el-dialog v-model="eviDialog" title="存证凭证（演示内容，待 API 对接后替换）" width="560" class="evi-dialog">
      <template v-if="eviRow">
        <div class="evi-head">
          <el-icon class="evi-ico"><Stamp /></el-icon>
          <div>
            <b>{{ eviRow.name }}</b>
            <span>{{ eviRow.actor }} · {{ fmtTime(eviRow.occurred_at) }}</span>
          </div>
          <em class="ntag" :class="tagClass(eviRow.result_level)">{{ eviRow.result }}</em>
        </div>
        <div class="evi-meta">
          <div><span>来源依据</span><code>{{ eviRow.source_ref }}</code></div>
          <div><span>存证时间戳</span><code>{{ eviStamp }}</code></div>
          <div><span>留痕哈希</span><code>{{ eviHash }}</code></div>
        </div>
        <p class="evi-text">{{ eviRow.evidence || '暂无凭证内容' }}</p>
      </template>
      <template #footer>
        <el-button @click="eviDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Clock,
  Collection,
  Connection,
  Cpu,
  Document,
  Finished,
  Guide,
  Link,
  Lock,
  Position,
  RefreshLeft,
  Right,
  Search,
  Stamp,
  Upload,
} from '@element-plus/icons-vue'
import {
  getTraceOptions,
  getTraceStats,
  listTraces,
  runTrace,
  type KbTrace,
  type TraceNode,
  type TraceOptions,
  type TraceStats,
} from '@/api/traces'

const updatedAt = ref('2026-10-30 08:26')
const stats = reactive<TraceStats>({ managed_entries: 0, chain_complete: 0, chain_missing: 0, queries_30d: 0 })
const options = reactive<TraceOptions>({ chips: [], secret_levels: [], chain_status: [] })

const keyword = ref('')
const tracing = ref(false)
const current = ref<KbTrace | null>(null)
const nodes = ref<TraceNode[]>([])
const activeStep = ref(-1)
const detailKw = ref('')

const eviDialog = ref(false)
const eviRow = ref<TraceNode | null>(null)
const eviStamp = ref('')
const eviHash = ref('')

const filteredNodes = computed(() => {
  const kw = detailKw.value.trim().toLowerCase()
  if (!kw) return nodes.value
  return nodes.value.filter(
    (n) => n.name.toLowerCase().includes(kw) || n.actor.toLowerCase().includes(kw),
  )
})

const STEP_ICONS = [Connection, Document, Cpu, Finished, Stamp, Link]
function stepIcon(i: number) {
  return STEP_ICONS[i % STEP_ICONS.length]
}
function tagClass(level: string): string {
  return level === 'green' ? 't-green' : level === 'warn' ? 't-warn' : 't-blue'
}
function secretClass(s: string): string {
  return s === '公开' ? 't-green' : s === '内部' ? 't-blue' : 't-warn'
}
function fmtTime(s: string | null): string {
  if (!s) return '—'
  return s.replace('T', ' ').slice(0, 16)
}
function rowClass({ row }: { row: TraceNode }): string {
  const i = nodes.value.findIndex((n) => n.id === row.id)
  return i === activeStep.value ? 'cur-row' : ''
}

async function loadBase() {
  const [st, op] = await Promise.all([getTraceStats(), getTraceOptions()])
  Object.assign(stats, st)
  Object.assign(options, op)
}

function applyTrace(t: KbTrace) {
  current.value = t
  nodes.value = t.nodes ?? []
  activeStep.value = nodes.value.length ? 0 : -1
}

async function traceById(id: number) {
  tracing.value = true
  try {
    applyTrace(await runTrace(id))
  } finally {
    tracing.value = false
  }
}

async function onTrace() {
  const kw = keyword.value.trim()
  if (!kw) {
    ElMessage.warning('请输入知识条目名称、编号或业务场景')
    return
  }
  tracing.value = true
  try {
    const { list } = await listTraces(kw)
    if (list.length) {
      await traceById(list[0].id)
      ElMessage.success(`溯源完成：「${current.value?.title}」，共 ${nodes.value.length} 个环节`)
    } else {
      ElMessage.info(`未找到与「${kw}」匹配的溯源主题（演示数据暂含 4 个主题）`)
    }
  } finally {
    tracing.value = false
  }
}

function locateNode(i: number) {
  activeStep.value = i
  const target = document.querySelector(`.trace-table .el-table__body tr:nth-child(${i + 1})`)
  target?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
}

function showEvidence(row: TraceNode) {
  eviRow.value = row
  eviStamp.value = row.occurred_at ? `${fmtTime(row.occurred_at)}:36（可信时间源）` : '—'
  const seed = `${row.id}-${row.step_no}`
  eviHash.value = `SHA-256 ${seed.length.toString(16).padStart(4, '0')}…${((row.id * 7919) % 0xffff).toString(16).padStart(4, '0')}`
  eviDialog.value = true
}

function exportReport() {
  ElMessage.success('已生成《知识溯源报告》演示文件，正式导出待后续 API 对接后开放下载')
}

onMounted(async () => {
  await loadBase()
  if (options.chips.length) {
    keyword.value = options.chips[0].title
    await traceById(options.chips[0].id)
  }
})
</script>

<style scoped>
/* 政务蓝设计令牌（对齐元数据/知识/规则/服务市场页） */
.trace-page {
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
  display: flex;
  gap: 6px;
  align-items: center;
}
.crumb b {
  color: var(--text);
}
.sep {
  color: var(--text-3);
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin: 12px 0 16px;
}
.page-head h2 {
  margin: 0 0 6px;
  font-size: 20px;
}
.page-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-2);
  max-width: 760px;
  line-height: 1.7;
}
.page-sub {
  font-size: 12px;
  color: var(--text-3);
  white-space: nowrap;
}
.num {
  font-variant-numeric: tabular-nums;
}

/* 统计条 */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.stat {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-ico {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  font-size: 19px;
}
.ico-blue {
  background: var(--blue-soft);
  color: var(--blue);
}
.ico-green {
  background: rgba(26, 138, 90, 0.12);
  color: var(--ok);
}
.ico-warn {
  background: rgba(193, 125, 22, 0.13);
  color: var(--warn);
}
.ico-purple {
  background: rgba(99, 80, 196, 0.12);
  color: var(--purple);
}
.stat-txt {
  margin: 0;
}
.stat-txt dt {
  font-size: 12px;
  color: var(--text-2);
}
.stat-txt dd {
  margin: 4px 0 0;
  font-size: 22px;
  font-weight: 700;
}
.stat-txt dd small {
  font-size: 12px;
  color: var(--text-3);
  font-weight: 400;
  margin-left: 4px;
}

/* 面板 */
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-2);
  gap: 12px;
  flex-wrap: wrap;
}
.panel-head h3 {
  margin: 0;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--blue);
}
.tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.head-tip {
  font-size: 12px;
  color: var(--text-2);
}
.head-tip b {
  color: var(--blue);
}
.tool-search {
  width: 220px;
}
.panel-body {
  padding: 12px 16px 16px;
}
.panel-body.pad {
  padding: 16px;
}

/* 溯源查询面板 */
.trace-search {
  padding: 16px;
}
.ts-row {
  display: flex;
  gap: 10px;
}
.ts-input {
  flex: 1;
}
.ts-btn {
  min-width: 120px;
}
.ts-chips {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.ts-label {
  font-size: 12px;
  color: var(--text-3);
}
.chip {
  border: 1px solid var(--blue-line);
  background: var(--blue-soft);
  color: var(--blue);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.chip:hover {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
}
.chip.on {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
  font-weight: 600;
}
.meta-strip {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-top: 14px;
  background: var(--panel-2);
  border: 1px dashed var(--blue-line);
  border-radius: 8px;
  padding: 12px 14px;
}
.ms-item span {
  display: block;
  font-size: 11px;
  color: var(--text-3);
  margin-bottom: 4px;
}
.ms-item b {
  font-size: 13px;
  word-break: break-all;
}

/* 彩色标签 */
.ntag {
  display: inline-block;
  font-style: normal;
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 10px;
  line-height: 1.5;
  white-space: nowrap;
}
.t-green {
  background: rgba(26, 138, 90, 0.12);
  color: var(--ok);
}
.t-blue {
  background: var(--blue-soft);
  color: var(--blue);
}
.t-warn {
  background: rgba(193, 125, 22, 0.14);
  color: var(--warn);
}

/* 溯源链路 */
.chain {
  display: flex;
  align-items: stretch;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.chain-node {
  flex: 1 0 130px;
  min-width: 130px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--panel-2);
  padding: 12px 12px 10px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.chain-node:hover {
  border-color: var(--blue-line);
}
.chain-node.on {
  border-color: var(--blue);
  background: var(--blue-soft);
  box-shadow: 0 2px 10px rgba(26, 95, 180, 0.15);
}
.chain-node.warn {
  border-color: rgba(193, 125, 22, 0.4);
}
.chain-node.warn.on {
  border-color: var(--warn);
  background: rgba(193, 125, 22, 0.07);
  box-shadow: 0 2px 10px rgba(193, 125, 22, 0.15);
}
.cn-idx {
  position: absolute;
  top: 8px;
  right: 10px;
  font-size: 11px;
  color: var(--text-3);
  font-weight: 600;
}
.cn-ico {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--blue-soft);
  color: var(--blue);
  display: grid;
  place-items: center;
  font-size: 16px;
}
.chain-node.warn .cn-ico {
  background: rgba(193, 125, 22, 0.13);
  color: var(--warn);
}
.chain-node b {
  font-size: 13px;
}
.cn-sub {
  font-style: normal;
  font-size: 11px;
  color: var(--text-2);
  line-height: 1.4;
  min-height: 30px;
}
.cn-time {
  font-size: 11px;
  color: var(--text-3);
}
.cn-tag {
  align-self: flex-start;
  display: inline-block;
  font-style: normal;
  font-size: 11px;
  border-radius: 999px;
  padding: 1px 8px;
}
.chain-link {
  align-self: center;
  color: var(--text-3);
  flex: 0 0 auto;
}
.chain-note {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 12px;
  background: var(--blue-soft);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.6;
}
.chain-note .el-icon {
  color: var(--blue);
  margin-top: 2px;
}
.empty-hint {
  text-align: center;
  color: var(--text-3);
  font-size: 13px;
  padding: 28px 0;
}

/* 明细表 */
.cell-name b {
  display: block;
  font-size: 13px;
}
.cell-name .sub {
  font-size: 12px;
  color: var(--text-3);
}
.cell-time {
  font-variant-numeric: tabular-nums;
  color: var(--text-2);
  font-size: 12px;
}
.code {
  font-family: Consolas, 'SFMono-Regular', Menlo, monospace;
  font-size: 12px;
  background: var(--panel-2);
  border: 1px solid var(--border-2);
  border-radius: 5px;
  padding: 2px 7px;
  color: var(--blue-2);
  word-break: break-all;
}
:deep(.trace-table .cur-row) td {
  background: var(--blue-soft) !important;
}
:deep(.el-table .btn-op-plain .el-icon) {
  margin-right: 2px;
}

/* 凭证弹窗 */
.evi-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-2);
}
.evi-ico {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  background: var(--blue-soft);
  color: var(--blue);
  display: grid;
  place-items: center;
  font-size: 19px;
  flex: 0 0 auto;
}
.evi-head b {
  display: block;
  font-size: 14px;
}
.evi-head span {
  font-size: 12px;
  color: var(--text-3);
}
.evi-head .ntag {
  margin-left: auto;
}
.evi-meta {
  display: grid;
  gap: 8px;
  margin: 12px 0;
}
.evi-meta > div {
  display: flex;
  gap: 10px;
  align-items: baseline;
}
.evi-meta span {
  flex: 0 0 76px;
  font-size: 12px;
  color: var(--text-3);
}
.evi-meta code {
  font-family: Consolas, 'SFMono-Regular', Menlo, monospace;
  font-size: 12px;
  color: var(--blue-2);
  word-break: break-all;
}
.evi-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-2);
  background: var(--panel-2);
  border-radius: 8px;
  padding: 12px 14px;
}

@media (max-width: 1100px) {
  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .meta-strip {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
