/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { listProjects } from '../api/client';

function LibraryPage() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  return (
    <section className="page library-page">
      <h1>我的作品</h1>
      <p className="placeholder-hint">M0 占位页 — 展示历史创作与成片预览</p>

      {isLoading && <p>加载中…</p>}

      {!isLoading && (!projects || projects.length === 0) && (
        <p className="empty-state">暂无作品，去首页开始创作吧</p>
      )}

      {projects && projects.length > 0 && (
        <ul className="project-list">
          {projects.map((project) => (
            <li key={project.id} className="project-card">
              <p className="project-story">{project.story}</p>
              <div className="project-meta">
                <span>{project.style}</span>
                <span>{project.duration}s</span>
                <span>{project.aspect_ratio}</span>
                <span className="status">{project.status}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default LibraryPage;
