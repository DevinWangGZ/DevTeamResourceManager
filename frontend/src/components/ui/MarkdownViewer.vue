<template>
  <div class="markdown-viewer" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

interface Props {
  content: string
}

const props = defineProps<Props>()

// 配置marked
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.error('代码高亮失败:', err)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true, // 支持换行
  gfm: true, // GitHub风格Markdown
})

// 渲染Markdown为HTML
const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked(props.content)
})
</script>

<style scoped>
.markdown-viewer {
  line-height: 1.6;
  color: #333;
}

.markdown-viewer :deep(h1),
.markdown-viewer :deep(h2),
.markdown-viewer :deep(h3),
.markdown-viewer :deep(h4),
.markdown-viewer :deep(h5),
.markdown-viewer :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-viewer :deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-viewer :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-viewer :deep(h3) {
  font-size: 1.25em;
}

.markdown-viewer :deep(h4) {
  font-size: 1em;
}

.markdown-viewer :deep(h5) {
  font-size: 0.875em;
}

.markdown-viewer :deep(h6) {
  font-size: 0.85em;
  color: #6a737d;
}

.markdown-viewer :deep(p) {
  margin-bottom: 16px;
}

.markdown-viewer :deep(ul),
.markdown-viewer :deep(ol) {
  margin-bottom: 16px;
  padding-left: 2em;
}

.markdown-viewer :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-viewer :deep(blockquote) {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin-bottom: 16px;
}

.markdown-viewer :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
}

.markdown-viewer :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.markdown-viewer :deep(pre code) {
  display: inline;
  padding: 0;
  margin: 0;
  overflow: visible;
  background-color: transparent;
  border-radius: 0;
  word-wrap: normal;
}

.markdown-viewer :deep(table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
}

.markdown-viewer :deep(table th),
.markdown-viewer :deep(table td) {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-viewer :deep(table th) {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-viewer :deep(table tr:nth-child(2n)) {
  background-color: #f6f8fa;
}

.markdown-viewer :deep(img) {
  max-width: 100%;
  height: auto;
  margin-bottom: 16px;
  border-radius: 4px;
}

.markdown-viewer :deep(a) {
  color: #0366d6;
  text-decoration: none;
}

.markdown-viewer :deep(a:hover) {
  text-decoration: underline;
}

.markdown-viewer :deep(hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}
</style>
