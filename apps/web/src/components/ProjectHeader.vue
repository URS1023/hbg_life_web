<script setup lang="ts">
import type { Project } from '../types'
defineProps<{ project: Project | null; connected: boolean }>()
const emit = defineEmits<{ newProject: []; refresh: [] }>()
</script>
<template>
  <header class="topbar"><div class="brand"><span class="brand-mark">H</span><span><strong>HBG LIFE</strong><small>AI VIDEO STUDIO</small></span></div><div class="topbar-project"><span class="status-dot" :class="{ off: !connected }"></span>{{ connected ? '本地工作区已连接' : '正在连接工作区' }}<span class="slash">/</span><strong>{{ project?.title ?? '准备开始创作' }}</strong></div><div class="topbar-actions"><button class="icon-button" title="刷新" @click="emit('refresh')">↻</button><button class="secondary-button" @click="emit('newProject')">＋ 新建项目</button><div class="avatar">演</div></div></header>
</template>
