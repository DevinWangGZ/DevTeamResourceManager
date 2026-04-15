<template>
  <div v-if="showBoard" class="announcement-board">
    <!-- 顶部标题栏 -->
    <div class="board-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><BellFilled /></el-icon>
        </div>
        <span class="header-title">系统公告</span>
        <el-badge v-if="urgentCount > 0" :value="urgentCount" type="danger" class="urgent-badge" />
      </div>
      <div class="header-right">
        <el-button
          v-if="isAdmin"
          type="primary"
          size="small"
          round
          @click="openCreateDialog"
          class="create-btn"
        >
          <el-icon><Plus /></el-icon>
          发布公告
        </el-button>
        <el-button
          v-if="isAdmin && hasInactive"
          size="small"
          round
          text
          @click="toggleShowAll"
          class="toggle-btn"
        >
          {{ showAll ? '只看启用' : '查看全部' }}
        </el-button>
      </div>
    </div>

    <!-- 公告列表 -->
    <div v-if="loading" class="board-loading">
      <el-skeleton :rows="2" animated />
    </div>

    <div v-else-if="displayList.length === 0" class="board-empty">
      <el-icon class="empty-icon"><Notification /></el-icon>
      <span>暂无公告</span>
    </div>

    <transition-group v-else name="ann-list" tag="div" class="ann-list">
      <div
        v-for="ann in displayList"
        :key="ann.id"
        class="ann-item"
        :class="[`priority-${ann.priority}`, { inactive: !ann.is_active }]"
      >
        <!-- 优先级色条 -->
        <div class="priority-bar" />

        <div class="ann-body">
          <div class="ann-top">
            <div class="ann-meta">
              <el-tag
                :type="priorityTagType(ann.priority)"
                size="small"
                effect="dark"
                round
                class="priority-tag"
              >
                {{ priorityLabel(ann.priority) }}
              </el-tag>
              <span class="ann-title">{{ ann.title }}</span>
              <el-tag v-if="!ann.is_active" type="info" size="small" effect="plain" round>
                已停用
              </el-tag>
            </div>
            <div v-if="isAdmin" class="ann-actions">
              <el-button link size="small" @click="openEditDialog(ann)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-popconfirm
                title="确认删除此公告？"
                confirm-button-text="删除"
                cancel-button-text="取消"
                confirm-button-type="danger"
                @confirm="handleDelete(ann.id)"
              >
                <template #reference>
                  <el-button link size="small" type="danger">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <div
            class="ann-content-wrap"
            :class="{ clickable: isLong(ann.content) }"
            @click="isLong(ann.content) && openDetail(ann)"
          >
            <p class="ann-content">{{ ann.content }}</p>
            <span v-if="isLong(ann.content)" class="expand-link">
              查看全文 <el-icon style="vertical-align: -2px; font-size: 12px"><ArrowRight /></el-icon>
            </span>
          </div>

          <div class="ann-footer">
            <div class="ann-author">
              <el-avatar :size="18" class="author-avatar">
                {{ (ann.author_name || '?').charAt(0).toUpperCase() }}
              </el-avatar>
              <span>{{ ann.author_name || '管理员' }}</span>
            </div>
            <span class="ann-time">{{ formatTime(ann.created_at) }}</span>
          </div>
        </div>
      </div>
    </transition-group>

    <!-- 全文查看弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="viewingAnn?.title"
      width="600px"
      class="ann-dialog ann-detail-dialog"
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-tag
            :type="priorityTagType(viewingAnn?.priority ?? 'normal')"
            size="small"
            effect="dark"
            round
            class="priority-tag"
          >
            {{ priorityLabel(viewingAnn?.priority ?? 'normal') }}
          </el-tag>
          <span class="detail-title">{{ viewingAnn?.title }}</span>
        </div>
      </template>

      <div class="detail-content">{{ viewingAnn?.content }}</div>

      <div class="detail-footer">
        <div class="ann-author">
          <el-avatar :size="20" class="author-avatar">
            {{ (viewingAnn?.author_name || '?').charAt(0).toUpperCase() }}
          </el-avatar>
          <span>{{ viewingAnn?.author_name || '管理员' }}</span>
        </div>
        <span class="ann-time">{{ viewingAnn ? formatTime(viewingAnn.created_at) : '' }}</span>
      </div>

      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 创建 / 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑公告' : '发布公告'"
      width="560px"
      destroy-on-close
      class="ann-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入公告标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="form.priority" class="priority-radio">
            <el-radio-button value="normal">
              <el-icon><InfoFilled /></el-icon> 普通
            </el-radio-button>
            <el-radio-button value="important">
              <el-icon><WarningFilled /></el-icon> 重要
            </el-radio-button>
            <el-radio-button value="urgent">
              <el-icon><CircleCloseFilled /></el-icon> 紧急
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="请输入公告内容"
            maxlength="2000"
            show-word-limit
            resize="none"
          />
        </el-form-item>

        <el-form-item label="立即启用">
          <el-switch v-model="form.is_active" />
          <span class="form-tip">关闭后所有用户不可见</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ editingId ? '保存修改' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  BellFilled,
  Plus,
  Edit,
  Delete,
  Notification,
  InfoFilled,
  WarningFilled,
  CircleCloseFilled,
  ArrowRight,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  type Announcement,
  type AnnouncementPriority,
} from '@/api/announcement'

