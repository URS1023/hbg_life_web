import type { Job, Project } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) }, ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(body.detail ?? `请求失败 (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; mode: string }>('/health'),
  listProjects: () => request<Project[]>('/projects'),
  createProject: (payload: { title: string; input_mode: 'keyword' | 'script'; orientation: 'landscape' | 'portrait'; source_text: string }) => request<Project>('/projects', { method: 'POST', body: JSON.stringify(payload) }),
  updateProject: (id: string, payload: Record<string, unknown>) => request<Project>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listJobs: (id: string) => request<Job[]>(`/projects/${id}/jobs`),
  createJob: (id: string, kind: string) => request<Job>(`/projects/${id}/jobs`, { method: 'POST', body: JSON.stringify({ kind }) }),
  cancelJob: (id: string) => request<Job>(`/jobs/${id}/cancel`, { method: 'POST' }),
}
