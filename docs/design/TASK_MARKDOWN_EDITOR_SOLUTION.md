# 任务描述Markdown编辑器技术方案

> **文档版本**：v1.0 | **创建日期**：2024-12 | **负责人**：技术组

## 一、技术选型

### 1.1 Markdown编辑器库选择

#### 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **@toast-ui/editor** | 功能完整、文档完善、支持图片上传 | 体积较大、Vue集成需要适配 | ⭐⭐⭐⭐ |
| **mavon-editor** | Vue专用、中文文档、功能完整 | 维护不够活跃、样式定制复杂 | ⭐⭐⭐ |
| **md-editor-v3** | Vue 3专用、TypeScript支持、轻量 | 功能相对简单、社区较小 | ⭐⭐⭐⭐ |
| **bytemd** | 轻量、可扩展、插件化 | 需要较多配置、文档较少 | ⭐⭐⭐ |
| **CodeMirror + Markdown-it** | 完全可控、高度定制 | 开发工作量大、需要自己实现 | ⭐⭐ |

#### 推荐方案：md-editor-v3

**选择理由**：
1. **Vue 3原生支持**：专为Vue 3设计，使用Composition API
2. **TypeScript支持**：完整的类型定义
3. **功能完整**：支持工具栏、实时预览、图片上传等
4. **轻量级**：体积相对较小
5. **活跃维护**：GitHub stars 1k+，持续更新
6. **中文友好**：支持中文界面

**安装**：
```bash
npm install md-editor-v3
```

---

### 1.2 图片上传方案

#### 方案选择

**方案1：直接上传到后端API**
- 优点：简单直接，数据可控
- 缺点：需要后端支持，增加服务器存储压力

**方案2：上传到对象存储（OSS）**
- 优点：减轻服务器压力，CDN加速
- 缺点：需要配置OSS服务，增加复杂度

**推荐方案：直接上传到后端API（初期）**

**理由**：
- 项目初期，图片数量不会太多
- 简化部署和运维
- 后续可以迁移到OSS

**后端API设计**：
```
POST /api/v1/upload/image
Content-Type: multipart/form-data

Response:
{
  "url": "https://example.com/uploads/image.jpg",
  "filename": "image.jpg",
  "size": 102400
}
```

---

### 1.3 Markdown渲染方案

**选择**：使用 `marked` + `highlight.js`

**理由**：
- `marked`：轻量、快速、功能完整
- `highlight.js`：代码高亮支持完善
- 两者配合使用，渲染效果好

**安装**：
```bash
npm install marked highlight.js
```

---

## 二、架构设计

### 2.1 组件结构

```
frontend/src/
├── views/
│   ├── TaskCreate.vue          # 任务创建页面（新建）
│   └── TaskEdit.vue            # 任务编辑页面（可选，可复用TaskCreate）
├── components/
│   ├── business/
│   │   ├── MarkdownEditor.vue  # Markdown编辑器组件（封装）
│   │   └── ImageUpload.vue     # 图片上传组件（可选）
│   └── ui/
│       └── MarkdownViewer.vue  # Markdown渲染组件（用于任务详情页）
└── api/
    ├── task.ts                 # 任务API（已有）
    └── upload.ts               # 图片上传API（新建）
```

---

### 2.2 数据流设计

```
用户输入
  ↓
MarkdownEditor组件
  ↓
md-editor-v3编辑器
  ↓
图片上传 → 后端API → 返回URL
  ↓
插入Markdown格式
  ↓
实时预览（marked渲染）
  ↓
表单提交 → 后端API
  ↓
保存到数据库（description字段存储Markdown）
```

---

### 2.3 状态管理

**使用Pinia Store（可选）**：
```typescript
// stores/taskEditor.ts
export const useTaskEditorStore = defineStore('taskEditor', {
  state: () => ({
    draft: null as TaskDraft | null,
    autoSaveTimer: null as number | null,
  }),
  actions: {
    saveDraft(data: TaskDraft) { ... },
    loadDraft() { ... },
    clearDraft() { ... },
  }
})
```

**或使用组件内状态**：
- 如果功能简单，可以直接在组件内使用 `ref` 管理状态

---

## 三、详细设计

### 3.1 MarkdownEditor组件设计

#### 3.1.1 组件接口

```typescript
interface MarkdownEditorProps {
  modelValue: string           // v-model绑定值
  placeholder?: string         // 占位符
  height?: string              // 编辑器高度
  preview?: boolean            // 是否显示预览
  toolbar?: boolean            // 是否显示工具栏
  uploadImage?: (file: File) => Promise<string>  // 图片上传函数
}

interface MarkdownEditorEmits {
  (e: 'update:modelValue', value: string): void
  (e: 'upload-image', file: File): void
}
```

