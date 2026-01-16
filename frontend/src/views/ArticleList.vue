<template>
  <div class="article-list-container">
    <Breadcrumb />
    
    <el-card class="page-header">
      <div class="header-content">
        <h1>知识分享</h1>
        <div class="header-actions">
          <el-button v-if="userStore.userInfo" @click="goToMyArticles">
            <el-icon><User /></el-icon>
            我的文章
          </el-button>
          <el-button type="primary" @click="goToCreate" v-if="userStore.userInfo">
            <el-icon><Plus /></el-icon>
            写文章
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索标题或内容"
            clearable
            @keyup.enter="handleSearch"
            style="width: 250px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="filterForm.category"
            placeholder="选择分类"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="cat in categories"
              :key="cat.name"
              :label="`${cat.name} (${cat.count})`"
              :value="cat.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="filterForm.tag"
            placeholder="选择标签"
            clearable
            filterable
            style="width: 150px"
          >
            <el-option
              v-for="tag in tags"
              :key="tag.name"
              :label="`${tag.name} (${tag.count})`"
              :value="tag.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文章列表 -->
    <el-card class="article-list-card" v-loading="loading">
      <div v-if="articles.length === 0" class="empty-state">
        <el-empty description="暂无文章" :image-size="120" />
      </div>
      <div v-else>
        <div
          v-for="article in articles"
          :key="article.id"
          class="article-item"
          @click="goToDetail(article.id)"
        >
          <div class="article-header">
            <h3 class="article-title">{{ article.title }}</h3>
            <div class="article-meta">
              <el-tag v-if="article.category" size="small" type="info">
                {{ article.category }}
              </el-tag>
              <el-tag v-if="!article.is_published" size="small" type="warning">
                草稿
              </el-tag>
            </div>
          </div>
          <div class="article-content">
            <p>{{ truncateContent(article.content) }}</p>
          </div>
          <div class="article-footer">
            <div class="article-info">
              <span class="author">
                <el-icon><User /></el-icon>
                {{ article.author_full_name || article.author_name || '未知' }}
              </span>
              <span class="date">
                <el-icon><Calendar /></el-icon>
                {{ formatDate(article.created_at) }}
              </span>
              <span class="views">
                <el-icon><View /></el-icon>
                {{ article.view_count }} 次浏览
              </span>
            </div>
            <div class="article-tags" v-if="article.tags">
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
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search, User, Calendar, View, Document } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import { useUserStore } from '@/stores/user'
import {
  getArticles,
  getCategories,
  getTags,
  type Article,
  type Category,
  type Tag,
} from '@/api/article'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const articles = ref<Article[]>([])
const total = ref(0)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const filterForm = reactive({
  keyword: '',
  category: '',
  tag: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
})

const loadCategories = async () => {
  try {
    const data = await getCategories()
    categories.value = data
  } catch (error: any) {
    console.error('加载分类失败:', error)
  }
}

const loadTags = async () => {
  try {
    const data = await getTags()
    tags.value = data
  } catch (error: any) {
    console.error('加载标签失败:', error)
  }
}

const loadArticles = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    
    // 如果URL中有my=true参数，且用户已登录，显示当前用户的文章（包括草稿）
    if (route.query.my === 'true' && userStore.userInfo) {
      params.author_id = userStore.userInfo.id
      // 不限制is_published，显示所有文章（包括草稿）
    } else {
      // 否则只显示已发布的文章
      params.is_published = true
    }
    
    if (filterForm.keyword) {
      params.keyword = filterForm.keyword
    }
    if (filterForm.category) {
      params.category = filterForm.category
    }
    if (filterForm.tag) {
      params.tag = filterForm.tag
    }
    const data = await getArticles(params)
    articles.value = data.items
    total.value = data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载文章列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadArticles()
}

const handleReset = () => {
  filterForm.keyword = ''
  filterForm.category = ''
  filterForm.tag = ''
  pagination.page = 1
  loadArticles()
}

const handleSizeChange = () => {
  loadArticles()
}

const handlePageChange = () => {
  loadArticles()
}

const goToDetail = (articleId: number) => {
  router.push({ name: 'ArticleDetail', params: { id: articleId } })
}

const goToCreate = () => {
  router.push({ name: 'ArticleCreate' })
}

const truncateContent = (content: string, maxLength: number = 200) => {
  if (!content) return ''
  // 移除Markdown标记
  const plainText = content.replace(/[#*`\[\]!]/g, '').trim()
  if (plainText.length <= maxLength) return plainText
  return plainText.substring(0, maxLength) + '...'
}

const getTagsList = (tags?: string) => {
  if (!tags) return []
  return tags.split(',').map(t => t.trim()).filter(t => t).slice(0, 5)
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

onMounted(() => {
  loadArticles()
  loadCategories()
  loadTags()
})

// 监听路由变化
watch(() => route.query, () => {
  pagination.page = 1
  loadArticles()
}, { deep: true })
</script>

<style scoped>
.article-list-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.article-list-card {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.article-item {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.article-item:hover {
  background-color: #f5f7fa;
}

.article-item:last-child {
  border-bottom: none;
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.article-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.article-meta {
  display: flex;
  gap: 8px;
  margin-left: 15px;
}

.article-content {
  margin-bottom: 15px;
  color: #606266;
  line-height: 1.6;
}

.article-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #909399;
}

.article-info {
  display: flex;
  gap: 20px;
  align-items: center;
}

.article-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.article-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-item {
  margin: 0;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
