<template>
  <div class="article-create-container">
    <Breadcrumb />
    
    <el-card class="article-form-card">
      <template #header>
        <div class="card-header">
          <h2>{{ isEdit ? '编辑文章' : '创建文章' }}</h2>
          <div class="header-actions">
            <el-button @click="handleCancel">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">
              {{ isEdit ? '更新' : '发布' }}
            </el-button>
            <el-button v-if="!isEdit" @click="handleSaveDraft" :loading="saving">
              保存草稿
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入文章标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="分类" prop="category">
          <el-select
            v-model="form.category"
            placeholder="选择分类（可选）"
            clearable
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="cat in categories"
              :key="cat.name"
              :label="cat.name"
              :value="cat.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标签" prop="tags">
          <el-input
            v-model="form.tags"
            placeholder="输入标签，用逗号分隔（可选）"
            clearable
          />
          <div class="form-tip">例如：Vue,TypeScript,前端开发</div>
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <MarkdownEditor
            v-model="form.content"
            :height="'600px'"
            placeholder="请输入文章内容（支持Markdown格式）"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="form.is_published">
            立即发布（取消勾选将保存为草稿）
          </el-checkbox>
          <div class="form-tip">提示：草稿只有作者本人可以查看，发布后所有用户都可以查看</div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import MarkdownEditor from '@/components/business/MarkdownEditor.vue'
import {
  createArticle,
  updateArticle,
  getArticle,
  getCategories,
  type Article,
} from '@/api/article'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const saving = ref(false)
const categories = ref<Array<{ name: string; count: number }>>([])

const isEdit = computed(() => {
  return !!route.params.id
})

const form = reactive({
  title: '',
  content: '',
  category: '',
  tags: '',
  is_published: false,
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入文章标题', trigger: 'blur' },
    { max: 200, message: '标题长度不能超过200个字符', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入文章内容', trigger: 'blur' },
  ],
}

const loadCategories = async () => {
  try {
    const data = await getCategories()
    categories.value = data
  } catch (error: any) {
    console.error('加载分类失败:', error)
  }
}

const loadArticle = async () => {
  if (!isEdit.value) return
  
  try {
    const articleId = parseInt(route.params.id as string)
    const data = await getArticle(articleId)
    form.title = data.title
    form.content = data.content
    form.category = data.category || ''
    form.tags = data.tags || ''
    form.is_published = data.is_published
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载文章失败')
    router.push({ name: 'ArticleList' })
  }
}

const handleSave = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    saving.value = true
    try {
      if (isEdit.value) {
        const articleId = parseInt(route.params.id as string)
        await updateArticle(articleId, {
          ...form,
          is_published: true,
        })
        ElMessage.success('文章更新成功')
      } else {
        await createArticle({
          ...form,
          is_published: true,
        })
        ElMessage.success('文章发布成功')
      }
      router.push({ name: 'ArticleList' })
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

const handleSaveDraft = async () => {
  if (!formRef.value) return
  
  // 草稿只需要标题和内容
  if (!form.title.trim()) {
    ElMessage.warning('请输入文章标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请输入文章内容')
    return
  }
  
  saving.value = true
  try {
    await createArticle({
      ...form,
      is_published: false,
    })
    ElMessage.success('草稿保存成功')
    router.push({ name: 'ArticleList' })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  router.back()
}

onMounted(() => {
  loadCategories()
  if (isEdit.value) {
    loadArticle()
  }
})
</script>

<style scoped>
.article-create-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.article-form-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
