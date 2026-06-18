import React from 'react';
import {BrowserRouter, Route, Routes, useNavigate} from 'react-router-dom';
import UploadPage from './pages/UploadPage.jsx';
import ProcessingPage from './pages/ProcessingPage.jsx';
import ResultsPage from './pages/ResultsPage.jsx';

function Sidebar({recentJobs = []}) {
  const navigate = useNavigate();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">📊</div>
        <span className="sidebar-logo-text">DataNarrate</span>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Recent</div>
        {recentJobs.length === 0 ? (
          <div style={{padding: '8px 16px', color: 'var(--text-3)', fontSize: 12}}>
            No analyses yet
          </div>
        ) : (
          recentJobs.map(j => (
            <div key={j.id} className="sidebar-item"
              onClick={() => navigate(`/results/${j.id}`)}>
              <span className="sidebar-item-icon">📄</span>
              <span>{j.filename}</span>
            </div>
          ))
        )}
      </nav>

      <div className="sidebar-footer">
        <button className="btn-new" onClick={() => navigate('/')}>
          <span>+</span> New Analysis
        </button>
      </div>
    </aside>
  );
}

function Layout({children, breadcrumb, recentJobs}) {
  return (
    <div className="layout">
      <Sidebar recentJobs={recentJobs} />
      <div className="main-content">
        {breadcrumb && (
          <div className="topbar">
            <div className="topbar-breadcrumb">{breadcrumb}</div>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

function App() {
  const [recentJobs, setRecentJobs] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem('dn_jobs') || '[]'); }
    catch { return []; }
  });

  const addJob = (job) => {
    const updated = [job, ...recentJobs].slice(0, 10);
    setRecentJobs(updated);
    localStorage.setItem('dn_jobs', JSON.stringify(updated));
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          <Layout recentJobs={recentJobs}>
            <UploadPage onJobCreated={addJob} />
          </Layout>
        }/>
        <Route path="/processing/:jobId" element={
          <Layout breadcrumb={<>Analysis <span>in progress</span></>} recentJobs={recentJobs}>
            <ProcessingPage />
          </Layout>
        }/>
        <Route path="/results/:jobId" element={
          <Layout breadcrumb={<>Analysis <span>complete</span></>} recentJobs={recentJobs}>
            <ResultsPage />
          </Layout>
        }/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
