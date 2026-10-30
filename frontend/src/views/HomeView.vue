<template>
  <el-card>
    <h2>欢迎，{{ displayName }} 👋</h2>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="用户名">{{ store.user?.username }}</el-descriptions-item>
      <el-descriptions-item label="昵称">{{ store.user?.nickname || '-' }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ store.user?.email }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ store.user?.role_code }}</el-descriptions-item>
      <el-descriptions-item label="注册时间">{{ store.user?.created_at?.replace('T', ' ') }}</el-descriptions-item>
    </el-descriptions>
    <el-alert
      class="tip"
      type="info"
      :closable="false"
      title="阶段四交付：登录注册 + 主布局 + 路由守卫"
      description="分类管理与知识条目页面将在阶段五实现；知识门户将在阶段六实现。"
    />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const displayName = computed(() => store.user?.nickname || store.user?.username || '用户')
</script>

<style scoped>
.tip {
  margin-top: 20px;
}
</style>
