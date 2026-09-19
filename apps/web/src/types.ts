export type StepId = 'input' | 'planning' | 'characters' | 'narration' | 'storyboard' | 'images' | 'audio' | 'export'

export interface Character { name: string; role: string; traits: string; style: string }
export interface Shot { id: string; cue: string; visual: string; motion: string; prompt: string }
export interface Brief { logline?: string; chapters?: readonly string[]; characters?: readonly Character[]; shots?: readonly Shot[]; narration?: { duration: number; voice: string }; images?: { count: number; selected: number } }
export interface Project { id: string; title: string; inputMode: 'keyword' | 'script'; orientation: 'landscape' | 'portrait'; step: StepId; status: string; sourceText: string; scriptText: string; brief: Brief; createdAt: string; updatedAt: string }
export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'
export interface Job { id: string; projectId: string; kind: string; status: JobStatus; progress: number; message: string; result: Record<string, unknown>; createdAt: string; updatedAt: string }
