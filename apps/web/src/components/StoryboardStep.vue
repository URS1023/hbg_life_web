<script setup lang="ts">
import type { Job, Project } from '../types'
defineProps<{ project: Project | null; activeJob: Job | null }>()
const emit = defineEmits<{ generate: []; continue: [] }>()
</script>
<template>
  <section class="step-panel"><div class="panel-kicker"><span class="eyebrow">STEP 05 · STORYBOARD & PROMPTS</span><span class="saved-pill">真实音频后校准</span></div><div class="panel-intro compact"><h1>把文字变成<em>可生成的镜头。</em></h1><p>每个镜头都有对应旁白、画面动作、镜头运动和完整提示词。你可以先审阅语义，再开始批量生图。</p></div><div v-if="!(project?.brief?.shots?.length)" class="empty-state"><div class="empty-orbit">▦</div><h3>还没有分镜</h3><p>分镜会引用已经锁定的人物锚点，并在旁白生成后用真实时间校准。</p><button class="primary-button" :disabled="!!activeJob" @click="emit('generate')">{{ activeJob ? '正在拆分镜头…' : '生成分镜与提示词 →' }}</button></div><div v-else class="shot-list"><article v-for="(shot, index) in project.brief.shots" :key="shot.id" class="shot-card"><div class="shot-index">{{ String(index + 1).padStart(2, '0') }}</div><div class="shot-content"><div class="shot-head"><strong>{{ shot.cue }}</strong><span>{{ shot.motion }}</span></div><p>{{ shot.visual }}</p><small>{{ shot.prompt }}</small></div></article><button class="primary-button" @click="emit('continue')">确认分镜，进入图片生成 →</button></div></section>
</template>
