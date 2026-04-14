import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';
import TherapyMinutes from './pages/TherapyMinutes';
import IDT from './pages/IDT';
import Functional from './pages/Functional';
import PhysicianEvaluation from './pages/PhysicianEvaluation';
import MedicalNecessity from './pages/MedicalNecessity';
import Admin from './pages/Admin';
import Tier1Scheduler from './pages/Tier1Scheduler';
import SessionView from './pages/SessionView';

function App() {
  const sidebarLinkClass = ({ isActive }) => (`rc-sidebar-link${isActive ? ' rc-sidebar-link-active' : ''}`);

  return (
    <Router>
      <div className="rc-app-shell">
        {/* Navigation Header */}
        <nav className="rc-topnav">
          <div className="rc-topnav-inner">
            <div className="rc-brand" aria-label="RehabConnect home">
              <span className="rc-brand-logo" aria-hidden="true" />
              <h1 className="rc-brand-text">RehabConnect</h1>
            </div>
            <div className="rc-nav-links">
              <Link to="/" className="rc-nav-link">Care Coordination Workspace</Link>
            </div>
          </div>
        </nav>

        <div className="rc-layout">
          <aside className="rc-sidebar" aria-label="Workspace navigation">
            <h2 className="rc-sidebar-title">Workspace</h2>
            <nav className="rc-sidebar-nav">
              <NavLink to="/" end className={sidebarLinkClass}>Dashboard</NavLink>
              <NavLink to="/patients" className={sidebarLinkClass}>Patients</NavLink>
              <NavLink to="/session-view" className={sidebarLinkClass}>Sessions</NavLink>
              <NavLink to="/scheduler" className={sidebarLinkClass}>Automation</NavLink>
            </nav>
          </aside>

          <main className="rc-main">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/patients" element={<PatientList />} />
              <Route path="/patients/:patientId" element={<PatientDetail />} />
              <Route path="/therapy" element={<TherapyMinutes />} />
              <Route path="/idt" element={<IDT />} />
              <Route path="/functional" element={<Functional />} />
              <Route path="/physician" element={<PhysicianEvaluation />} />
              <Route path="/medical-necessity" element={<MedicalNecessity />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/scheduler" element={<Tier1Scheduler />} />
              <Route path="/session-view" element={<SessionView />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;