<template>
  <div class="home-container">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <h1>DevTeam Manager</h1>
          <div class="user-info" v-if="userStore.userInfo">
            <MessageNotification />
            <el-dropdown @command="handleCommand">
              <span class="user-dropdown">
                <el-icon><User /></el-icon>
                {{ userStore.userInfo.username }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>
                    <div class="user-detail">
                      <div>角色: 
                        <template v-if="userStore.userInfo.role_codes && userStore.userInfo.role_codes.length > 0">
                          <span v-for="(roleCode, index) in userStore.userInfo.role_codes" :key="roleCode">
                            {{ getRoleName(roleCode) }}<span v-if="index < userStore.userInfo.role_codes!.length - 1">、</span>
                          </span>
                        </template>
                        <template v-else>
                          {{ getRoleName(userStore.userInfo.role) }}
                        </template>
                      </div>
                      <div v-if="userStore.userInfo.full_name">姓名: {{ userStore.userInfo.full_name }}</div>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main>
        <div class="welcome-content">
          <div class="slogan-section">
            <h1 class="slogan">数字驱动，智能协作</h1>
            <p class="subtitle" v-if="userStore.userInfo">
              你好，{{ userStore.userInfo.full_name || userStore.userInfo.username }}！
            </p>
            <p class="description">极简、透明、自助的开发者资源管理与协作平台</p>
          </div>
          <div class="quick-actions">
            <div 
              class="action-card" 
              @click="goToDashboard" 
              v-if="hasRole('developer')"
            >
              <div class="card-icon primary">
                <el-icon><Monitor /></el-icon>
              </div>
              <h3>个人工作台</h3>
              <p>查看任务、工作负荷和绩效数据</p>
            </div>
            <div 
              class="action-card" 
              @click="goToProjectManagerDashboard" 
              v-if="hasRole('project_manager')"
            >
              <div class="card-icon primary">
                <el-icon><Monitor /></el-icon>
              </div>
              <h3>项目仪表盘</h3>
              <p>项目概览、任务完成情况和产值统计</p>
            </div>
            <div 
              class="action-card" 
              @click="goToTeamDashboard" 
              v-if="hasRole('development_lead')"
            >
              <div class="card-icon primary">
                <el-icon><Monitor /></el-icon>
              </div>
              <h3>团队仪表盘</h3>
              <p>团队总览、成员负荷和任务完成率</p>
            </div>
            <div class="action-card" @click="goToTasks">
              <div class="card-icon primary">
                <el-icon><List /></el-icon>
              </div>
              <h3>任务管理</h3>
              <p>创建、发布和管理项目任务</p>
            </div>
            <div 
              class="action-card" 
              @click="goToMarketplace" 
              v-if="hasRole('developer')"
            >
              <div class="card-icon success">
                <el-icon><ShoppingBag /></el-icon>
              </div>
              <h3>任务集市</h3>
              <p>浏览和认领适合的任务</p>
            </div>
            <div class="action-card" @click="goToProfile">
              <div class="card-icon success">
                <el-icon><User /></el-icon>
              </div>
              <h3>个人档案</h3>
              <p>维护技能、履历和序列信息</p>
            </div>
            <div class="action-card" @click="goToWorkload">
              <div class="card-icon info">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <h3>工作量统计</h3>
              <p>查看工作量趋势和统计分析</p>
            </div>
            <div class="action-card" @click="goToProjects">
              <div class="card-icon warning">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <h3>项目管理</h3>
              <p>管理项目信息和产值数据</p>
            </div>
            <div class="action-card" @click="goToArticles">
              <div class="card-icon primary">
                <el-icon><Document /></el-icon>
              </div>
              <h3>知识分享</h3>
              <p>分享技术文章和知识沉淀</p>
            </div>
            <div 
              class="action-card" 
              @click="goToUserManagement" 
              v-if="hasRole('system_admin')"
            >
              <div class="card-icon danger">
                <el-icon><UserFilled /></el-icon>
              </div>
              <h3>用户管理</h3>
              <p>管理系统用户和权限</p>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, ArrowDown, List, DataAnalysis, Monitor, FolderOpened, ShoppingBag, Document, UserFilled } from '@element-plus/icons-vue'
import MessageNotification from '@/components/business/MessageNotification.vue'
import { onMounted, watch } from 'vue'

const router = useRouter()
const userStore = useUserStore()

// 监听用户信息变化，确保角色数据正确加载
watch(() => userStore.userInfo, (newInfo) => {
  if (newInfo) {
    console.log('用户信息更新:', {
      role: newInfo.role,
      role_codes: newInfo.role_codes,
    })
  }
}, { immediate: true })

onMounted(() => {
  // 确保用户信息已加载
  if (userStore.userInfo && !userStore.userInfo.role_codes) {
    userStore.fetchUserInfo()
  }
})

const getRoleName = (role: string) => {
  const roleMap: Record<string, string> = {
    developer: '开发人员',
    project_manager: '项目经理',
    development_lead: '开发组长',
    system_admin: '系统管理员',
  }
  return roleMap[role] || role
}

// 检查用户是否拥有指定角色
const hasRole = (roleCode: string): boolean => {
  if (!userStore.userInfo) return false
  
  // 优先使用 role_codes 数组（多角色系统）
  if (userStore.userInfo.role_codes && Array.isArray(userStore.userInfo.role_codes) && userStore.userInfo.role_codes.length > 0) {
    return userStore.userInfo.role_codes.includes(roleCode)
  }
  
  // 向后兼容：如果没有 role_codes，使用单个 role 字段
  if (userStore.userInfo.role) {
    return userStore.userInfo.role === roleCode
  }
  
  return false
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
  }
}

const goToTasks = () => {
  router.push('/tasks')
}

const goToProfile = () => {
  router.push('/profile')
}

const goToWorkload = () => {
  router.push('/workload')
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const goToProjectManagerDashboard = () => {
  router.push('/dashboard/project-manager')
}

const goToTeamDashboard = () => {
  router.push('/dashboard/team')
}

const goToProjects = () => {
  router.push('/projects')
}

const goToMarketplace = () => {
  router.push('/marketplace')
}

const goToArticles = () => {
  router.push({ name: 'ArticleList' })
}

const goToUserManagement = () => {
  router.push({ name: 'UserManagement' })
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
}

.header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-detail {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
}

.welcome-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 20px;
}

.slogan-section {
  text-align: center;
  margin-bottom: 60px;
}

.slogan {
  font-size: 42px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 20px;
  color: #4b5563;
  margin: 10px 0;
  font-weight: 500;
}

.description {
  font-size: 16px;
  color: #6b7280;
  margin: 10px 0 0 0;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-top: 40px;
}

.action-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-height: 200px;
  justify-content: center;
}

.action-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border-color: #d1d5db;
}

.action-card .card-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 32px;
  transition: transform 0.3s ease;
}

.action-card:hover .card-icon {
  transform: scale(1.1);
}

.card-icon.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-icon.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.card-icon.info {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.card-icon.warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.card-icon.danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.action-card h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.action-card p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .slogan {
    font-size: 32px;
  }
  
  .quick-actions {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .action-card {
    min-height: 160px;
    padding: 24px 20px;
  }
}
</style>
