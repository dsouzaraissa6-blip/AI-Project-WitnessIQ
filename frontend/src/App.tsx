// WitnessIQ App root — router setup
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import CreateCase from './pages/CreateCase';
import CaseWorkspace from './pages/CaseWorkspace';
import AnalysisResults from './pages/AnalysisResults';
import CaseHistory from './pages/CaseHistory';
import About from './pages/About';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create-case" element={<CreateCase />} />
            <Route path="/case/:id" element={<CaseWorkspace />} />
            <Route path="/case/:id/results" element={<AnalysisResults />} />
            <Route path="/history" element={<CaseHistory />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: { fontSize: '13px', maxWidth: '400px' },
            success: { duration: 3000 },
            error: { duration: 5000 },
          }}
        />
      </div>
    </BrowserRouter>
  );
}
