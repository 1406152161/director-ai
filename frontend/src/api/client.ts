/**
 * @author zhangzhihao
 */
const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ProjectCreatePayload {
  story: string;
  style: string;
  duration: number;
  aspect_ratio: string;
}

export interface ShotResponse {
  id: string;
  index: number;
  scene_cn: string;
  image_prompt_en: string;
  motion_prompt_en: string;
  narration_cn: string;
  duration: number;
  image_url: string | null;
  video_url: string | null;
  audio_url: string | null;
  clip_url: string | null;
  clip_status: string;
  status: string;
}

export interface AssetResponse {
  id: string;
  asset_type: string;
  asset_key: string;
  name_cn: string;
  description_en: string;
  image_url: string | null;
  status: string;
}

export interface ProjectResponse {
  id: string;
  story: string;
  style: string;
  duration: number;
  aspect_ratio: string;
  status: string;
  progress: number;
  title: string | null;
  error: string | null;
  output_url: string | null;
  created_at: string | null;
  shots: ShotResponse[];
  assets: AssetResponse[];
}

export interface ProjectListItem {
  id: string;
  story: string;
  style: string;
  duration: number;
  aspect_ratio: string;
  status: string;
  progress: number;
  title: string | null;
  created_at: string | null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health');
}

export async function createProject(payload: ProjectCreatePayload): Promise<ProjectResponse> {
  return request<ProjectResponse>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchProject(projectId: string): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/api/projects/${projectId}`);
}

export async function listProjects(): Promise<ProjectListItem[]> {
  return request<ProjectListItem[]>('/api/projects');
}
