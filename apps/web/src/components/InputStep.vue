<script setup lang="ts">
import { reactive, shallowRef } from 'vue'
import type { Project } from '../types'
const props = defineProps<{ project: Project | null; saving: boolean }>()
const emit = defineEmits<{ create: [input: { title: string; inputMode: 'keyword' | 'script'; orientation: 'landscape' | 'portrait'; sourceText: string }]; save: [sourceText: string] }>()
const mode = shallowRef<'keyword' | 'script'>(props.project?.inputMode ?? 'keyword')
const form = reactive({ title: props.project?.title ?? '', sourceText: props.project?.sourceText ?? '', orientation: props.project?.orientation ?? 'landscape' as 'landscape' | 'portrait' })
function submit() { if (!props.project) emit('create', { title: form.title || '未命名人生副本', inputMode: mode.value, orientation: form.orientation, sourceText: form.sourceText }); else emit('save', form.sourceText) }
</script>
<template>
  <section class="step-panel input-panel"><div class="panel-intro"><span class="eyebrow">STEP 01 · INPUT</span><h1>把一个想法，<em>交给故事。</em></h1><p>输入几个关键词，或者粘贴已经写好的脚本。AI 会把它整理成可以继续编辑的完整创作项目。</p></div>
    <div class="mode-tabs"><button :class="{ active: mode === 'keyword' }" @click="mode = 'keyword'">✦ 从关键词开始 <small>让 AI 帮你写</small></button><button :class="{ active: mode === 'script' }" @click="mode = 'script'">▤ 我已经有脚本 <small>保留我的原文</small></button></div>
    <label v-if="!project" class="field"><span>项目名称</span><input v-model="form.title" placeholder="例如：县城青年的第二人生" /></label>
    <label class="field"><span>{{ mode === 'keyword' ? '你的创作关键词' : '粘贴你的脚本' }}</span><textarea v-model="form.sourceText" :placeholder="mode === 'keyword' ? '例如：县城青年、外卖员、逆袭、温暖、第一人称' : '把完整脚本粘贴到这里，AI 会先保存原文，再开始分析。'" rows="6"></textarea><small class="field-hint">{{ form.sourceText.length }} / 50,000 字</small></label>
    <div class="format-row"><span class="field-label">画面比例</span><button class="format-option" :class="{ active: form.orientation === 'landscape' }" @click="form.orientation = 'landscape'"><span class="ratio landscape-ratio"></span><span><strong>横屏 16:9</strong><small>适合 YouTube、B 站</small></span></button><button class="format-option" :class="{ active: form.orientation === 'portrait' }" @click="form.orientation = 'portrait'"><span class="ratio portrait-ratio"></span><span><strong>竖屏 9:16</strong><small>适合抖音、短视频</small></span></button></div>
    <button class="primary-button wide" :disabled="saving || !form.sourceText.trim()" @click="submit()"><span v-if="saving" class="spinner"></span>{{ project ? '保存并继续' : '创建项目并开始' }} <span>→</span></button>
  </section>
</template>
