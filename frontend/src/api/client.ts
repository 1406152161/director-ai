/**
 * @author zhangzhihao
 */
import type {
  NovelBibleCharacter,
  NovelBibleForeshadowing,
  NovelBibleItem,
  NovelBibleOutlineItem,
  NovelBibleVolume,
} from '../utils/novelBible';
import { getStoredToken } from '../store/useAuthStore';

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
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    let message = `请求失败 (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string | { msg?: string }[] };
      if (typeof body.detail === 'string') {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg;
      }
    } catch {
      /* 非 JSON 响应 */
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
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

export async function retryProject(projectId: string): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/api/projects/${projectId}/retry`, { method: 'POST' });
}

export async function deleteProject(projectId: string): Promise<void> {
  await request<void>(`/api/projects/${projectId}`, { method: 'DELETE' });
}

// --- 小说 API ---

export interface NovelCreatePayload {
  premise: string;
  genre: string;
  target_chapters?: number;
}

export interface NovelChapterResponse {
  id: string;
  index: number;
  title: string;
  content: string;
  summary: string;
  word_count: number;
  status: string;
  validation_status: string;
  validation_score: number;
  validation_issues: string;
}

export interface NovelResponse {
  id: string;
  premise: string;
  genre: string;
  title: string;
  synopsis: string;
  bible_json: string;
  status: string;
  progress: number;
  error: string | null;
  created_at: string | null;
  chapters: NovelChapterResponse[];
}

export interface NovelListItem {
  id: string;
  premise: string;
  genre: string;
  title: string;
  status: string;
  progress: number;
  created_at: string | null;
}

export interface NovelChatResponse {
  reply: string;
  novel: NovelResponse;
}

export async function createNovel(payload: NovelCreatePayload): Promise<NovelResponse> {
  return request<NovelResponse>('/api/novels', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchNovel(novelId: string): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}`);
}

export async function listNovels(): Promise<NovelListItem[]> {
  return request<NovelListItem[]>('/api/novels');
}

export async function deleteNovel(novelId: string): Promise<void> {
  await request<void>(`/api/novels/${novelId}`, { method: 'DELETE' });
}

export async function continueNovel(
  novelId: string,
  writeCount = 1,
): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/chapters/next`, {
    method: 'POST',
    body: JSON.stringify({ write_count: writeCount }),
  });
}

export async function approveNovelChapter(
  novelId: string,
  chapterIndex: number,
): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/chapters/${chapterIndex}/approve`, {
    method: 'POST',
  });
}

export async function rewriteNovelChapter(
  novelId: string,
  chapterIndex: number,
): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/chapters/${chapterIndex}/rewrite`, {
    method: 'POST',
  });
}

export async function replanNovel(novelId: string): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/replan`, {
    method: 'POST',
  });
}

export async function startNovelWriting(
  novelId: string,
  writeCount = 3,
): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/start-writing`, {
    method: 'POST',
    body: JSON.stringify({ write_count: writeCount }),
  });
}

export interface NovelBiblePatchPayload {
  world?: string;
  power_system?: string;
  characters?: NovelBibleCharacter[];
  items?: NovelBibleItem[];
  outline?: NovelBibleOutlineItem[];
  volumes?: NovelBibleVolume[];
  foreshadowing?: NovelBibleForeshadowing[];
}

export async function retryNovelPlan(novelId: string): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/retry-plan`, {
    method: 'POST',
  });
}

export interface NovelOutlineItemResponse {
  index: number;
  title: string;
  summary: string;
  hook?: string;
  arc_id?: string;
  volume_id?: string;
  detail_level?: string;
}

export async function fetchNovelOutline(
  novelId: string,
  from: number,
  to: number,
  detail?: 'skeleton' | 'detailed',
): Promise<NovelOutlineItemResponse[]> {
  const params = new URLSearchParams({ from: String(from), to: String(to) });
  if (detail) {
    params.set('detail_level', detail);
  }
  return request<NovelOutlineItemResponse[]>(`/api/novels/${novelId}/outline?${params}`);
}

export async function patchNovelBible(
  novelId: string,
  patch: NovelBiblePatchPayload,
): Promise<NovelResponse> {
  return request<NovelResponse>(`/api/novels/${novelId}/bible`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}

export async function chatNovel(novelId: string, message: string): Promise<NovelChatResponse> {
  return request<NovelChatResponse>(`/api/novels/${novelId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export function exportNovelUrl(novelId: string, format: 'md' | 'txt'): string {
  return `${API_BASE}/api/novels/${novelId}/export?format=${format}`;
}

// --- 鉴权 ---

export interface AuthUserResponse {
  id: string;
  email: string;
  display_name: string;
  tenant_id: string;
  tenant_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUserResponse;
}

export async function fetchAuthStatus(): Promise<{ enabled: boolean }> {
  return request<{ enabled: boolean }>('/api/auth/status');
}

export async function login(payload: { email: string; password: string }): Promise<TokenResponse> {
  return request<TokenResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function register(payload: {
  email: string;
  password: string;
  display_name?: string;
}): Promise<TokenResponse> {
  return request<TokenResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchMe(): Promise<AuthUserResponse> {
  return request<AuthUserResponse>('/api/auth/me');
}

// --- 图文 ---

export interface ArticleCreatePayload {
  topic: string;
  platform: string;
  tone: string;
}

export interface ArticleResponse {
  id: string;
  topic: string;
  platform: string;
  tone: string;
  status: string;
  title: string;
  body_md: string;
  error: string | null;
  created_at: string | null;
}

export async function createArticle(payload: ArticleCreatePayload): Promise<ArticleResponse> {
  return request<ArticleResponse>('/api/articles', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchArticle(articleId: string): Promise<ArticleResponse> {
  return request<ArticleResponse>(`/api/articles/${articleId}`);
}

export async function listArticles(): Promise<
  Pick<ArticleResponse, 'id' | 'topic' | 'platform' | 'status' | 'title' | 'created_at'>[]
> {
  return request(`/api/articles`);
}
