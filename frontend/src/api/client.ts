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

export interface ProjectResponse {
  id: string;
  story: string;
  style: string;
  duration: number;
  aspect_ratio: string;
  status: string;
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

export async function listProjects(): Promise<ProjectResponse[]> {
  return request<ProjectResponse[]>('/api/projects');
}
