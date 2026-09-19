<script setup lang="ts">
import type { Project } from '../types'
defineProps<{ project: Project | null; step: string; title: string; description: string; icon: string }>()
const emit = defineEmits<{ run: [] }>()
</script>
<template><section class="step-panel coming-panel"><div class="panel-kicker"><span class="eyebrow">WORKFLOW · {{ step }}</span><span class="beta-pill">正在接入</span></div><div class="coming-hero"><div class="coming-icon">{{ icon }}</div><h1>{{ title }}</h1><p>{{ description }}</p><button class="primary-button" :disabled="!project" @click="emit('run')">让 AI 开始处理 →</button></div><div class="coming-list"><div><span>01</span><strong>保留项目版本</strong><small>每次生成都可以回退</small></div><div><span>02</span><strong>局部重做</strong><small>失败镜头不会影响已完成素材</small></div><div><span>03</span><strong>真实进度</strong><small>关闭网页后任务仍会继续</small></div></div></section>
</template>
