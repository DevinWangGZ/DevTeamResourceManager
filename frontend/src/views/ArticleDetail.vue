<template>
  <div class="article-detail-container">
    <Breadcrumb />
    
    <el-card v-loading="loading" class="article-card">
      <div v-if="article">
        <!-- 文章头部 -->
        <div class="article-header">
          <h1 class="article-title">{{ article.title }}</h1>
          <div class="article-meta">
            <div class="meta-item">
              <el-icon><User /></el-icon>
              <span>{{ article.author_full_name || article.author_name || '未知' }}</span>
            </div>
            <div class="meta-item">
              <el-icon><Calendar /></el-icon>
              <span>{{ formatDate(article.created_at) }}</span>
            </div>
            <div class="meta-item">
              <el-icon><View /></el-icon>
              <span>{{ article.view_count }} 次浏览</span>
            </div>
            <div class="meta-item" v-if="article.category">
              <el-tag type="info">{{ article.category }}</el-tag>
            </div>
            <div class="meta-item" v-if="article.tags">
              <el-tag
                v-for="tag in getTagsList(article.tags)"
                :key="tag"
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 操作按钮（仅作者可见） -->
        <div class="article-actions" v-if="canEdit">
          <el-button type="primary" @click="goToEdit">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
          <el-button v-if="!article.is_published" type="success" @click="handlePublish">
            <el-icon><Promotion /></el-icon>
            发布
          </el-button>
        </div>

        <el-divider />

        <!-- 文章内容 -->
        <div class="article-content">
          <MarkdownViewer :content="article.content" />
        </div>
      </div>
      <div v-else class="empty-state">
        <el-empty description="文章不存在或已被删除" :image-size="120" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Calendar, View, Edit, Delete, Promotion } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import MarkdownViewer from '@/components/ui/MarkdownViewer.vue'
import { getArticle, deleteArticle, updateArticle, type Article } from '@/api/article'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const article = ref<Article | null>(null)

const canEdit = computed(() => {
  if (!article.value || !userStore.userInfo) return false
  return article.value.author_id === userStore.userInfo.id
})

const loadArticle = async () => {
  loading.value = true
  try {
    const articleId = parseInt(route.params.id as string)
    const data = await getArticle(articleId)
    article.value = data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载文章失败')
    if (error.response?.status === 404) {
      article.value = null
    }
  } finally {
    loading.value = false
  }
}

const goToEdit = () => {
  if (article.value) {
    router.push({ name: 'ArticleEdit', params: { id: article.value.id } })
  }
}

const handleDelete = async () => {
  if (!article.value) return
  
  try {
    await ElMessageBox.confirm('确定要删除这篇文章吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await deleteArticle(article.value.id)
    ElMessage.success('删除成功')
    router.push({ name: 'ArticleList' })
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handlePublish = async () => {
  if (!article.value) return
  
  try {
    await ElMessageBox.confirm('确定要发布这篇文章吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    })
    
    await updateArticle(article.value.id, {
      is_published: true,
    })
    ElMessage.success('发布成功')
    loadArticle()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '发布失败')
    }
  }
}

const getTagsList = (tags?: string) => {
  if (!tags) return []
  return tags.split(',').map(t => t.trim()).filter(t => t)
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadArticle()
})
</script>

<style scoped>
.article-detail-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.article-card {
  margin-top: 20px;
}

.article-header {
  margin-bottom: 20px;
}

.article-title {
  margin: 0 0 15px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  font-size: 14px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-item {
  margin: 0;
}

.article-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.article-content {
  padding: 20px 0;
  min-height: 200px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}
</style>
