<template>
  <el-card>
    <template #header>
      <div class="card-head">
        <span>知识条目</span>
        <el-button type="primary" :icon="Plus" @click="router.push('/entries/new')">新建条目</el-button>
      </div>
    </template>

    <el-form inline class="filters">
      <el-form-item label="关键词">
        <el-input
          v-model="query.keyword"
          placeholder="标题/内容搜索"
          clearable
          style="width: 220px"
          @keyup.enter="onSearch"
          @clear="onSearch"
        />
      </el-form-item>
      <el-form-item label="分类">
        <el-tree-select
          v-model="query.category_id"
          :data="categoryOptions"
          check-strictly
          clearable
          placeholder="全部分类"
          style="width: 180px"
          @change="onSearch"
        />
      </el-form-item>
      <el-form-item label="可见性">
        <el-select v-model="query.visibility" clearable placeholder="全部" style="width: 120px" @change="onSearch">
          <el-option label="私有" :value="0" />
          <el-option label="公开" :value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="onSearch">搜索</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="router.push(`/entries/${row.id}/edit`)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="160">
        <template #default="{ row }">
          <el-tag v-for="t in row.tags" :key="t.id" size="small" class="tag-item">{{ t.name }}</el-tag>
          <span v-if="!row.tags.length" class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="可见性" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.visibility === 1 ? 'success' : 'info'" size="small">
            {{ row.visibility === 1 ? '公开' : '私有' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="view_count" label="浏览" width="80" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/entries/${row.id}/edit`)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="query.page"
      v-model:page-size="query.page_size"
      class="pager"
      layout="total, prev, pager, next, sizes"
      :total="total"
      :page-sizes="[10, 20, 50]"
      @current-change="load"
      @size-change="onSearch"
    />
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { listEntries, deleteEntry, type EntryBrief } from '@/api/entries'
import { getCategories, type CategoryNode } from '@/api/categories'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const loading = ref(false)
const rows = ref<EntryBrief[]>([])
const total = ref(0)
const tree = ref<CategoryNode[]>([])

const query = reactive({
  keyword: '',
  category_id: undefined as number | undefined,
  visibility: undefined as number | undefined,
  page: 1,
  page_size: 10,
})

const categoryOptions = computed(() => {
  const toOpt = (n: CategoryNode): Record<string, unknown> => ({
    value: n.id,
    label: n.name,
    children: n.children.map(toOpt),
  })
  return tree.value.map(toOpt)
})

function fmtTime(s: string): string {
  return s ? s.replace('T', ' ').slice(0, 19) : ''
}

async function load() {
  loading.value = true
  try {
    const data = await listEntries({
      keyword: query.keyword.trim() || undefined,
      category_id: query.category_id,
      visibility: query.visibility,
      page: query.page,
      page_size: query.page_size,
    })
    rows.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  load()
}

async function onDelete(row: EntryBrief) {
  const isAdmin = store.user?.role_code === 'ADMIN'
  try {
    await ElMessageBox.confirm(
      `确定删除条目「${row.title}」吗？${isAdmin ? '' : '仅能删除自己创建的条目。'}`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteEntry(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(async () => {
  load()
  tree.value = await getCategories()
})
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
.tag-item {
  margin-right: 6px;
}
.muted {
  color: #c0c4cc;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