const userStore = useUserStore()

const loading = ref(false)
const saving = ref(false)
const announcements = ref<Announcement[]>([])
const showAll = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

// 全文查看
const detailVisible = ref(false)
const viewingAnn = ref<Announcement | null>(null)

/** 内容超过此字符数视为"长文"，显示展开入口 */
const LONG_THRESHOLD = 80

const isLong = (content: string) => content.length > LONG_THRESHOLD

const openDetail = (ann: Announcement) => {
  viewingAnn.value = ann
  detailVisible.value = true
}
const formRef = ref<FormInstance>()

const isAdmin = computed(() =>
  userStore.hasAnyRole('system_admin')
)

const showBoard = computed(() =>
  // 有公告或管理员（需要管理入口）时显示
  announcements.value.length > 0 || isAdmin.value
)

const hasInactive = computed(() =>
  announcements.value.some(a => !a.is_active)
)

const urgentCount = computed(() =>
  announcements.value.filter(a => a.priority === 'urgent' && a.is_active).length
)

const displayList = computed(() => {
  if (showAll.value) return announcements.value
  return announcements.value.filter(a => a.is_active)
})

const form = reactive({
  title: '',
  content: '',
  priority: 'normal' as AnnouncementPriority,
  is_active: true,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }],
}

const priorityLabel = (p: AnnouncementPriority) => {
  return { normal: '普通', important: '重要', urgent: '紧急' }[p] ?? p
}

