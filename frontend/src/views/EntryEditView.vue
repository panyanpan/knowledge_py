<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="card-head">
        <span>{{ isEdit ? '编辑条目' : '新建条目' }}</span>
        <el-button :icon="Back" @click="router.back()">返回</el-button>
      </div>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="entry-form">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="条目标题" />
      </el-form-item>
      <el-form-item label="所属分类" prop="category_id">
        <el-tree-select
          v-model="form.category_id"
          :data="categoryOptions"
          check-strictly
          placeholder="请选择分类"
          style="width: 320px"
        />
      </el-form-item>
      <el-form-item label="可见性">
        <el-radio-group v-model="form.visibility">
          <el-radio :value="0">私有（仅自己和管理员可见）</el-radio>
          <el-radio :value="1">公开（门户匿名可见）</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="标签">
        <el-select
          v-model="form.tag_ids"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="选择或输入新标签后回车"
          style="width: 100%"
          :multiple-limit="20"
        >
          <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="摘要">
        <el-input v-model="form.summary" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="选填，列表页展示" />
      </el-form-item>
      <el-form-item label="正文">
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

      <el-form-item v-if="isEdit" label="附件">
        <div class="att-block">
          <el-upload
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="doUpload"
            multiple
          >
            <el-button type="primary" plain :icon="Upload" :loading="uploading">上传附件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 pdf/office/图片/压缩包等 17 类扩展名，单个 ≤10MB
              </div>
            </template>
          </el-upload>
          <el-table v-if="form.attachments.length" :data="form.attachments" size="small" class="att-table">
            <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column label="大小" width="100">
              <template #default="{ row }">{{ fmtSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="onDownload(row)">下载</el-button>
                <el-button link type="danger" @click="onAttDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-form-item>
      <el-form-item v-else label="附件">
        <span class="muted">请先保存条目后再上传附件</span>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadRequestOptions } from 'element-plus'
import { Back, Upload } from '@element-plus/icons-vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import '@wangeditor/editor/dist/css/style.css'
import type { IDomEditor } from '@wangeditor/editor'

import { getCategories, type CategoryNode } from '@/api/categories'
import { getTags, createTag, type Tag } from '@/api/tags'
import {
  getEntry,
  createEntry,
  updateEntry,
  type EntryDetail,
  type Attachment,
} from '@/api/entries'
import {
  uploadAttachment,
  deleteAttachment,
  downloadAttachment,
} from '@/api/attachments'

const route = useRoute()
const router = useRouter()
// 路由参数响应式：/entries/new 保存后 replace 到 /entries/:id/edit 时组件被复用，
// 必须用 computed 而非 setup 时固化，否则附件区块永不显示
const entryId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => entryId.value !== null)

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const formRef = ref<FormInstance>()
const tags = ref<Tag[]>([])
const tree = ref<CategoryNode[]>([])

const form = reactive({
  title: '',
  category_id: undefined as number | undefined,
  visibility: 0,
  tag_ids: [] as number[],
  summary: '',
  content: '',
  attachments: [] as Attachment[],
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

// ---- 富文本 ----
const editorRef = shallowRef<IDomEditor>()
const toolbarConfig = {}
const editorConfig = { placeholder: '开始编写正文…' }
function onEditorCreated(editor: IDomEditor) {
  editorRef.value = editor
}
onBeforeUnmount(() => editorRef.value?.destroy())

const categoryOptions = computed(() => {
  const toOpt = (n: CategoryNode): Record<string, unknown> => ({
    value: n.id,
    label: n.name,
    children: n.children.map(toOpt),
  })
  return tree.value.map(toOpt)
})

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadMeta() {
  ;[tree.value, tags.value] = await Promise.all([getCategories(), getTags()])
}

async function loadEntry() {
  if (!entryId.value) return
  const e: EntryDetail = await getEntry(entryId.value)
  form.title = e.title
  form.category_id = e.category_id
  form.visibility = e.visibility
  form.tag_ids = e.tags.map((t) => t.id)
  form.summary = e.summary ?? ''
  form.content = e.content ?? ''
  form.attachments = e.attachments
}

// 路由参数变化（new → :id/edit）时重置并加载
watch(entryId, async (id) => {
  form.title = ''
  form.category_id = undefined
  form.visibility = 0
  form.tag_ids = []
  form.summary = ''
  form.content = ''
  form.attachments = []
  if (id) await loadEntry()
})

// 标签：allow-create 会把输入的新名称作为字符串值放进 tag_ids，
// watcher 检测到字符串后调创建接口（后端同名幂等），再把字符串替换为真实 id
let creatingTag = false
watch(
  () => [...form.tag_ids],
  async (vals) => {
    const nameIdx = vals.findIndex((v) => typeof v === 'string')
    if (nameIdx < 0 || creatingTag) return
    const name = (vals[nameIdx] as unknown as string).trim()
    form.tag_ids = form.tag_ids.filter((v) => typeof v !== 'string')
    if (!name) return
    creatingTag = true
    try {
      const tag = await createTag(name)
      if (!tags.value.some((t) => t.id === tag.id)) tags.value.push(tag)
      form.tag_ids.push(tag.id)
    } finally {
      creatingTag = false
    }
  },
)

// ---- 附件 ----
const ALLOWED_EXTS = [
  'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'csv',
  'png', 'jpg', 'jpeg', 'gif', 'webp', 'zip', 'rar', '7z',
]

function beforeUpload(file: File): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!ALLOWED_EXTS.includes(ext)) {
    ElMessage.error(`不支持的文件类型：.${ext}`)
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小超过 10MB 限制')
    return false
  }
  return true
}

async function doUpload(options: UploadRequestOptions) {
  uploading.value = true
  try {
    const att = await uploadAttachment(entryId.value!, options.file)
    form.attachments.push(att)
    ElMessage.success(`「${att.file_name}」上传成功`)
  } finally {
    uploading.value = false
  }
}

async function onAttDelete(att: Attachment) {
  try {
    await ElMessageBox.confirm(`确定删除附件「${att.file_name}」吗？`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  await deleteAttachment(att.id)
  form.attachments = form.attachments.filter((a) => a.id !== att.id)
  ElMessage.success('删除成功')
}

async function onDownload(att: Attachment) {
  await downloadAttachment(att)
}

// ---- 保存 ----
async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = {
      category_id: form.category_id!,
      title: form.title.trim(),
      content: form.content || null,
      summary: form.summary || null,
      visibility: form.visibility,
      tag_ids: form.tag_ids,
    }
    if (isEdit.value && entryId.value) {
      await updateEntry(entryId.value, payload)
      ElMessage.success('保存成功')
    } else {
      const created = await createEntry(payload)
      ElMessage.success('创建成功，可上传附件')
      // 路由 replace 触发 entryId watcher，重置表单并加载新建条目（编辑态）
      router.replace(`/entries/${created.id}/edit`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadMeta()
    await loadEntry()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.entry-form {
  max-width: 900px;
}
.editor-wrap {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  z-index: 100;
}
.editor-toolbar {
  border-bottom: 1px solid #dcdfe6;
}
.editor-content {
  height: 360px;
  overflow-y: hidden;
}
.att-block {
  width: 100%;
}
.att-table {
  margin-top: 10px;
}
.muted {
  color: #909399;
  font-size: 13px;
}
</style>
