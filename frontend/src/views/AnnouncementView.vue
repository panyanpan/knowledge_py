<template>
  <el-card>
    <template #header>
      <div class="card-head">
        <span>公告 / 轮播图管理</span>
        <div>
          <el-button type="primary" :icon="Plus" @click="openCreate(1)">新建公告</el-button>
          <el-button type="primary" plain :icon="Plus" @click="openCreate(2)">新建轮播图</el-button>
        </div>
      </div>
    </template>

    <el-form inline class="filters">
      <el-form-item label="类型">
        <el-select v-model="typeFilter" clearable placeholder="全部" style="width: 140px" @change="onFilter">
          <el-option label="公告" :value="1" />
          <el-option label="轮播图" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.type === 2 ? 'warning' : 'primary'" size="small">
            {{ row.type === 2 ? '轮播图' : '公告' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="content" label="内容" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ row.content || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_published === 1 ? 'success' : 'info'" size="small">
            {{ row.is_published === 1 ? '已发布' : '已下线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="togglePublish(row)">
            {{ row.is_published === 1 ? '下线' : '发布' }}
          </el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      @current-change="load"
    />

    <el-dialog v-model="dialog.visible" :title="dialog.title" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio :value="1">公告</el-radio>
            <el-radio :value="2">轮播图</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="标题" />
        </el-form-item>
        <el-form-item v-if="form.type === 1" label="正文">
          <el-input v-model="form.content" type="textarea" :rows="6" maxlength="5000" show-word-limit placeholder="公告正文（纯文本）" />
        </el-form-item>
        <el-form-item v-else label="图片地址">
          <el-input v-model="form.image_url" placeholder="https://…（可选，留空则显示文字版）" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.link_url" placeholder="https://…（可选）" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_published" :active-value="1" :inactive-value="0" active-text="发布" inactive-text="下线" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  listAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
} from '@/api/announcements'
import type { Announcement } from '@/api/portal'

const loading = ref(false)
const rows = ref<Announcement[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const typeFilter = ref<number | undefined>()

const dialog = reactive({ visible: false, saving: false, title: '', id: 0 })
const formRef = ref<FormInstance>()
const form = reactive({
  type: 1,
  title: '',
  content: '',
  image_url: '',
  link_url: '',
  sort_order: 0,
  is_published: 1,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

function fmtTime(s: string): string {
  return s ? s.replace('T', ' ').slice(0, 19) : ''
}

async function load() {
  loading.value = true
  try {
    const data = await listAnnouncements({
      type: typeFilter.value,
      page: page.value,
      page_size: pageSize,
    })
    rows.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onFilter() {
  page.value = 1
  load()
}

function openCreate(type: number) {
  dialog.id = 0
  dialog.title = type === 2 ? '新建轮播图' : '新建公告'
  Object.assign(form, {
    type,
    title: '',
    content: '',
    image_url: '',
    link_url: '',
    sort_order: 0,
    is_published: 1,
  })
  dialog.visible = true
}

function openEdit(row: Announcement) {
  dialog.id = row.id
  dialog.title = '编辑' + (row.type === 2 ? '轮播图' : '公告')
  Object.assign(form, {
    type: row.type,
    title: row.title,
    content: row.content ?? '',
    image_url: row.image_url ?? '',
    link_url: row.link_url ?? '',
    sort_order: row.sort_order,
    is_published: row.is_published,
  })
  dialog.visible = true
}

async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  dialog.saving = true
  try {
    const payload = {
      type: form.type,
      title: form.title.trim(),
      content: form.content || null,
      image_url: form.image_url || null,
      link_url: form.link_url || null,
      sort_order: form.sort_order,
      is_published: form.is_published,
    }
    if (dialog.id) {
      await updateAnnouncement(dialog.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createAnnouncement(payload)
      ElMessage.success('创建成功')
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function togglePublish(row: Announcement) {
  await updateAnnouncement(row.id, { is_published: row.is_published === 1 ? 0 : 1 })
  ElMessage.success(row.is_published === 1 ? '已下线' : '已发布')
  await load()
}

async function onDelete(row: Announcement) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」吗？`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  await deleteAnnouncement(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(load)
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filters {
  margin-bottom: 4px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
