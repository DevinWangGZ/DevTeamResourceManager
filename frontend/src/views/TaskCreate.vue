<template>
  <div class="task-create-container">
    <Breadcrumb />
    
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>创建任务</h2>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        v-loading="loading"
      >
        <!-- 基本信息 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务标题" prop="title">
              <el-input
                v-model="form.title"
                placeholder="请输入任务标题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属项目" prop="project_id">
              <el-select
                v-model="form.project_id"
                placeholder="请选择项目"
                filterable
                clearable
                style="width: 100%"
                :loading="projectLoading"
              >
                <el-option
                  v-for="project in projectList"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="拟投入人天" prop="estimated_man_days">
              <el-input-number
                v-model="form.estimated_man_days"
                :min="0"
                :precision="2"
                style="width: 100%"
                placeholder="请输入拟投入人天"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="所需技能" prop="required_skills">
              <el-input
                v-model="form.required_skills"
                placeholder="请输入所需技能（逗号分隔）"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="截止时间" prop="deadline">
              <el-date-picker
                v-model="form.deadline"
                type="date"
                placeholder="选择截止时间"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 任务描述 -->
        <el-form-item label="任务描述" prop="description">
          <MarkdownEditor
            v-model="form.description"
            placeholder="请输入任务描述，支持Markdown格式..."
            height="500px"
            @save="handleSaveDraft"
          />
        </el-form-item>
      </el-form>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button @click="handleSaveDraft">保存草稿</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          创建任务
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import MarkdownEditor from '@/components/business/MarkdownEditor.vue'
import { createTask, type TaskCreate } from '@/api/task'
import { getProjects, type Project } from '@/api/project'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const projectLoading = ref(false)
const formRef = ref<FormInstance>()
const projectList = ref<Project[]>([])

const form = reactive<TaskCreate>({
  title: '',
  description: '',
  project_id: undefined,
  estimated_man_days: 0,
  required_skills: '',
  deadline: undefined,
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 1, max: 200, message: '任务标题长度在1到200个字符', trigger: 'blur' },
  ],
  estimated_man_days: [
    { required: true, message: '请输入拟投入人天', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '拟投入人天必须大于0', trigger: 'blur' },
  ],
  deadline: [
    {
      validator: (rule, value, callback) => {
        if (value) {
          const deadline = new Date(value)
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          if (deadline < today) {
            callback(new Error('截止时间必须是未来日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 自动保存定时器
let autoSaveTimer: number | null = null

// 加载项目列表
const loadProjects = async () => {
  projectLoading.value = true
  try {
    const result = await getProjects({ limit: 1000 })
    projectList.value = result.items
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载项目列表失败')
  } finally {
    projectLoading.value = false
  }
}

// 保存草稿
const handleSaveDraft = () => {
  const draft = {
    title: form.title,
    description: form.description,
    project_id: form.project_id,
    estimated_man_days: form.estimated_man_days,
    required_skills: form.required_skills,
    deadline: form.deadline,
    savedAt: new Date().toISOString(),
  }
  localStorage.setItem('task_draft', JSON.stringify(draft))
  ElMessage.success('草稿已保存')
}

// 加载草稿
const loadDraft = () => {
  try {
    const draftStr = localStorage.getItem('task_draft')
    if (draftStr) {
      const draft = JSON.parse(draftStr)
      // 询问是否加载草稿
      ElMessageBox.confirm('检测到未保存的草稿，是否加载？', '提示', {
        confirmButtonText: '加载',
        cancelButtonText: '忽略',
        type: 'info',
      })
        .then(() => {
          Object.assign(form, {
            title: draft.title || '',
            description: draft.description || '',
            project_id: draft.project_id,
            estimated_man_days: draft.estimated_man_days || 0,
            required_skills: draft.required_skills || '',
            deadline: draft.deadline,
          })
        })
        .catch(() => {
          // 用户选择忽略，清除草稿
          localStorage.removeItem('task_draft')
        })
    }
  } catch (error) {
    console.error('加载草稿失败:', error)
  }
}

// 清除草稿
const clearDraft = () => {
  localStorage.removeItem('task_draft')
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await createTask(form)
        ElMessage.success('任务创建成功')
        clearDraft()
        // 跳转到任务列表
        router.push('/tasks')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建任务失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 取消
const handleCancel = () => {
  ElMessageBox.confirm('确定要离开吗？未保存的内容将丢失。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      clearDraft()
      router.push('/tasks')
    })
    .catch(() => {
      // 用户取消
    })
}

// 启动自动保存
const startAutoSave = () => {
  autoSaveTimer = window.setInterval(() => {
    if (form.title || form.description) {
      handleSaveDraft()
    }
  }, 30000) // 每30秒自动保存
}

// 停止自动保存
const stopAutoSave = () => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
    autoSaveTimer = null
  }
}

onMounted(() => {
  loadProjects()
  loadDraft()
  startAutoSave()
})

onBeforeUnmount(() => {
  stopAutoSave()
})
</script>

<style scoped>
.task-create-container {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}
</style>
