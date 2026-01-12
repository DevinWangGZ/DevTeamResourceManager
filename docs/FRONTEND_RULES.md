# 前端技术栈与开发规范

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：前端组

## 目录
- [整体架构](#整体架构)
- [核心框架与库](#核心框架与库)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [样式规范](#样式规范)
- [性能优化](#性能优化)
- [开发流程](#开发流程)
- [交互设计](#交互设计)

---

## 整体架构

- **架构模式**：单页应用（SPA）
- **开发模式**：前后端分离，通过RESTful API与后端通信
- **构建部署**：静态资源构建，通过Nginx/CDN分发

---

## 核心框架与库

### 主要框架
- **Vue 3.4+**：组合式API，`<script setup>`语法
- **TypeScript 5.3+**：强类型支持
- **Vite 5.0+**：构建工具与开发服务器

### UI与组件
- **Element Plus 2.4+**：主UI组件库
- **Vue Router 4.2+**：路由管理
- **Pinia 2.1+**：状态管理
- **Axios 1.6+**：HTTP客户端
- **ECharts 5.4+**：数据可视化图表
- **Day.js 1.11+**：日期时间处理
- **VueUse 10.0+**：常用组合式函数工具集

### 开发工具
- **ESLint 8.56+**：代码质量检查
- **Prettier 3.1+**：代码格式化
- **Vitest 1.0+**：单元测试框架
- **Vue Test Utils 2.4+**：Vue组件测试
- **Cypress 13.0+**：E2E测试（可选）

---

## 项目结构

```
src/
├── modules/              # 业务模块（按功能划分）
│   ├── auth/            # 认证模块
│   │   ├── components/  # 模块内组件
│   │   ├── composables/ # 模块内组合式函数
│   │   ├── types/       # 模块内类型定义
│   │   └── index.ts     # 模块入口
│   ├── dashboard/       # 工作台模块（开发/管理视角）
│   ├── task/            # 任务系统模块
│   ├── profile/          # 个人档案模块（技能/履历）
│   ├── admin/           # 管理后台模块
│   └── common/          # 公共业务模块
├── components/          # 全局公共组件
│   ├── ui/              # 基础UI组件（按钮、卡片等）
│   ├── business/        # 业务公共组件
│   └── layout/          # 布局组件
├── composables/         # 全局组合式函数
├── stores/              # Pinia store
├── router/              # 路由配置
├── api/                 # API接口层
│   ├── modules/         # 按模块划分的API
│   └── index.ts         # API实例和拦截器
├── types/               # 全局TypeScript类型定义
├── utils/               # 工具函数
├── assets/              # 静态资源
│   ├── styles/          # 全局样式
│   ├── icons/           # 图标资源
│   └── images/          # 图片资源
└── App.vue              # 根组件
```

### 目录说明

- **modules/**：按业务功能划分的模块，每个模块包含完整的业务逻辑
- **components/**：全局可复用的组件，按类型分类
- **composables/**：全局组合式函数，可在任何组件中使用
- **stores/**：Pinia状态管理，按模块划分store
- **api/**：API接口层，统一管理所有HTTP请求
- **types/**：全局TypeScript类型定义
- **utils/**：工具函数库

---

## 代码规范

### 组件开发

#### 组件命名
- **文件命名**：使用帕斯卡命名法，如`UserProfileCard.vue`
- **组件注册**：注册时使用帕斯卡命名
- **目录命名**：使用小写+连字符，如`user-profile/`

#### Props定义
使用TypeScript接口定义props，并使用`withDefaults`提供默认值：

```typescript
// 使用TypeScript接口定义props
interface Props {
  userId: number
  userName?: string
  isActive: boolean
}

const props = withDefaults(defineProps<Props>(), {
  userName: '匿名用户',
  isActive: false
})
```

#### Emits定义
使用TypeScript类型定义emits：

```typescript
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit', payload: SubmitPayload): void
}>()
```

#### 组合式API规范
- **优先使用**：`<script setup>`语法
- **响应式数据**：使用`ref`和`reactive`
- **计算属性**：使用`computed`
- **生命周期**：使用组合式API的生命周期钩子

#### 组件示例

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<{
  (e: 'update', value: number): void
}>()

const localCount = ref(props.count)

const displayText = computed(() => {
  return `${props.title}: ${localCount.value}`
})

const handleClick = () => {
  localCount.value++
  emit('update', localCount.value)
}
</script>

<template>
  <div class="component-wrapper">
    <h3>{{ displayText }}</h3>
    <button @click="handleClick">增加</button>
  </div>
</template>

<style scoped>
.component-wrapper {
  padding: 16px;
}
</style>
```

---

### 状态管理

#### Store组织
按模块划分store，使用Pinia的`defineStore`：

```typescript
// stores/user.ts
import { defineStore } from 'pinia'

interface UserInfo {
  id: number
  name: string
  email: string
}

interface UserState {
  userInfo: UserInfo | null
  token: string
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userInfo: null,
    token: ''
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.userInfo?.name || '游客'
  },
  
  actions: {
    async login(credentials: LoginCredentials) {
      // 登录逻辑
      const response = await authApi.login(credentials)
      this.token = response.token
      this.userInfo = response.userInfo
    },
    
    logout() {
      this.token = ''
      this.userInfo = null
    }
  }
})
```

#### Store命名规范
- **文件命名**：使用小写+连字符，如`user-store.ts`、`task-store.ts`
- **Store ID**：使用小写+连字符，与文件名保持一致
- **导出命名**：使用`use`前缀，如`useUserStore`

#### Store使用规范
- 在组件中使用`useStore()`获取store实例
- 使用`storeToRefs()`解构响应式状态
- Actions中可以使用`this`访问state和getters

---

### API层规范

#### 统一请求拦截

创建Axios实例，配置baseURL和拦截器：

```typescript
// api/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    
    // 根据业务状态码处理
    if (code === 200) {
      return data
    } else {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }
  },
  (error) => {
    // 统一错误处理
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，跳转登录
          break
        case 403:
          ElMessage.error('无权限访问')
          break
        case 404:
          ElMessage.error('资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(error.response.data?.message || '请求失败')
      }
    }
    return Promise.reject(error)
  }
)

export default request
```

#### 模块化API

按业务模块划分API文件，统一导出：

```typescript
// api/modules/task.ts
import request from '../request'
import type { Task, TaskQueryParams, TaskListResponse } from '@/types/task'

export const taskApi = {
  // 获取任务列表
  getTasks(params: TaskQueryParams) {
    return request.get<TaskListResponse>('/api/v1/tasks', { params })
  },
  
  // 获取任务详情
  getTaskById(id: number) {
    return request.get<Task>(`/api/v1/tasks/${id}`)
  },
  
  // 创建任务
  createTask(data: Partial<Task>) {
    return request.post<Task>('/api/v1/tasks', data)
  },
  
  // 更新任务
  updateTask(id: number, data: Partial<Task>) {
    return request.put<Task>(`/api/v1/tasks/${id}`, data)
  },
  
  // 删除任务
  deleteTask(id: number) {
    return request.delete(`/api/v1/tasks/${id}`)
  },
  
  // 认领任务
  claimTask(taskId: number) {
    return request.post(`/api/v1/tasks/${taskId}/claim`)
  },
  
  // 提交任务
  submitTask(taskId: number, data: { actualDays: number }) {
    return request.post(`/api/v1/tasks/${taskId}/submit`, data)
  },
  
  // 确认任务
  confirmTask(taskId: number) {
    return request.post(`/api/v1/tasks/${taskId}/confirm`)
  }
}
```

#### API命名规范
- **文件命名**：使用小写+连字符，如`task-api.ts`、`user-api.ts`
- **导出对象**：使用模块名+Api后缀，如`taskApi`、`userApi`
- **方法命名**：使用动词+名词，语义清晰，如`getTasks`、`claimTask`

---

## 样式规范

### CSS方案
- **作用域**：使用`<style scoped>`避免样式污染
- **CSS Modules**：复杂组件可使用CSS Modules
- **主题变量**：使用Element Plus主题变量，通过CSS变量覆盖

### 主题定制

通过CSS变量覆盖Element Plus主题：

```scss
// assets/styles/variables.scss
:root {
  // Element Plus主题变量覆盖
  --el-color-primary: #409eff;
  --el-color-success: #67c23a;
  --el-color-warning: #e6a23c;
  --el-color-danger: #f56c6c;
  
  // 自定义变量
  --app-sidebar-width: 240px;
  --app-header-height: 60px;
}
```

### 响应式设计

使用Element Plus的断点mixins：

```scss
// 使用Element Plus的断点
@use 'element-plus/theme-chalk/src/mixins/mixins' as *;

.container {
  width: 100%;
  padding: 20px;
  
  @include res(xs) {
    padding: 10px;
  }
  
  @include res(sm) {
    padding: 15px;
  }
  
  @include res(md) {
    padding: 20px;
  }
  
  @include res(lg) {
    padding: 24px;
  }
  
  @include res(xl) {
    padding: 28px;
  }
}
```

### 样式组织
- **全局样式**：放在`assets/styles/`目录
- **组件样式**：使用`<style scoped>`，放在组件内部
- **工具类**：使用Tailwind CSS或自定义工具类（可选）

---

## 性能优化

### 组件懒加载

路由组件使用动态import：

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/task-market',
    name: 'TaskMarket',
    component: () => import('@/modules/task/views/TaskMarket.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/modules/dashboard/views/Dashboard.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

### 图片懒加载

使用v-lazy指令（需要安装vue-lazyload）：

```vue
<template>
  <img v-lazy="imageUrl" alt="描述" />
</template>
```

或使用原生loading属性：

```vue
<template>
  <img :src="imageUrl" loading="lazy" alt="描述" />
</template>
```

### 代码分割

Vite会自动进行代码分割：
- 路由级别的代码分割（动态import）
- 第三方库自动分割
- 公共代码提取

### API缓存

对频繁请求的数据使用Pinia缓存：

```typescript
// stores/task.ts
export const useTaskStore = defineStore('task', {
  state: () => ({
    taskList: [] as Task[],
    lastFetchTime: 0,
    cacheDuration: 5 * 60 * 1000 // 5分钟
  }),
  
  actions: {
    async fetchTasks(force = false) {
      const now = Date.now()
      
      // 检查缓存是否有效
      if (!force && this.lastFetchTime && (now - this.lastFetchTime) < this.cacheDuration) {
        return this.taskList
      }
      
      const tasks = await taskApi.getTasks()
      this.taskList = tasks
      this.lastFetchTime = now
      return tasks
    }
  }
})
```

### 其他优化建议
- **虚拟滚动**：长列表使用虚拟滚动（如`vue-virtual-scroller`）
- **防抖节流**：搜索、滚动等操作使用防抖节流
- **预加载**：关键资源预加载
- **CDN加速**：静态资源使用CDN

---

## 开发流程

### 环境变量

创建`.env.development`、`.env.production`等文件：

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=DevTeam Manager (开发环境)
VITE_APP_ENV=development
```

```env
# .env.production
VITE_API_BASE_URL=https://api.example.com
VITE_APP_TITLE=DevTeam Manager
VITE_APP_ENV=production
```

### 开发命令

在`package.json`中配置：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "build:prod": "vue-tsc && vite build --mode production",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "lint:check": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts",
    "format": "prettier --write \"src/**/*.{js,ts,vue,json,css,scss,md}\"",
    "test:unit": "vitest",
    "test:e2e": "cypress run"
  }
}
```

### Git工作流
- **分支命名**：`feature/xxx`、`bugfix/xxx`、`hotfix/xxx`
- **提交规范**：使用Conventional Commits规范
- **代码审查**：所有代码必须经过Code Review

---

## 交互设计

### 操作反馈
- **加载状态**：使用Element Plus的`loading`指令或`ElLoading`
- **成功提示**：使用`ElMessage.success()`
- **错误提示**：使用`ElMessage.error()`，错误信息要友好
- **确认对话框**：关键操作使用`ElMessageBox.confirm()`

### 用户体验
- **表单验证**：使用Element Plus的表单验证，提供即时反馈
- **快捷键**：支持常用快捷键操作
- **响应式**：适配不同屏幕尺寸
- **无障碍**：考虑无障碍访问（ARIA标签等）

### 错误处理
- **网络错误**：友好的错误提示，提供重试机制
- **表单错误**：字段级错误提示，指明修正方向
- **权限错误**：提示无权限，引导用户联系管理员

---

## 更新日志

| 版本 | 日期 | 更新内容 | 负责人 |
|------|------|----------|--------|
| v1.0 | 2024-05 | 初始版本，制定前端开发规范 | 前端组 |

---

**文档维护**：本文档随前端技术栈发展持续更新，重大变更需团队评审。