const priorityTagType = (p: AnnouncementPriority) => {
  return { normal: 'info', important: 'warning', urgent: 'danger' }[p] ?? 'info'
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffH = diffMs / 3_600_000
  if (diffH < 1) return `${Math.max(1, Math.floor(diffMs / 60_000))} 分钟前`
  if (diffH < 24) return `${Math.floor(diffH)} 小时前`
  if (diffH < 48) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const loadAnnouncements = async () => {
  loading.value = true
  try {
    const res = await getAnnouncements(isAdmin.value)
    announcements.value = res.items
  } catch {
    // 静默失败，不影响首页主体
  } finally {
    loading.value = false
  }
}

const toggleShowAll = () => {
  showAll.value = !showAll.value
}

const resetForm = () => {
  form.title = ''
  form.content = ''
  form.priority = 'normal'
  form.is_active = true
  editingId.value = null
}

const openCreateDialog = () => {
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (ann: Announcement) => {
  editingId.value = ann.id
  form.title = ann.title
  form.content = ann.content
  form.priority = ann.priority
  form.is_active = ann.is_active
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editingId.value) {
        await updateAnnouncement(editingId.value, { ...form })
        ElMessage.success('公告已更新')
      } else {
        await createAnnouncement({ ...form })
        ElMessage.success('公告发布成功')
      }
      dialogVisible.value = false
      await loadAnnouncements()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = async (id: number) => {
  try {
    await deleteAnnouncement(id)
    ElMessage.success('公告已删除')
    await loadAnnouncements()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(loadAnnouncements)
</script>

<style scoped>
/* ---- 外层容器 ---- */
.announcement-board {
  background: linear-gradient(135deg, #f0f4ff 0%, #fafbff 100%);
  border: 1px solid #e0e7ff;
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 40px;
  box-shadow: 0 4px 24px 0 rgba(99, 102, 241, 0.07);
}

/* ---- 顶部标题栏 ---- */
.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.5px;
}

.urgent-badge {
  margin-left: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.create-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 600;
}

.toggle-btn {
  color: #6b7280;
  font-size: 13px;
}

/* ---- 加载 / 空状态 ---- */
.board-loading {
  padding: 8px 0;
}

.board-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-size: 14px;
  padding: 8px 0;
}

.empty-icon {
  font-size: 18px;
}

/* ---- 公告列表 ---- */
.ann-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ann-item {
  display: flex;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s, transform 0.2s;
}

.ann-item:hover {
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.1);
  transform: translateX(2px);
}

.ann-item.inactive {
  opacity: 0.55;
}

/* 色条 */
.priority-bar {
  width: 4px;
  flex-shrink: 0;
  border-radius: 0;
}

.priority-normal .priority-bar {
  background: linear-gradient(180deg, #6b7280, #9ca3af);
}

.priority-important .priority-bar {
  background: linear-gradient(180deg, #f59e0b, #d97706);
}

.priority-urgent .priority-bar {
  background: linear-gradient(180deg, #ef4444, #dc2626);
}

/* 紧急公告额外高亮 */
.priority-urgent {
  background: linear-gradient(90deg, #fff5f5 0%, #fff 60%);
  border-color: #fecaca;
}

.priority-important {
  background: linear-gradient(90deg, #fffbeb 0%, #fff 60%);
  border-color: #fde68a;
}

/* ---- 公告主体 ---- */
.ann-body {
  flex: 1;
  padding: 12px 16px;
  min-width: 0;
}

.ann-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 6px;
}

.ann-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.priority-tag {
  flex-shrink: 0;
}

.ann-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ann-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.ann-item:hover .ann-actions {
  opacity: 1;
}

/* ---- 内容 & 页脚 ---- */
.ann-content-wrap {
  margin-bottom: 10px;
}

.ann-content-wrap.clickable {
  cursor: pointer;
}

.ann-content-wrap.clickable:hover .ann-content {
  color: #374151;
}

.ann-content {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.15s;
}

.expand-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  color: #667eea;
  margin-top: 4px;
  cursor: pointer;
  user-select: none;
  transition: color 0.15s;
}

.expand-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* ---- 全文弹窗 ---- */
.detail-dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.detail-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 60vh;
  overflow-y: auto;
  padding: 4px 2px;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.ann-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ann-author {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.author-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 10px;
  font-weight: 700;
}

.ann-time {
  font-size: 12px;
  color: #9ca3af;
}

/* ---- 表单提示 ---- */
.form-tip {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 10px;
}

.priority-radio {
  display: flex;
  gap: 8px;
}

/* ---- 过渡动画 ---- */
.ann-list-enter-active,
.ann-list-leave-active {
  transition: all 0.3s ease;
}

.ann-list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.ann-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* ---- 对话框 ---- */
.ann-dialog :deep(.el-dialog__header) {
  padding-bottom: 0;
}
</style>
