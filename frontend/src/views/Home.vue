<template>
  <div class="home-container">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <h1>DevTeam Manager</h1>
          <div class="user-info" v-if="userStore.userInfo">
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
                      <div>角色: {{ getRoleName(userStore.userInfo.role) }}</div>
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
          <h2>欢迎使用 DevTeam Manager</h2>
          <p v-if="userStore.userInfo">
            你好，{{ userStore.userInfo.full_name || userStore.userInfo.username }}！
          </p>
          <p>开发人员管理工具</p>
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="goToTasks">
              <el-icon><List /></el-icon>
              任务管理
            </el-button>
            <el-button type="success" size="large" @click="goToProfile">
              <el-icon><User /></el-icon>
              个人档案
            </el-button>
            <el-button type="info" size="large" @click="goToWorkload">
              <el-icon><DataAnalysis /></el-icon>
              工作量统计
            </el-button>
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
import { User, ArrowDown, List } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const getRoleName = (role: string) => {
  const roleMap: Record<string, string> = {
    developer: '开发人员',
    project_manager: '项目经理',
    development_lead: '开发组长',
    system_admin: '系统管理员',
  }
  return roleMap[role] || role
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
  text-align: center;
  padding: 40px 20px;
}

.welcome-content h2 {
  margin-bottom: 20px;
  color: #333;
}

.welcome-content p {
  margin: 10px 0;
  color: #666;
  font-size: 16px;
}

.quick-actions {
  margin-top: 30px;
}
</style>
