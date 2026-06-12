/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listProjects } from '../api/client';

const STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  scripting: '脚本生成中',
  imaging: '配图生成中',
  completed: '已完成',
  failed: '失败',
};

function LibraryPage() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
    refetchInterval: 5000,
  });

  return (
    <section className="page library-page">
      <h1>我的作品</h1>

      {isLoading && <p>加载中…</p>}

      {!isLoading && (!projects || projects.length === 0) && (
        <p className="empty-state">暂无作品，去首页开始创作吧</p>
      )}

      {projects && projects.length > 0 && (
        <ul className="project-list">
          {projects.map((project) => (
            <li key={project.id}>
              <Link to={`/progress/${project.id}`} className="project-card">
                <p className="project-title">{project.title ?? project.story}</p>
                <p className="project-story">{project.story}</p>
                <div className="project-meta">
                  <span>{project.style}</span>
                  <span>{project.duration}s</span>
                  <span>{project.aspect_ratio}</span>
                  <span className={`status status-${project.status}`}>
                    {STATUS_LABEL[project.status] ?? project.status}
                  </span>
                  {project.status !== 'completed' && (
                    <span className="progress-mini">{project.progress}%</span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default LibraryPage;
