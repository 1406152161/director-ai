/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { fetchProject } from '../api/client';

const STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  scripting: '脚本生成中',
  imaging: '配图生成中',
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
  const completedShots = project.shots.filter((s) => s.image_url).length;
  const totalShots = project.shots.length;

  const progressHint =
    project.status === 'imaging' && totalShots > 0
      ? `配图 ${completedShots}/${totalShots}`
      : statusLabel;

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
          正在为 {totalShots} 个镜头生成竖屏配图（{completedShots}/{totalShots}）…
        </p>
      )}

      {project.status === 'completed' && project.shots.length > 0 && (
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
                <div className="shot-info">
                  <span className="shot-index">镜头 {shot.index}</span>
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
