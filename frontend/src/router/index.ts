import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/tasks',
    name: 'TaskList',
    component: () => import('@/views/TaskList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/views/TaskDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/workload',
    name: 'WorkloadStatistics',
    component: () => import('@/views/WorkloadStatistics.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'DeveloperDashboard',
    component: () => import('@/views/DeveloperDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard/project-manager',
    name: 'ProjectManagerDashboard',
    component: () => import('@/views/ProjectManagerDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard/team',
    name: 'TeamDashboard',
    component: () => import('@/views/TeamDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('@/views/ProjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/ProjectList.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn()

  // 如果路由需要认证且用户未登录，重定向到登录页
  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  // 如果已登录且访问登录页，根据角色重定向
  else if (to.name === 'Login' && isLoggedIn) {
    const userStore = useUserStore()
    const role = userStore.userInfo?.role
    // 开发人员跳转到工作台，其他角色跳转到首页
    if (role === 'developer') {
      next({ name: 'DeveloperDashboard' })
    } else {
      next({ name: 'Home' })
    }
  }
  else {
    next()
  }
})

export default router
