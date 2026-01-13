<template>
  <el-breadcrumb separator="/" class="breadcrumb-container">
    <el-breadcrumb-item :to="{ path: '/' }">
      <el-icon><HomeFilled /></el-icon>
      首页
    </el-breadcrumb-item>
    <el-breadcrumb-item v-for="item in items" :key="item.path" :to="item.path">
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled } from '@element-plus/icons-vue'

interface BreadcrumbItem {
  title: string
  path?: string
}

const route = useRoute()

const items = computed<BreadcrumbItem[]>(() => {
  const routeName = route.name as string
  const breadcrumbs: BreadcrumbItem[] = []

  // 根据路由名称添加面包屑
  switch (routeName) {
    case 'TaskList':
      breadcrumbs.push({ title: '任务管理' })
      break
    case 'TaskDetail':
      breadcrumbs.push(
        { title: '任务管理', path: '/tasks' },
        { title: '任务详情' }
      )
      break
    case 'Profile':
      breadcrumbs.push({ title: '个人档案' })
      break
    case 'WorkloadStatistics':
      breadcrumbs.push({ title: '工作量统计' })
      break
    default:
      // 如果没有匹配的路由，尝试从路由meta中获取
      if (route.meta?.title) {
        breadcrumbs.push({ title: route.meta.title as string })
      }
  }

  return breadcrumbs
})
</script>

<style scoped>
.breadcrumb-container {
  margin-bottom: 20px;
  padding: 10px 0;
}

.breadcrumb-container :deep(.el-breadcrumb__item) {
  display: flex;
  align-items: center;
}

.breadcrumb-container :deep(.el-icon) {
  margin-right: 4px;
}
</style>
