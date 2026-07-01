/**
 * @author zhangzhihao
 */
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import HubPage from './pages/HubPage';
import VideoCreatePage from './pages/VideoCreatePage';
import ProgressPage from './pages/ProgressPage';
import LibraryPage from './pages/LibraryPage';
import NovelCreatePage from './pages/NovelCreatePage';
import NovelWorkbenchPage from './pages/NovelWorkbenchPage';
import ArticleCreatePage from './pages/ArticleCreatePage';
import ArticlePreviewPage from './pages/ArticlePreviewPage';
import LoginPage from './pages/LoginPage';
import { useEffect, type ReactNode } from 'react';
import { fetchAuthStatus, fetchMe } from './api/client';
import { useAuthStore } from './store/useAuthStore';
import './App.css';

function AppHeader() {
  const location = useLocation();
  const path = location.pathname;
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const authEnabled = useAuthStore((s) => s.authEnabled);
  const clearSession = useAuthStore((s) => s.clearSession);

  const navClass = (prefix: string) =>
    path === prefix || path.startsWith(`${prefix}/`) ? 'nav-link active' : 'nav-link';

  return (
    <header className="app-header">
      <Link to="/" className="logo">
        director-ai
      </Link>
      <nav className="app-nav-main">
        <Link to="/" className={path === '/' ? 'nav-link active' : 'nav-link'}>
          首页
        </Link>
        <Link to="/video" className={navClass('/video')}>
          视频
        </Link>
        <Link to="/novel" className={navClass('/novel')}>
          小说
        </Link>
        <Link to="/article" className={navClass('/article')}>
          图文
        </Link>
        <Link to="/library" className={navClass('/library')}>
          我的作品
        </Link>
        {authEnabled && (
          token && user ? (
            <button type="button" className="nav-link nav-link-btn" onClick={clearSession}>
              退出 ({user.display_name || user.email})
            </button>
          ) : (
            <Link to="/login" className={navClass('/login')}>
              登录
            </Link>
          )
        )}
      </nav>
    </header>
  );
}

function AppBootstrap({ children }: { children: ReactNode }) {
  const setAuthEnabled = useAuthStore((s) => s.setAuthEnabled);
  const setSession = useAuthStore((s) => s.setSession);
  const token = useAuthStore((s) => s.token);
  const clearSession = useAuthStore((s) => s.clearSession);

  useEffect(() => {
    fetchAuthStatus()
      .then((s) => setAuthEnabled(s.enabled))
      .catch(() => setAuthEnabled(false));
  }, [setAuthEnabled]);

  useEffect(() => {
    if (!token) return;
    fetchMe()
      .then((user) => setSession(token, user))
      .catch(() => clearSession());
  }, [token, setSession, clearSession]);

  return <>{children}</>;
}

function App() {
  return (
    <div className="app">
      <AppBootstrap>
        <AppHeader />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HubPage />} />
            <Route path="/video" element={<VideoCreatePage />} />
            <Route path="/video/progress/:projectId" element={<ProgressPage />} />
            <Route path="/progress/:projectId" element={<ProgressRedirect />} />
            <Route path="/novel" element={<NovelCreatePage />} />
            <Route path="/novel/:novelId" element={<NovelWorkbenchPage />} />
            <Route path="/article" element={<ArticleCreatePage />} />
            <Route path="/article/:articleId" element={<ArticlePreviewPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/library" element={<LibraryPage />} />
          </Routes>
        </main>
      </AppBootstrap>
    </div>
  );
}

function ProgressRedirect() {
  const location = useLocation();
  const id = location.pathname.split('/').pop();
  return <Navigate to={`/video/progress/${id}`} replace />;
}

export default App;
