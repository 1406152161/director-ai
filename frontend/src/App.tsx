/**
 * @author zhangzhihao
 */
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProgressPage from './pages/ProgressPage';
import LibraryPage from './pages/LibraryPage';
import NovelCreatePage from './pages/NovelCreatePage';
import NovelWorkbenchPage from './pages/NovelWorkbenchPage';
import './App.css';

function AppTabs() {
  const location = useLocation();
  const isVideo = location.pathname === '/' || location.pathname.startsWith('/progress');
  const isNovel = location.pathname.startsWith('/novel');

  return (
    <nav className="app-tabs">
      <Link to="/" className={isVideo ? 'tab active' : 'tab'}>
        视频
      </Link>
      <Link to="/novel" className={isNovel ? 'tab active' : 'tab'}>
        小说
      </Link>
      <span className="tab tab-disabled" title="敬请期待">
        图文（敬请期待）
      </span>
    </nav>
  );
}

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="logo">
          director-ai
        </Link>
        <AppTabs />
        <nav className="app-nav-secondary">
          <Link to="/library">我的作品</Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/progress/:projectId" element={<ProgressPage />} />
          <Route path="/novel" element={<NovelCreatePage />} />
          <Route path="/novel/:novelId" element={<NovelWorkbenchPage />} />
          <Route path="/library" element={<LibraryPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
