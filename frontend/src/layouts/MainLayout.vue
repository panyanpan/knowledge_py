<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">📚 知识库管理</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/categories">
          <el-icon><FolderOpened /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Notebook /></el-icon>
          <span>知识管理</span>
        </el-menu-item>
        <el-menu-item index="/rules">
          <el-icon><SetUp /></el-icon>
          <span>规则管理</span>
        </el-menu-item>
        <el-menu-item index="/services">
          <el-icon><Goods /></el-icon>
          <span>服务市场</span>
        </el-menu-item>
        <el-menu-item index="/traces">
          <el-icon><Guide /></el-icon>
          <span>知识溯源</span>
        </el-menu-item>
        <el-menu-item index="/entries">
          <el-icon><Document /></el-icon>
          <span>知识条目</span>
        </el-menu-item>
        <el-menu-item index="/metadata">
          <el-icon><Grid /></el-icon>
          <span>知识元数据</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/announcements">
          <el-icon><Bell /></el-icon>
          <span>公告管理</span>
        </el-menu-item>
        <el-menu-item index="/portal">
          <el-icon><Monitor /></el-icon>
          <span>知识门户</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div />
        <el-dropdown @command="onCommand">
          <span class="user-info">
            <el-avatar :size="30" class="avatar">{{ displayName.charAt(0) }}</el-avatar>
            {{ displayName }}（{{ store.user?.role_code }}）
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { HomeFilled, FolderOpened, Document, ArrowDown, Bell, Monitor, Grid, Notebook, SetUp, Goods, Guide } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { logoutApi } from '@/api/authApi'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const displayName = computed(() => store.user?.nickname || store.user?.username || '用户')
const isAdmin = computed(() => store.user?.role_code === 'ADMIN')

async function onCommand(cmd: string) {
  if (cmd !== 'logout') return
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await logoutApi()
  } catch {
    // 后端登出失败不阻塞本地清理
  }
  store.clear()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
}
.menu {
  border-right: none;
}
.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.avatar {
  background-color: #409eff;
}
.main {
  padding: 20px;
}
</style>
