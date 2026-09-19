<script setup lang="ts">
import type { Project, StepId } from '../types'
const props = defineProps<{ project: Project | null }>()
const emit = defineEmits<{ select: [step: StepId] }>()
const steps: Array<{ id: StepId; label: string; caption: string }> = [
  { id: 'input', label: '创作输入', caption: '关键词或脚本' }, { id: 'planning', label: '故事规划', caption: '大纲与旁白稿' },
  { id: 'characters', label: '人物场景', caption: '角色与画风' }, { id: 'narration', label: '旁白节奏', caption: '音色与时间轴' },
  { id: 'storyboard', label: '分镜提示词', caption: '镜头与构图' }, { id: 'images', label: '图片生成', caption: '候选与选用' },
  { id: 'audio', label: '声音预览', caption: '配乐与混音' }, { id: 'export', label: '合成交付', caption: '质检与下载' },
]
const index = (id: StepId) => steps.findIndex((step) => step.id === id)
</script>

<template>
  <nav class="step-rail" aria-label="创作流程">
    <div class="rail-title"><span class="eyebrow">WORKFLOW</span><strong>创作流程</strong></div>
    <button v-for="(step, stepIndex) in steps" :key="step.id" class="step-item" :class="{ active: project?.step === step.id, done: project && index(project.step) > stepIndex }" @click="emit('select', step.id)">
      <span class="step-dot">{{ project && index(project.step) > stepIndex ? '✓' : String(stepIndex + 1).padStart(2, '0') }}</span>
      <span class="step-copy"><strong>{{ step.label }}</strong><small>{{ step.caption }}</small></span>
      <span v-if="project?.step === step.id" class="step-live">当前</span>
    </button>
    <div class="rail-note"><span class="pulse"></span><span>AI 助手在线<br><small>会保存每个版本</small></span></div>
  </nav>
</template>