#### 3.1.2 组件实现要点

1. **封装md-editor-v3**
   - 配置工具栏按钮
   - 配置图片上传回调
   - 配置预览选项

2. **图片上传集成**
   - 监听粘贴事件（Ctrl+V）
   - 监听拖拽事件
   - 调用上传API
   - 插入Markdown格式

3. **实时预览**
   - 使用md-editor-v3内置预览
   - 或使用marked自定义渲染

---

### 3.2 任务创建页面设计

#### 3.2.1 页面结构

```vue
<template>
  <div class="task-create-container">
    <Breadcrumb />
    
    <el-card>
      <template #header>
        <h2>创建任务</h2>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef">
        <!-- 基本信息 -->
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        
        <el-form-item label="所属项目" prop="project_id">
          <el-select v-model="form.project_id">
            ...
          </el-select>
        </el-form-item>
        
        <!-- 其他字段... -->
        
        <!-- 任务描述 -->
        <el-form-item label="任务描述" prop="description">
          <MarkdownEditor
            v-model="form.description"
            :upload-image="handleImageUpload"
            height="500px"
          />
        </el-form-item>
      </el-form>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="saveDraft">保存草稿</el-button>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">创建任务</el-button>
      </div>
    </el-card>
  </div>
</template>
```

#### 3.2.2 路由配置

```typescript
// router/index.ts
{
  path: '/tasks/create',
  name: 'TaskCreate',
  component: () => import('@/views/TaskCreate.vue'),
  meta: { requiresAuth: true }
}
```

---

### 3.3 图片上传API设计

#### 3.3.1 前端API

```typescript
// api/upload.ts
export interface ImageUploadResponse {
  url: string
  filename: string
  size: number
}

export function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post('/api/v1/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
```

#### 3.3.2 后端API

```python
# backend/app/api/v1/endpoints/upload.py
@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传图片"""
    # 验证文件类型
    # 验证文件大小
    # 保存文件
    # 返回URL
    pass
```

---

### 3.4 后端数据存储

#### 3.4.1 数据库字段

**当前设计**：
- `tasks.description` 字段类型为 `Text`
- 可以存储Markdown格式文本

**无需修改**：现有字段已支持存储Markdown内容

#### 3.4.2 图片存储

**方案1：存储在服务器文件系统**
- 路径：`backend/uploads/images/`
- URL：`/uploads/images/{filename}`

**方案2：存储在数据库（Base64）**
- 不推荐：数据库压力大

**推荐方案1**：存储在文件系统，后续可迁移到OSS

---

## 四、实现步骤

### 阶段1：基础功能（1-2天）

1. **安装依赖**
   ```bash
   npm install md-editor-v3 marked highlight.js
   ```

2. **创建MarkdownEditor组件**
   - 封装md-editor-v3
   - 配置基础功能
   - 测试编辑器

3. **创建任务创建页面**
   - 创建TaskCreate.vue
   - 集成MarkdownEditor组件
   - 配置路由

4. **修改任务列表页面**
   - 将"创建任务"按钮改为路由跳转
   - 移除创建任务弹窗

**验收**：
- [ ] 可以访问任务创建页面
- [ ] Markdown编辑器正常显示
- [ ] 可以输入和编辑Markdown内容

---

### 阶段2：图片上传功能（2-3天）

1. **后端图片上传API**
   - 创建upload.py端点
   - 实现文件验证和保存
   - 返回图片URL

2. **前端图片上传**
   - 创建upload.ts API
   - 在MarkdownEditor中集成上传
   - 支持粘贴、拖拽、点击上传

3. **图片上传优化**
   - 添加上传进度提示
   - 添加图片预览
   - 添加错误处理

**验收**：
- [ ] 可以上传图片
- [ ] 图片自动插入Markdown
- [ ] 上传进度和错误提示正常

---

### 阶段3：完善功能（1-2天）

1. **草稿保存功能**
   - 实现自动保存
   - 实现手动保存
   - 实现草稿加载

2. **任务详情页Markdown渲染**
   - 创建MarkdownViewer组件
   - 在TaskDetail.vue中使用
   - 配置代码高亮

3. **任务编辑功能**
   - 复用TaskCreate组件
   - 添加编辑模式
   - 加载已有内容

**验收**：
- [ ] 草稿保存功能正常
- [ ] 任务详情页Markdown渲染正常
- [ ] 任务编辑功能正常

---

### 阶段4：优化和测试（1天）

1. **性能优化**
   - 编辑器懒加载
   - 图片压缩优化
   - 预览性能优化

2. **用户体验优化**
   - 添加加载状态
   - 优化错误提示
   - 优化响应式布局

