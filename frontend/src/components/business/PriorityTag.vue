<template>
  <el-tag
    :color="tagColor"
    :style="{ color: '#fff', borderColor: tagColor, fontWeight: 'bold' }"
    size="small"
    :effect="effect"
  >
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TaskPriority } from '@/api/task'

const props = withDefaults(defineProps<{
  priority: TaskPriority | string
  showLabel?: boolean
  effect?: 'dark' | 'light' | 'plain'
}>(), {
  showLabel: true,
  effect: 'dark',
})

const PRIORITY_CONFIG: Record<string, { color: string; text: string }> = {
  P0: { color: '#F56C6C', text: 'P0 最紧急' },
  P1: { color: '#E6A23C', text: 'P1 较紧急' },
  P2: { color: '#909399', text: 'P2 常规' },
}

const tagColor = computed(() => PRIORITY_CONFIG[props.priority]?.color ?? '#909399')
const label = computed(() =>
  props.showLabel
    ? (PRIORITY_CONFIG[props.priority]?.text ?? props.priority)
    : props.priority
)
</script>
