<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Character, Project } from '../types'
const props = defineProps<{ project: Project | null }>()
const emit = defineEmits<{ save: [character: Character]; continue: [] }>()
const form = reactive<Character>({ name: '主角', role: '故事主视角', traits: '二十多岁，克制但有韧性，眼神清澈', style: '统一 HBG 漫画风，柔和颗粒，电影感光影' })
watch(() => props.project?.brief.characters, (characters) => { if (characters?.[0]) Object.assign(form, characters[0]) }, { immediate: true })
</script>
<template>
  <section class="step-panel"><div class="panel-kicker"><span class="eyebrow">STEP 03 · CHARACTER & SCENE</span><span class="saved-pill">✓ 项目隔离</span></div><div class="panel-intro compact"><h1>先让主角，<em>拥有一张脸。</em></h1><p>角色锚点会被复制到后面的提示词中，保证人物在不同镜头里保持同一个身份。</p></div><div class="character-layout"><div class="character-preview"><div class="portrait-orbit">◉</div><span class="eyebrow">IDENTITY ANCHOR</span><strong>{{ form.name }}</strong><small>{{ form.role }}</small><div class="anchor-tags"><span v-for="tag in form.traits.split('，').slice(0, 3)" :key="tag">{{ tag }}</span></div></div><div class="character-form"><label class="field"><span>角色名称</span><input v-model="form.name" /></label><label class="field"><span>剧情作用</span><input v-model="form.role" /></label><label class="field"><span>不可变特征</span><textarea v-model="form.traits" rows="3"></textarea></label><label class="field"><span>统一画风</span><textarea v-model="form.style" rows="3"></textarea></label><button class="primary-button wide" @click="emit('save', { ...form })">保存角色锚点并继续 <span>→</span></button></div></div></section>
</template>
