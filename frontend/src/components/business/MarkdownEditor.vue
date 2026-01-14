<template>
  <div class="markdown-editor-container">
    <MdEditor
      v-model="editorValue"
      :language="language"
      :preview="preview"
      :preview-theme="previewTheme"
      :code-theme="codeTheme"
      :toolbars="toolbars"
      :placeholder="placeholder"
      :height="height"
      :on-upload-img="handleUploadImg"
      @on-save="handleSave"
      @on-change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import MdEditor from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { uploadImage } from '@/api/upload'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: string
  placeholder?: string
  height?: string
  preview?: boolean
  language?: string
  previewTheme?: string
  codeTheme?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请输入Markdown内容...',
  height: '500px',
  preview: true,
  language: 'zh-CN',
  previewTheme: 'default',
  codeTheme: 'github',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'save'): void
}>()

const editorValue = ref(props.modelValue)

// 工具栏配置
const toolbars = [
  'bold',
  'underline',
  'italic',
  'strikeThrough',
  '-',
  'title',
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
  'catalog',
]

// 图片上传处理
const handleUploadImg = async (
  files: File[],
  callback: (urls: string[]) => void
) => {
  try {
    const uploadPromises = files.map(async (file) => {
      // 验证文件类型
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
      if (!allowedTypes.includes(file.type)) {
        throw new Error(`不支持的文件格式: ${file.type}`)
      }

      // 验证文件大小（5MB）
      const maxSize = 5 * 1024 * 1024
      if (file.size > maxSize) {
        throw new Error('图片大小不能超过5MB')
      }

      // 压缩图片（如果超过2MB）
      let uploadFile = file
      if (file.size > 2 * 1024 * 1024) {
        uploadFile = await compressImage(file)
      }

      // 上传图片
      const response = await uploadImage(uploadFile)
      // 如果返回的是相对路径，需要拼接baseURL
      let imageUrl = response.url
      if (imageUrl.startsWith('/')) {
        const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        imageUrl = `${baseURL}${imageUrl}`
      }
      return imageUrl
    })

    const urls = await Promise.all(uploadPromises)
    callback(urls)
    ElMessage.success('图片上传成功')
  } catch (error: any) {
    ElMessage.error(error.message || '图片上传失败')
    callback([])
  }
}

// 图片压缩
const compressImage = (file: File): Promise<File> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = (e) => {
      const img = new Image()
      img.src = e.target?.result as string
      img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('无法创建canvas上下文'))
          return
        }

        // 计算压缩后的尺寸（保持宽高比，最大宽度1920px）
        const maxWidth = 1920
        let width = img.width
        let height = img.height

        if (width > maxWidth) {
          height = (height * maxWidth) / width
          width = maxWidth
        }

        canvas.width = width
        canvas.height = height

        // 绘制图片
        ctx.drawImage(img, 0, 0, width, height)

        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const compressedFile = new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now(),
              })
              resolve(compressedFile)
            } else {
              reject(new Error('图片压缩失败'))
            }
          },
          file.type,
          0.8 // 质量0.8
        )
      }
      img.onerror = () => reject(new Error('图片加载失败'))
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
  })
}

// 保存处理
const handleSave = () => {
  emit('save')
}

// 内容变化处理
const handleChange = (value: string) => {
  editorValue.value = value
  emit('update:modelValue', value)
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== editorValue.value) {
      editorValue.value = newValue
    }
  }
)
</script>

<style scoped>
.markdown-editor-container {
  width: 100%;
}
</style>
