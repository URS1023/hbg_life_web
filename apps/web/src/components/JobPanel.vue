<script setup lang="ts">
import type { Job } from '../types'
defineProps<{ jobs: readonly Job[] }>()
const emit = defineEmits<{ cancel: [id: string] }>()
const label = (kind: string) => ({ plan: '故事规划', storyboard: '分镜提示词', narration: '旁白与字幕', images: '图片生成', render: '视频合成' }[kind] ?? kind)
</script>
<template><aside class="job-panel"><div class="job-title"><span class="eyebrow">ACTIVITY</span><strong>任务动态</strong></div><div v-if="jobs.length === 0" class="job-empty">还没有后台任务</div><div v-for="job in jobs" :key="job.id" class="job-row"><div class="job-icon" :class="job.status">{{ job.status === 'succeeded' ? '✓' : job.status === 'failed' ? '!' : '·' }}</div><div class="job-copy"><strong>{{ label(job.kind) }}</strong><small>{{ job.message }}</small><div v-if="['queued', 'running'].includes(job.status)" class="progress"><span :style="{ width: `${job.progress}%` }"></span></div></div><button v-if="['queued', 'running'].includes(job.status)" class="job-cancel" @click="emit('cancel', job.id)">取消</button></div></aside></template>