3. **测试**
   - 功能测试
   - 兼容性测试
   - 性能测试

**验收**：
- [ ] 所有功能正常
- [ ] 性能满足要求
- [ ] 兼容性良好

---

## 五、技术细节

### 5.1 md-editor-v3配置

```typescript
import MdEditor from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

// 配置
const editorConfig = {
  modelValue: markdownText,
  language: 'zh-CN',
  preview: true,
  previewTheme: 'default',
  codeTheme: 'github',
  toolbars: [
    'bold',
    'underline',
    'italic',
    '-',
    'title',
    'strikeThrough',
    'sub',
    'sup',
    'quote',
    'unorderedList',
    'orderedList',
    'task',
    '-',
    'codeRow',
    'code',
    'link',
    'image',
    'table',
    '-',
    'revoke',
    'next',
    'save',
    '=',
    'pageFullscreen',
    'fullscreen',
    'preview',
    'catalog'
  ],
  onUploadImg: async (files: File[]) => {
    // 上传图片
    const urls = await Promise.all(
      files.map(file => uploadImage(file))
    )
    return urls.map(res => res.url)
  }
}
```

---

### 5.2 图片上传实现

```typescript
const handleImageUpload = async (file: File): Promise<string> => {
  try {
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      throw new Error('不支持的图片格式')
    }
    
    // 验证文件大小（5MB）
    if (file.size > 5 * 1024 * 1024) {
      throw new Error('图片大小不能超过5MB')
    }
    
    // 压缩图片（如果超过2MB）
    let uploadFile = file
    if (file.size > 2 * 1024 * 1024) {
      uploadFile = await compressImage(file)
    }
    
    // 上传
    const response = await uploadImage(uploadFile)
    return response.url
  } catch (error) {
    ElMessage.error(error.message || '图片上传失败')
    throw error
  }
}
```

---

### 5.3 草稿保存实现

```typescript
// 使用localStorage保存草稿
const saveDraft = () => {
  const draft = {
    title: form.title,
    description: form.description,
    project_id: form.project_id,
    estimated_man_days: form.estimated_man_days,
    required_skills: form.required_skills,
    deadline: form.deadline,
    savedAt: new Date().toISOString()
  }
  localStorage.setItem('task_draft', JSON.stringify(draft))
  ElMessage.success('草稿已保存')
}

// 加载草稿
const loadDraft = () => {
  const draftStr = localStorage.getItem('task_draft')
  if (draftStr) {
    const draft = JSON.parse(draftStr)
    Object.assign(form, draft)
  }
}

// 自动保存（每30秒）
const autoSaveTimer = setInterval(() => {
  if (form.title || form.description) {
    saveDraft()
  }
}, 30000)
```

---

## 六、风险评估与应对

### 6.1 技术风险

**风险1：md-editor-v3不满足需求**
- **应对**：提前测试，如有问题考虑切换到其他库
- **备选方案**：@toast-ui/editor

**风险2：图片上传性能问题**
- **应对**：实现图片压缩，使用异步上传
- **优化**：后续迁移到OSS + CDN

**风险3：Markdown渲染安全问题**
- **应对**：使用安全的Markdown渲染库，转义HTML
- **验证**：进行XSS测试

### 6.2 进度风险

**风险1：开发时间估算不准**
- **应对**：分阶段实现，先实现核心功能
- **缓冲**：预留20%缓冲时间

**风险2：功能范围扩大**
- **应对**：严格控制功能范围，先实现MVP
- **原则**：核心功能优先，增强功能后续迭代

---

## 七、后续优化方向

### 7.1 功能增强

- 任务描述模板
- 任务描述历史版本
- 任务描述导出
- 协作编辑

### 7.2 性能优化

- 编辑器懒加载
- 图片CDN加速
- 预览虚拟滚动

### 7.3 用户体验

- 快捷键自定义
- 主题切换
- 全屏编辑模式

---

## 八、总结

### 8.1 技术栈

- **编辑器**：md-editor-v3
- **渲染**：marked + highlight.js
- **上传**：原生FormData + Axios
- **存储**：localStorage（草稿）+ 服务器文件系统（图片）

### 8.2 开发时间估算

- **阶段1**：1-2天（基础功能）
- **阶段2**：2-3天（图片上传）
- **阶段3**：1-2天（完善功能）
- **阶段4**：1天（优化测试）
- **总计**：5-8天

### 8.3 关键决策

1. **选择md-editor-v3**：Vue 3原生支持，功能完整
2. **图片上传到服务器**：简化初期实现，后续可迁移
3. **草稿使用localStorage**：简单高效，无需后端支持
4. **分阶段实现**：降低风险，快速迭代

---

**文档维护**：本文档随开发进展持续更新，技术选型变更需团队评审。
