<script setup lang="ts">
import type { Project } from '../types'
defineProps<{ projects: readonly Project[]; selectedId: string | null }>()
const emit = defineEmits<{ select: [id: string] }>()
</script>
<template>
  <aside class="project-list">
    <div class="list-heading"><div><span class="eyebrow">MY STUDIO</span><strong>我的项目</strong></div><span class="count">{{ projects.length }}</span></div>
    <button v-if="projects.length === 0" class="empty-project" @click="emit('select', '')">创建你的第一个视频</button>
    <button v-for="project in projects" :key="project.id" class="project-card" :class="{ selected: selectedId === project.id }" @click="emit('select', project.id)">
      <span class="project-thumb" :class="project.orientation"><span>{{ project.title.slice(0, 1) }}</span></span>
      <span class="project-meta"><strong>{{ project.title }}</strong><small>{{ project.inputMode === 'keyword' ? '关键词创作' : '已有脚本' }} · {{ project.step }}</small></span>
      <span class="project-status" :class="project.status">{{ project.status === 'ready' ? '已完成' : '草稿' }}</span>
    </button>
  </aside>
</template>
