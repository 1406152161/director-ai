/**
 * @author zhangzhihao
 */
import { Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProgressPage from './pages/ProgressPage';
import LibraryPage from './pages/LibraryPage';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="logo">
          director-ai
        </Link>
        <nav>
          <Link to="/">创作</Link>
          <Link to="/library">我的作品</Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/progress/:projectId" element={<ProgressPage />} />
          <Route path="/library" element={<LibraryPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
