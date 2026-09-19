import { computed, readonly, shallowRef } from 'vue'
import { api } from '../api/client'
import type { Job, Project, StepId } from '../types'

export function useProjects() {
  const _projects = shallowRef<Project[]>([])
  const _jobs = shallowRef<Job[]>([])
  const selectedId = shallowRef<string | null>(null)
  const loading = shallowRef(false)
  const error = shallowRef('')
  const selectedProject = computed(() => _projects.value.find((item) => item.id === selectedId.value) ?? _projects.value[0] ?? null)
  const activeJob = computed(() => _jobs.value.find((job) => ['queued', 'running'].includes(job.status)) ?? null)

  async function load() {
    loading.value = true; error.value = ''
    try { _projects.value = await api.listProjects(); if (!selectedId.value && _projects.value[0]) selectedId.value = _projects.value[0].id; if (selectedId.value) await loadJobs(selectedId.value) }
    catch (cause) { error.value = cause instanceof Error ? cause.message : '项目加载失败' }
    finally { loading.value = false }
  }
  async function loadJobs(id: string) { _jobs.value = await api.listJobs(id) }
  async function create(input: { title: string; inputMode: 'keyword' | 'script'; orientation: 'landscape' | 'portrait'; sourceText: string }) {
    const project = await api.createProject({ title: input.title, input_mode: input.inputMode, orientation: input.orientation, source_text: input.sourceText })
    _projects.value = [project, ..._projects.value]; selectedId.value = project.id; _jobs.value = []; return project
  }
  async function update(project: Project, payload: { title?: string; step?: StepId; source_text?: string; script_text?: string; brief?: Record<string, unknown> }) {
    const next = await api.updateProject(project.id, payload); _projects.value = _projects.value.map((item) => item.id === next.id ? next : item); return next
  }
  async function startJob(kind: string) { if (!selectedProject.value) throw new Error('请先选择项目'); const job = await api.createJob(selectedProject.value.id, kind); _jobs.value = [job, ..._jobs.value]; return job }
  return { projects: readonly(_projects), jobs: readonly(_jobs), selectedId, selectedProject, activeJob, loading: readonly(loading), error: readonly(error), load, loadJobs, create, update, startJob }
}
