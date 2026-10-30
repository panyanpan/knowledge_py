<template>
  <el-card>
    <template #header>
      <div class="card-head">
        <span>分类管理</span>
        <el-button type="primary" :icon="Plus" @click="openCreate(0)">新建顶级分类</el-button>
      </div>
    </template>

    <el-tree
      v-loading="loading"
      :data="tree"
      node-key="id"
      :props="{ label: 'name', children: 'children' }"
      default-expand-all
      :expand-on-click-node="false"
    >
      <template #default="{ data }">
        <div class="node">
          <span>{{ data.name }}</span>
          <span class="node-meta">Level {{ data.level }} · 排序 {{ data.sort_order }}</span>
          <span class="node-actions">
            <el-button link type="primary" :icon="Plus" @click="openCreate(data.id)">子级</el-button>
            <el-button link type="primary" :icon="Edit" @click="openEdit(data)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="onDelete(data)">删除</el-button>
          </span>
        </div>
      </template>
    </el-tree>

    <el-dialog v-model="dialog.visible" :title="dialog.title" width="420px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" maxlength="100" placeholder="分类名称" />
        </el-form-item>
        <el-form-item v-if="!dialog.editing" label="父级">
          <el-tree-select
            v-model="form.parent_id"
            :data="parentOptions"
            check-strictly
            :render-after-expand="false"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
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
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  type CategoryNode,
} from '@/api/categories'

const loading = ref(false)
const tree = ref<CategoryNode[]>([])

const dialog = reactive({ visible: false, saving: false, editing: false, title: '', nodeId: 0 })
const form = reactive({ name: '', parent_id: 0, sort_order: 0 })

// 树形父级下拉：包含"顶级(0)"
const parentOptions = computed(() => {
  const toOpt = (n: CategoryNode): Record<string, unknown> => ({
    value: n.id,
    label: n.name,
    children: n.children.map(toOpt),
  })
  return [{ value: 0, label: '顶级分类', children: tree.value.map(toOpt) }]
})

async function load() {
  loading.value = true
  try {
    tree.value = await getCategories()
  } finally {
    loading.value = false
  }
}

function openCreate(parentId: number) {
  dialog.editing = false
  dialog.title = parentId === 0 ? '新建顶级分类' : '新建子分类'
  form.name = ''
  form.parent_id = parentId
  form.sort_order = 0
  dialog.visible = true
}

function openEdit(node: CategoryNode) {
  dialog.editing = true
  dialog.title = '编辑分类'
  dialog.nodeId = node.id
  form.name = node.name
  form.sort_order = node.sort_order
  dialog.visible = true
}

async function onSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  dialog.saving = true
  try {
    if (dialog.editing) {
      await updateCategory(dialog.nodeId, { name: form.name.trim(), sort_order: form.sort_order })
    } else {
      await createCategory({
        name: form.name.trim(),
        parent_id: form.parent_id,
        sort_order: form.sort_order,
      })
    }
    ElMessage.success('保存成功')
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(node: CategoryNode) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${node.name}」吗？若其下存在子分类或知识条目，删除将被拒绝。`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteCategory(node.id)
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
.node {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.node-meta {
  color: #909399;
  font-size: 12px;
}
.node-actions {
  margin-left: auto;
  display: none;
}
:deep(.el-tree-node__content:hover) .node-actions {
  display: inline-flex;
}
</style>
