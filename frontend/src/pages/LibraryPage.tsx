/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listNovels, listProjects } from '../api/client';

const VIDEO_STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  scripting: '脚本生成中',
  asseting: '资产生成中',
  imaging: '配图生成中',
  videoing: '视频生成中',
  synthesizing: '合成中',
  completed: '已完成',
  failed: '失败',
};

const NOVEL_STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  planning: '规划中',
  writing: '写作中',
  completed: '已完成',
  failed: '失败',
};

const GENRE_LABEL: Record<string, string> = {
  xuanhuan: '玄幻',
  dushi: '都市',
  xuanyi: '悬疑',
  tianai: '甜宠',
  kehuan: '科幻',
};

function LibraryPage() {
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
    refetchInterval: 5000,
  });

  const { data: novels, isLoading: novelsLoading } = useQuery({
    queryKey: ['novels'],
    queryFn: listNovels,
    refetchInterval: 5000,
  });

  const isLoading = projectsLoading || novelsLoading;

  return (
    <section className="page library-page">
      <h1>我的作品</h1>

      {isLoading && <p>加载中…</p>}

      <h2 className="library-section-title">视频</h2>
      {!projectsLoading && (!projects || projects.length === 0) && (
        <p className="empty-state">暂无视频作品，去首页开始创作吧</p>
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
                    {VIDEO_STATUS_LABEL[project.status] ?? project.status}
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

      <h2 className="library-section-title">小说</h2>
      {!novelsLoading && (!novels || novels.length === 0) && (
        <p className="empty-state">暂无小说，去小说 Tab 开始创作吧</p>
      )}
      {novels && novels.length > 0 && (
        <ul className="project-list">
          {novels.map((novel) => (
            <li key={novel.id}>
              <Link to={`/novel/${novel.id}`} className="project-card">
                <p className="project-title">{novel.title || novel.premise}</p>
                <p className="project-story">{novel.premise}</p>
                <div className="project-meta">
                  <span>{GENRE_LABEL[novel.genre] ?? novel.genre}</span>
                  <span className={`status status-${novel.status}`}>
                    {NOVEL_STATUS_LABEL[novel.status] ?? novel.status}
                  </span>
                  {novel.status !== 'completed' && (
                    <span className="progress-mini">{novel.progress}%</span>
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
