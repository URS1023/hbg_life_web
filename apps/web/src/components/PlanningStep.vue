<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import type { Job, Project } from '../types'
const props = defineProps<{ project: Project | null; activeJob: Job | null }>()
const emit = defineEmits<{ generate: []; save: [scriptText: string]; continue: [] }>()
const scriptText = shallowRef(props.project?.scriptText ?? '')
watch(() => props.project?.scriptText, (value) => { if (value !== undefined && value !== scriptText.value) scriptText.value = value }, { immediate: true })
</script>
<template>
  <section class="step-panel"><div class="panel-kicker"><span class="eyebrow">STEP 02 · STORY PLAN</span><span class="saved-pill">✓ 自动保存</span></div><div class="panel-intro compact"><h1>先确定故事的<em>骨架。</em></h1><p>AI 会把关键词扩展成故事方向、章节和旁白初稿。你可以逐段修改，再确认下一步。</p></div><div v-if="!project?.brief?.logline" class="empty-state"><div class="empty-orbit">✦</div><h3>故事规划还没有开始</h3><p>点击生成，AI 会先分析创作意图，再给出可编辑的故事结构。</p><button class="primary-button" :disabled="!!activeJob" @click="emit('generate')">{{ activeJob ? '正在规划…' : '生成故事规划 →' }}</button></div><div v-else class="plan-result"><div class="result-label">故事一句话</div><div class="logline">{{ project.brief.logline }}</div><div class="chapter-grid"><div v-for="(chapter, index) in (project.brief.chapters ?? [])" :key="chapter" class="chapter-card"><span>0{{ index + 1 }}</span><strong>{{ chapter }}</strong><small>章节节拍已识别</small></div></div><div class="script-preview"><div class="result-label">旁白稿初稿</div><textarea v-model="scriptText" rows="7"></textarea><button class="secondary-button save-script" @click="emit('save', scriptText)">保存旁白稿</button></div><button class="primary-button" @click="emit('continue')">确认规划，进入人物场景 →</button></div></section>
</template>
