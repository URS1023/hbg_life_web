<script setup lang="ts">
import { computed, onMounted, onUnmounted, shallowRef } from 'vue'
import { api } from './api/client'
import { useProjects } from './composables/useProjects'
import type { StepId } from './types'
import ProjectHeader from './components/ProjectHeader.vue'
import ProjectList from './components/ProjectList.vue'
import StepRail from './components/StepRail.vue'
import InputStep from './components/InputStep.vue'
import PlanningStep from './components/PlanningStep.vue'
import CharactersStep from './components/CharactersStep.vue'
import StoryboardStep from './components/StoryboardStep.vue'
import ComingStep from './components/ComingStep.vue'
import JobPanel from './components/JobPanel.vue'

const { projects, jobs, selectedId, selectedProject, activeJob, error, load, loadJobs, create, update, startJob } = useProjects()
const connected = shallowRef(false)
const saving = shallowRef(false)
const currentStep = computed<StepId>(() => selectedProject.value?.step ?? 'input')
let pollTimer: number | undefined

async function refresh() { await load(); try { await api.health(); connected.value = true } catch { connected.value = false } }
async function selectProject(id: string) { if (!id) { selectedId.value = null; return } selectedId.value = id; await loadJobs(id) }
async function createProject(input: { title: string; inputMode: 'keyword' | 'script'; orientation: 'landscape' | 'portrait'; sourceText: string }) { await create(input) }
async function saveInput(text: string) { if (!selectedProject.value) return; saving.value = true; try { await update(selectedProject.value, { source_text: text, step: 'planning' }) } finally { saving.value = false } }
async function move(step: StepId) { if (selectedProject.value) await update(selectedProject.value, { step }) }
async function run(kind: string) { await startJob(kind); if (selectedProject.value) await loadJobs(selectedProject.value.id) }
async function handleGeneratePlan() { await run('plan') }
async function continuePlan() { await move('characters') }
async function saveScript(scriptText: string) { if (selectedProject.value) await update(selectedProject.value, { script_text: scriptText }) }
async function saveCharacter(character: { name: string; role: string; traits: string; style: string }) { if (selectedProject.value) await update(selectedProject.value, { brief: { ...selectedProject.value.brief, characters: [character] } }) ; await move('narration') }
async function continueStoryboard() { await move('images') }
onMounted(async () => { await refresh(); pollTimer = window.setInterval(async () => { if (selectedProject.value) await load() }, 1000) })
onUnmounted(() => { if (pollTimer) window.clearInterval(pollTimer) })
</script>

<template><div class="app-shell"><ProjectHeader :project="selectedProject" :connected="connected" @new-project="selectedId = null" @refresh="refresh" /><div class="workspace"><ProjectList :projects="projects" :selected-id="selectedId" @select="selectProject" /><StepRail :project="selectedProject" @select="move" /><main class="main-content"><div v-if="error" class="error-banner">{{ error }}</div><InputStep v-if="currentStep === 'input'" :project="selectedProject" :saving="saving" @create="createProject" @save="saveInput" /><PlanningStep v-else-if="currentStep === 'planning'" :project="selectedProject" :active-job="activeJob" @generate="handleGeneratePlan" @save="saveScript" @continue="continuePlan" /><CharactersStep v-else-if="currentStep === 'characters'" :project="selectedProject" @save="saveCharacter" /><ComingStep v-else-if="currentStep === 'narration'" :project="selectedProject" step="04" title="让故事拥有自己的声音。" description="选择音色并生成连续旁白，字幕和镜头时间会以真实音频为准。" icon="◒" @run="run('narration')" /><StoryboardStep v-else-if="currentStep === 'storyboard'" :project="selectedProject" :active-job="activeJob" @generate="run('storyboard')" @continue="continueStoryboard" /><ComingStep v-else-if="currentStep === 'images'" :project="selectedProject" step="06" title="让每个镜头有画面。" description="先生成少量样张，再批量生成并挑选最终使用的图片。" icon="✧" @run="run('images')" /><ComingStep v-else-if="currentStep === 'audio'" :project="selectedProject" step="07" title="把声音和画面放在一起。" description="加入配乐与音效，生成可以反复预览的完整时间线。" icon="♫" @run="run('narration')" /><ComingStep v-else :project="selectedProject" step="08" title="导出你的完整人生副本。" description="渲染、混音和质检会在后台完成，成功后保留可下载的项目版本。" icon="↗" @run="run('render')" /></main><JobPanel :jobs="jobs" /></div></div></template>
