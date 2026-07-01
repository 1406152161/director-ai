/**

 * @author zhangzhihao

 */

import { useQuery } from '@tanstack/react-query';

import { Link } from 'react-router-dom';

import { listNovels, listProjects } from '../api/client';
import { CardSkeleton } from '../components/Skeleton';
import { ProgressBar } from '../components/ProgressBar';
import { NOVEL_STATUS_LABEL } from '../utils/novelLabels';

import { VIDEO_STATUS_LABEL } from '../utils/videoLabels';

import { isNovelInProgress, isVideoInProgress } from '../utils/workStatus';



type HubWorkItem = {

  kind: 'video' | 'novel';

  id: string;

  title: string;

  status: string;

  statusLabel: string;

  progress: number;

  href: string;

  at: string | null;

  inProgress: boolean;

};



function HubPage() {

  const {

    data: projects,

    isLoading: projectsLoading,

    isError: projectsError,

    error: projectsFetchError,

  } = useQuery({

    queryKey: ['projects'],

    queryFn: listProjects,

    refetchInterval: (query) => {

      const items = query.state.data ?? [];

      return items.some((p) => isVideoInProgress(p.status)) ? 5000 : false;

    },

  });



  const {

    data: novels,

    isLoading: novelsLoading,

    isError: novelsError,

    error: novelsFetchError,

  } = useQuery({

    queryKey: ['novels'],

    queryFn: listNovels,

    refetchInterval: (query) => {

      const items = query.state.data ?? [];

      return items.some((n) => isNovelInProgress(n.status)) ? 5000 : false;

    },

  });



  const allItems: HubWorkItem[] = [

    ...(projects ?? []).map((p) => ({

      kind: 'video' as const,

      id: p.id,

      title: p.title ?? p.story.slice(0, 40),

      status: p.status,

      statusLabel: VIDEO_STATUS_LABEL[p.status] ?? p.status,

      progress: p.progress,

      href: `/video/progress/${p.id}`,

      at: p.created_at,

      inProgress: isVideoInProgress(p.status),

    })),

    ...(novels ?? []).map((n) => ({

      kind: 'novel' as const,

      id: n.id,

      title: n.title || n.premise.slice(0, 40),

      status: n.status,

      statusLabel: NOVEL_STATUS_LABEL[n.status] ?? n.status,

      progress: n.progress,

      href: `/novel/${n.id}`,

      at: n.created_at,

      inProgress: isNovelInProgress(n.status),

    })),

  ];



  const inProgress = allItems

    .filter((item) => item.inProgress)

    .sort((a, b) => {

      const ta = a.at ? new Date(a.at).getTime() : 0;

      const tb = b.at ? new Date(b.at).getTime() : 0;

      return tb - ta;

    });



  const recent = [...allItems]

    .sort((a, b) => {

      const ta = a.at ? new Date(a.at).getTime() : 0;

      const tb = b.at ? new Date(b.at).getTime() : 0;

      return tb - ta;

    })

    .slice(0, 3);



  const isLoading = projectsLoading || novelsLoading;



  return (

    <section className="page hub-page">

      <div className="hub-hero">

        <h1>AI 导演工作台</h1>

        <p className="subtitle">

          从一句话创意到成片视频，或整本长篇小说——工业化 AI 创作流程，一站完成。

        </p>

      </div>



      {isLoading && <CardSkeleton count={3} />}



      {projectsError && (

        <p className="form-error" role="alert">

          加载视频列表失败：{(projectsFetchError as Error)?.message ?? '请稍后重试'}

        </p>

      )}

      {novelsError && (

        <p className="form-error" role="alert">

          加载小说列表失败：{(novelsFetchError as Error)?.message ?? '请稍后重试'}

        </p>

      )}



      {inProgress.length > 0 && (

        <div className="hub-in-progress">

          <div className="hub-section-head">

            <h2>进行中</h2>

            <Link to="/library" className="hub-section-link">

              查看全部

            </Link>

          </div>

          <ul className="hub-in-progress-list">

            {inProgress.map((item) => (

              <li key={`${item.kind}-${item.id}`}>

                <Link to={item.href} className="hub-in-progress-item">

                  <span className={`hub-recent-kind kind-${item.kind}`}>

                    {item.kind === 'video' ? '视频' : '小说'}

                  </span>

                  <div className="hub-in-progress-body">

                    <span className="hub-recent-title">{item.title}</span>

                    <span className="hub-recent-status">

                      {item.statusLabel} · {item.progress}%

                    </span>

                    <ProgressBar value={item.progress} mini />

                  </div>

                  <span className="hub-in-progress-cta">继续 →</span>

                </Link>

              </li>

            ))}

          </ul>

        </div>

      )}



      <div className="hub-grid">

        <Link to="/video" className="hub-card hub-card-video">

          <span className="hub-card-label">短视频</span>

          <h2>一句话生成完整短片</h2>

          <p>脚本 · 资产 · 配图 · 视频 · 合成</p>

        </Link>

        <Link to="/novel" className="hub-card hub-card-novel">

          <span className="hub-card-label">长篇小说</span>

          <h2>规划世界观与整本大纲</h2>

          <p>卷弧 · 伏笔 · 道具 · 按章连载写作</p>

        </Link>

        <Link to="/article" className="hub-card hub-card-article">

          <span className="hub-card-label">图文</span>

          <h2>多平台图文种草</h2>

          <p>小红书 · 公众号 · 预览占位</p>

        </Link>

        <Link to="/library" className="hub-card hub-card-library">

          <span className="hub-card-label">作品库</span>

          <h2>我的作品</h2>

          <p>视频与小说统一管理</p>

        </Link>

      </div>



      {recent.length > 0 && (

        <div className="hub-recent">

          <h2>最近作品</h2>

          <ul className="hub-recent-list">

            {recent.map((item) => (

              <li key={`${item.kind}-${item.id}`}>

                <Link to={item.href} className="hub-recent-item">

                  <span className={`hub-recent-kind kind-${item.kind}`}>

                    {item.kind === 'video' ? '视频' : '小说'}

                  </span>

                  <span className="hub-recent-title">{item.title}</span>

                  <span className="hub-recent-status">{item.statusLabel}</span>

                </Link>

              </li>

            ))}

          </ul>

        </div>

      )}

    </section>

  );

}



export default HubPage;


