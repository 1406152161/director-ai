/**
 * @author zhangzhihao
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { fetchProject, retryProject } from '../api/client';
import type { AssetResponse } from '../api/client';
import { isTerminalProgressStatus, useProgressEvents } from '../hooks/useProgressEvents';
import {
  VIDEO_ASPECT_LABEL,
  VIDEO_STATUS_LABEL,
  VIDEO_STYLE_LABEL,
} from '../utils/videoLabels';
import { useCallback, useState } from 'react';
import { LoadableImage, LoadableVideo } from '../components/MediaLoadable';
import { ContentSkeleton } from '../components/Skeleton';
import { ProgressBar } from '../components/ProgressBar';
import { StatusBadge } from '../components/StatusBadge';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const ASSET_TYPE_LABEL: Record<string, string> = {
  character: '角色',
  scene: '场景',
  prop: '道具',
};

function mediaSrc(url: string): string {
  return url.startsWith('http') ? url : `${API_BASE}${url}`;
}

function AssetCard({ asset }: { asset: AssetResponse }) {
  const typeLabel = ASSET_TYPE_LABEL[asset.asset_type] ?? asset.asset_type;
  return (
    <article className="asset-card">
      {asset.image_url ? (
        <LoadableImage
          src={mediaSrc(asset.image_url)}
          alt={asset.name_cn}
          className="asset-image"
          placeholderClassName="asset-image-placeholder media-load-error"
          errorLabel="资产图加载失败"
        />
      ) : (
        <div className="asset-image-placeholder">生成中…</div>
      )}
      <div className="asset-info">
        <span className="asset-type-badge">{typeLabel}</span>
        <p className="asset-name">{asset.name_cn}</p>
      </div>
    </article>
  );
}

function ProgressPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [sseConnected, setSseConnected] = useState(false);

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      if (sseConnected) return false;
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 2000;
    },
  });

  const onProgress = useCallback(() => {
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    }
  }, [projectId, queryClient]);

  const retryMutation = useMutation({
    mutationFn: () => retryProject(projectId!),
    onSuccess: (updated) => {
      queryClient.setQueryData(['project', projectId], updated);
    },
  });

  useProgressEvents(
    'project',
    projectId,
    !!projectId && !isTerminalProgressStatus('project', project?.status),
    onProgress,
    () => setSseConnected(true),
    () => setSseConnected(false),
  );

  if (isLoading) {
    return (
      <section className="page progress-page">
        <h1>创作进度</h1>
        <ContentSkeleton />
      </section>
    );
  }

  if (error || !project) {
    return (
      <section className="page progress-page">
        <h1>创作进度</h1>
        <p className="error-text" role="alert">
          {error
            ? `加载失败：${(error as Error).message}`
            : '项目不存在或已被删除'}
        </p>
        <div className="progress-actions">
          <Link to="/library?tab=video" className="btn-secondary">
            我的作品
          </Link>
          <Link to="/video" className="btn-primary">
            新建视频
          </Link>
        </div>
      </section>
    );
  }

  const statusLabel = VIDEO_STATUS_LABEL[project.status] ?? project.status;
  const totalShots = project.shots.length;
  const totalAssets = project.assets.length;
  const completedAssets = project.assets.filter((a) => a.image_url).length;
  const completedImages = project.shots.filter((s) => s.image_url).length;
  const completedVideos = project.shots.filter((s) => s.video_url).length;
  const completedClips = project.shots.filter((s) => s.clip_status === 'completed').length;

  let progressHint = statusLabel;
  if (project.status === 'asseting' && totalAssets > 0) {
    progressHint = `资产 ${completedAssets}/${totalAssets}`;
  } else if (project.status === 'imaging' && totalShots > 0) {
    progressHint = `配图 ${completedImages}/${totalShots}`;
  } else if (project.status === 'videoing' && totalShots > 0) {
    progressHint = `视频 ${completedVideos}/${totalShots}`;
  } else if (project.status === 'synthesizing' && totalShots > 0) {
    progressHint = `合成 ${completedClips}/${totalShots}`;
  }

  const outputSrc = project.output_url ? mediaSrc(project.output_url) : null;
  const downloadName = `${(project.title || 'director-ai').replace(/[\\/:*?"<>|]/g, '_')}.mp4`;
  const styleLabel = VIDEO_STYLE_LABEL[project.style] ?? project.style;
  const aspectLabel = VIDEO_ASPECT_LABEL[project.aspect_ratio] ?? project.aspect_ratio;

  return (
    <section className="page progress-page">
      <div className="progress-header">
        <div>
          <h1>{project.title ?? '创作进度'}</h1>
          <p className="progress-story-excerpt">{project.story}</p>
          <p className="project-meta-line">
            {styleLabel} · {project.duration} 秒 · {aspectLabel}
          </p>
        </div>
        <div className="progress-actions">
          <Link to="/library?tab=video" className="btn-secondary btn-sm">
            我的作品
          </Link>
          <Link to="/video" className="btn-secondary btn-sm">
            再创作
          </Link>
        </div>
      </div>

      <ProgressBar value={project.progress} />
      <p className="progress-status">
        <StatusBadge status={project.status} label={progressHint} />
        <span className="progress-percent">{project.progress}%</span>
      </p>

      {project.status === 'failed' && (
        <div className="progress-failed-panel" role="alert">
          <p className="error-text">错误：{project.error ?? '未知错误'}</p>
          <p className="form-hint">可点击下方重试，或调整创意后重新创建。</p>
          <div className="progress-actions">
            <button
              type="button"
              className="btn-primary"
              disabled={retryMutation.isPending}
              onClick={() => retryMutation.mutate()}
            >
              {retryMutation.isPending ? '重试中…' : '重试任务'}
            </button>
            <Link to="/video" className="btn-secondary">
              重新创作
            </Link>
          </div>
          {retryMutation.isError && (
            <p className="form-error" role="alert">
              重试失败：{(retryMutation.error as Error)?.message ?? '请稍后重试'}
            </p>
          )}
        </div>
      )}

      {project.status === 'pending' && project.progress === 0 && (
        <p className="form-hint">
          任务排队中…若长时间无进展，请确认后端 API 与 Celery Worker 已启动（生产环境需{' '}
          <code>USE_CELERY=true</code>）。
        </p>
      )}

      {project.status !== 'completed' && project.status !== 'failed' && totalShots === 0 && (
        <p className="placeholder-hint">正在生成分镜脚本，请稍候…</p>
      )}

      {project.status === 'asseting' && totalAssets > 0 && (
        <p className="placeholder-hint">
          正在生成导演设定资产（{completedAssets}/{totalAssets}）…
        </p>
      )}

      {project.status === 'imaging' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在为 {totalShots} 个镜头生成关键帧（{completedImages}/{totalShots}）…
        </p>
      )}

      {project.status === 'videoing' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在链式生成视频与旁白（{completedVideos}/{totalShots}）…
        </p>
      )}

      {project.status === 'synthesizing' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在 xfade 转场合成（{completedClips}/{totalShots}）…
        </p>
      )}

      {project.status === 'completed' && !outputSrc && (
        <p className="form-error" role="alert">
          生成已完成但未找到成片文件，请检查后端 outputs 目录或联系管理员。
        </p>
      )}

      {project.status === 'completed' && outputSrc && (
        <div className="output-preview">
          <h2>成片预览</h2>
          <LoadableVideo
            className="output-video"
            src={outputSrc}
            errorLabel="成片加载失败，可尝试下载或重试"
          />
          <a href={outputSrc} download={downloadName} className="download-btn">
            下载成片
          </a>
          <p className="form-hint">若下载无效，请右键视频选择「另存为」。</p>
        </div>
      )}

      {project.assets.length > 0 && (
        <div className="director-settings">
          <h2>导演设定</h2>
          <div className="asset-grid">
            {project.assets.map((asset) => (
              <AssetCard key={asset.id} asset={asset} />
            ))}
          </div>
        </div>
      )}

      {project.shots.length > 0 && (
        <div className="storyboard-result">
          <h2>分镜卡片</h2>
          <div className="shot-grid">
            {project.shots.map((shot) => (
              <article key={shot.id} className="shot-card">
                {shot.image_url ? (
                  <LoadableImage
                    src={mediaSrc(shot.image_url)}
                    alt={`镜头 ${shot.index}`}
                    className="shot-image"
                    placeholderClassName="shot-image-placeholder media-load-error"
                    errorLabel={`镜头 ${shot.index} 配图加载失败`}
                  />
                ) : (
                  <div className="shot-image-placeholder">暂无配图</div>
                )}
                {shot.video_url ? (
                  <LoadableVideo
                    className="shot-video"
                    src={mediaSrc(shot.video_url)}
                    errorLabel={`镜头 ${shot.index} 视频加载失败`}
                    placeholderClassName="shot-video-placeholder media-load-error"
                  />
                ) : project.status === 'videoing' || project.status === 'synthesizing' ? (
                  <div className="shot-video-placeholder">视频生成中…</div>
                ) : null}
                <div className="shot-info">
                  <span className="shot-index">镜头 {shot.index}</span>
                  {shot.clip_status === 'completed' && (
                    <span className="clip-badge">已合成</span>
                  )}
                  <p className="shot-scene">{shot.scene_cn}</p>
                  <p className="shot-narration">{shot.narration_cn}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default ProgressPage;
