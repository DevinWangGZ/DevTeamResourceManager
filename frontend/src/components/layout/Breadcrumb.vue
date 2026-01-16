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
    case 'Home':
      breadcrumbs.push({ title: '首页' })
      break
    case 'DeveloperDashboard':
      breadcrumbs.push({ title: '个人工作台' })
      break
    case 'ProjectManagerDashboard':
      breadcrumbs.push({ title: '项目仪表盘' })
      break
    case 'TeamDashboard':
      breadcrumbs.push({ title: '团队管理仪表盘' })
      break
    case 'TeamCapabilityInsights':
      breadcrumbs.push({ title: '团队能力洞察' })
      break
    case 'TaskList':
      breadcrumbs.push({ title: '任务管理' })
      break
    case 'TaskMarketplace':
      breadcrumbs.push({ title: '任务集市' })
      break
    case 'MessageCenter':
      breadcrumbs.push({ title: '消息中心' })
      break
    case 'ArticleList':
      breadcrumbs.push({ title: '知识分享' })
      break
    case 'ArticleCreate':
      breadcrumbs.push(
        { title: '知识分享', path: '/articles' },
        { title: '创建文章' }
      )
      break
    case 'ArticleDetail':
      breadcrumbs.push(
        { title: '知识分享', path: '/articles' },
        { title: '文章详情' }
      )
      break
    case 'ArticleEdit':
      breadcrumbs.push(
        { title: '知识分享', path: '/articles' },
        { title: '编辑文章' }
      )
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
