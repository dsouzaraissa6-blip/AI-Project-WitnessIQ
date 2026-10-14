// WitnessIQ Dashboard page
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FlaskConical, FolderOpen, FileText, AlertTriangle, Clock, Scale } from 'lucide-react';
import { getCases, loadDemo } from '../api/client';
import type { Case } from '../types';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => {
    getCases()
      .then(data => setCases(data.cases))
      .catch(() => toast.error('Failed to load cases.'))
      .finally(() => setLoading(false));
  }, []);

  const handleLoadDemo = async () => {
    setDemoLoading(true);
    try {
      const result = await loadDemo();
      toast.success('Demo case loaded — ' + result.message);
      navigate(`/case/${result.case_id}`);
    } catch {
      toast.error('Failed to load demo case.');
    } finally {
      setDemoLoading(false);
    }
  };

  const totalStatements = cases.reduce((s, c) => s + c.statement_count, 0);
  const recentCases = cases.slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Scale className="w-8 h-8" style={{ color: '#1e3a5f' }} />
          <h1 className="text-2xl font-bold" style={{ color: '#0f2044' }}>WitnessIQ</h1>
        </div>
        <p className="text-slate-500 text-sm max-w-2xl">
          AI-powered witness statement analysis and inconsistency detection.
          This tool assists investigators by flagging potential textual discrepancies for human review.
          It does not determine truth, guilt, or credibility.
        </p>
      </div>

      {/* Disclaimer banner */}
      <div className="mb-6 p-3 rounded-lg border border-amber-200 bg-amber-50 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-800">
          <strong>Academic / Research Tool:</strong> All results are automated observations requiring
          human expert review. This system does not assess witness credibility or establish factual truth.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
        <div className="card p-4">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <FolderOpen className="w-4 h-4" /> Total Cases
          </div>
          <div className="text-2xl font-bold" style={{ color: '#0f2044' }}>{cases.length}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <FileText className="w-4 h-4" /> Statements
          </div>
          <div className="text-2xl font-bold" style={{ color: '#0f2044' }}>{totalStatements}</div>
        </div>
        <div className="card p-4 col-span-2 sm:col-span-1">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <Clock className="w-4 h-4" /> Last Updated
          </div>
          <div className="text-sm font-medium" style={{ color: '#0f2044' }}>
            {cases.length > 0
              ? new Date(cases[0].updated_at).toLocaleDateString()
              : 'No cases yet'}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 mb-8">
        <button
          className="btn-primary px-5 py-2.5 text-sm"
          onClick={() => navigate('/create-case')}
        >
          <Plus className="w-4 h-4" />
          Create New Case
        </button>
        <button
          className="btn-secondary px-5 py-2.5 text-sm"
          onClick={handleLoadDemo}
          disabled={demoLoading}
        >
          <FlaskConical className="w-4 h-4" />
          {demoLoading ? 'Loading Demo…' : 'Load Demo Case'}
        </button>
      </div>

      {/* Recent cases */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-800">Recent Cases</h2>
          <button
            className="text-xs text-blue-600 hover:underline"
            onClick={() => navigate('/history')}
          >
            View all →
          </button>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="card p-4 shimmer h-20" />
            ))}
          </div>
        ) : recentCases.length === 0 ? (
          <div className="card p-8 text-center text-slate-400">
            <FolderOpen className="w-10 h-10 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No cases yet. Create a case or load the demo to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentCases.map(c => (
              <div
                key={c.id}
                className="card p-4 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all duration-150"
                onClick={() => navigate(`/case/${c.id}`)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-medium text-sm text-slate-800 truncate">{c.title}</span>
                      {c.is_demo && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-purple-50 text-purple-600 border border-purple-200 shrink-0">
                          Demo
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400">{c.reference_id}</div>
                    {c.description && (
                      <div className="text-xs text-slate-500 mt-1 line-clamp-1">{c.description}</div>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-slate-400">{c.statement_count} statement{c.statement_count !== 1 ? 's' : ''}</div>
                    <div className="text-xs text-slate-400">{new Date(c.updated_at).toLocaleDateString()}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
