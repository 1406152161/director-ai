/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { fetchProject } from '../api/client';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  scripting: '脚本生成中',
  imaging: '配图生成中',
  videoing: '视频生成中',
  synthesizing: '合成中',
  completed: '已完成',
  failed: '生成失败',
};

function ProgressPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 2000;
    },
  });

  if (isLoading) {
    return (
      <section className="page progress-page">
        <h1>创作进度</h1>
        <p>加载中…</p>
      </section>
    );
  }

  if (error || !project) {
    return (
      <section className="page progress-page">
        <h1>创作进度</h1>
        <p className="error-text">加载失败，请返回重试</p>
        <Link to="/">返回首页</Link>
      </section>
    );
  }

  const statusLabel = STATUS_LABEL[project.status] ?? project.status;
  const totalShots = project.shots.length;
  const completedImages = project.shots.filter((s) => s.image_url).length;
  const completedVideos = project.shots.filter((s) => s.video_url).length;
  const completedClips = project.shots.filter((s) => s.clip_status === 'completed').length;

  let progressHint = statusLabel;
  if (project.status === 'imaging' && totalShots > 0) {
    progressHint = `配图 ${completedImages}/${totalShots}`;
  } else if (project.status === 'videoing' && totalShots > 0) {
    progressHint = `视频 ${completedVideos}/${totalShots}`;
  } else if (project.status === 'synthesizing' && totalShots > 0) {
    progressHint = `合成 ${completedClips}/${totalShots}`;
  }

  const outputSrc = project.output_url
    ? project.output_url.startsWith('http')
      ? project.output_url
      : `${API_BASE}${project.output_url}`
    : null;

  return (
    <section className="page progress-page">
      <h1>{project.title ?? '创作进度'}</h1>
      <p className="project-id">项目 ID: {project.id}</p>

      <div className="progress-bar-wrap">
        <div className="progress-bar" style={{ width: `${project.progress}%` }} />
      </div>
      <p className="progress-status">
        <span className={`status-badge status-${project.status}`}>{progressHint}</span>
        <span className="progress-percent">{project.progress}%</span>
      </p>

      {project.status === 'failed' && (
        <p className="error-text">错误：{project.error ?? '未知错误'}</p>
      )}

      {project.status !== 'completed' && totalShots === 0 && (
        <p className="placeholder-hint">正在生成分镜脚本，请稍候…</p>
      )}

      {project.status === 'imaging' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在为 {totalShots} 个镜头生成竖屏配图（{completedImages}/{totalShots}）…
        </p>
      )}

      {project.status === 'videoing' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在生成视频与旁白（{completedVideos}/{totalShots}）…
        </p>
      )}

      {project.status === 'synthesizing' && totalShots > 0 && (
        <p className="placeholder-hint">
          正在合成镜头片段（{completedClips}/{totalShots}）…
        </p>
      )}

      {project.status === 'completed' && outputSrc && (
        <div className="output-preview">
          <h2>成片预览</h2>
          <video controls className="output-video" src={outputSrc}>
            您的浏览器不支持视频播放
          </video>
          <a href={outputSrc} download className="download-btn">
            下载成片
          </a>
        </div>
      )}

      {project.shots.length > 0 && (
        <div className="storyboard-result">
          <h2>分镜卡片</h2>
          <div className="shot-grid">
            {project.shots.map((shot) => (
              <article key={shot.id} className="shot-card">
                {shot.image_url ? (
                  <img
                    src={shot.image_url}
                    alt={`镜头 ${shot.index}`}
                    className="shot-image"
                  />
                ) : (
                  <div className="shot-image-placeholder">暂无配图</div>
                )}
                {shot.video_url && (
                  <video
                    controls
                    className="shot-video"
                    src={shot.video_url.startsWith('http') ? shot.video_url : `${API_BASE}${shot.video_url}`}
                  />
                )}
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
