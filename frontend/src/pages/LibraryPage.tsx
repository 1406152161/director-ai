/**

 * @author zhangzhihao

 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { Link, useSearchParams } from 'react-router-dom';

import { useEffect } from 'react';

import { listNovels, listProjects, retryProject } from '../api/client';
import { CardSkeleton } from '../components/Skeleton';
import { ProgressBar } from '../components/ProgressBar';
import { useToastStore } from '../store/useToastStore';
import { GENRE_LABEL, NOVEL_STATUS_LABEL } from '../utils/novelLabels';

import { VIDEO_ASPECT_LABEL, VIDEO_STATUS_LABEL, VIDEO_STYLE_LABEL } from '../utils/videoLabels';

import { isNovelInProgress, isVideoInProgress } from '../utils/workStatus';



const LIBRARY_TAB_KEY = 'director-ai-library-tab';



type LibraryTab = 'video' | 'novel';



function LibraryPage() {

  const queryClient = useQueryClient();

  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab');

  const activeTab: LibraryTab =

    tabParam === 'novel' || tabParam === 'video'

      ? tabParam

      : ((localStorage.getItem(LIBRARY_TAB_KEY) as LibraryTab) ?? 'video');



  useEffect(() => {

    localStorage.setItem(LIBRARY_TAB_KEY, activeTab);

  }, [activeTab]);



  const setTab = (tab: LibraryTab) => {

    setSearchParams({ tab });

  };



  const { data: projects, isLoading: projectsLoading, isError: projectsError, error: projectsFetchError } = useQuery({

    queryKey: ['projects'],

    queryFn: listProjects,

    refetchInterval: (query) => {

      if (activeTab !== 'video') return false;

      const items = query.state.data ?? [];

      return items.some((p) => isVideoInProgress(p.status)) ? 5000 : false;

    },

  });



  const { data: novels, isLoading: novelsLoading, isError: novelsError, error: novelsFetchError } = useQuery({

    queryKey: ['novels'],

    queryFn: listNovels,

    refetchInterval: (query) => {

      if (activeTab !== 'novel') return false;

      const items = query.state.data ?? [];

      return items.some((n) => isNovelInProgress(n.status)) ? 5000 : false;

    },

  });



  const showToast = useToastStore((s) => s.showToast);

  const retryMutation = useMutation({

    mutationFn: retryProject,

    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: ['projects'] });

    },

    onError: (err) => showToast('error', (err as Error)?.message ?? '重试失败'),

  });



  const videoCount = projects?.length ?? 0;

  const novelCount = novels?.length ?? 0;

  const isLoading = activeTab === 'video' ? projectsLoading : novelsLoading;



  return (

    <section className="page library-page">

      <h1>我的作品</h1>



      <div className="library-tabs">

        <button

          type="button"

          className={activeTab === 'video' ? 'active' : ''}

          onClick={() => setTab('video')}

        >

          视频 <span className="tab-badge">{videoCount}</span>

        </button>

        <button

          type="button"

          className={activeTab === 'novel' ? 'active' : ''}

          onClick={() => setTab('novel')}

        >

          小说 <span className="tab-badge">{novelCount}</span>

        </button>

      </div>



      {isLoading && <CardSkeleton count={6} />}



      {activeTab === 'video' && projectsError && (

        <p className="form-error" role="alert">

          加载视频列表失败：{(projectsFetchError as Error)?.message ?? '请稍后重试'}

        </p>

      )}



      {activeTab === 'video' && (

        <>

          {!projectsLoading && !projectsError && videoCount === 0 && (

            <p className="empty-state">

              暂无视频作品，<Link to="/video">去视频专区</Link> 开始创作

            </p>

          )}

          {videoCount > 0 && !projectsError && (

            <ul className="project-list">

              {projects!.map((project) => (

                <li key={project.id}>

                  <Link to={`/video/progress/${project.id}`} className="project-card">

                    <p className="project-title">{project.title ?? project.story}</p>

                    <p className="project-story">{project.story}</p>

                    <div className="project-meta">

                      <span>{VIDEO_STYLE_LABEL[project.style] ?? project.style}</span>

                      <span>{project.duration}s</span>

                      <span>{VIDEO_ASPECT_LABEL[project.aspect_ratio] ?? project.aspect_ratio}</span>

                      <span className={`status status-${project.status}`}>

                        {VIDEO_STATUS_LABEL[project.status] ?? project.status}

                      </span>

                      {project.status === 'failed' && (

                        <button

                          type="button"

                          className="inline-link-btn"

                          disabled={retryMutation.isPending}

                          onClick={(e) => {

                            e.preventDefault();

                            e.stopPropagation();

                            retryMutation.mutate(project.id);

                          }}

                        >

                          {retryMutation.isPending ? '重试中…' : '重试'}

                        </button>

                      )}

                      {project.status !== 'completed' && project.status !== 'failed' && (

                        <span className="progress-mini">{project.progress}%</span>

                      )}

                    </div>

                    {project.status !== 'completed' && project.status !== 'failed' && (
                      <ProgressBar value={project.progress} mini />
                    )}

                  </Link>

                </li>

              ))}

            </ul>

          )}

        </>

      )}



      {activeTab === 'novel' && novelsError && (

        <p className="form-error" role="alert">

          加载小说列表失败：{(novelsFetchError as Error)?.message ?? '请稍后重试'}

        </p>

      )}



      {activeTab === 'novel' && (

        <>

          {!novelsLoading && !novelsError && novelCount === 0 && (

            <p className="empty-state">

              暂无小说，<Link to="/novel">去小说专区</Link> 开始创作

            </p>

          )}

          {novelCount > 0 && !novelsError && (

            <ul className="project-list">

              {novels!.map((novel) => (

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

        </>

      )}

    </section>

  );

}



export default LibraryPage;


