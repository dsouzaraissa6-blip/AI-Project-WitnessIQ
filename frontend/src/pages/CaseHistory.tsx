// Case History page
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderOpen, Trash2, BarChart2, Eye } from 'lucide-react';
import { getCases, deleteCase } from '../api/client';
import type { Case } from '../types';
import toast from 'react-hot-toast';

export default function CaseHistory() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCases()
      .then(d => setCases(d.cases))
      .catch(() => toast.error('Failed to load cases.'))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (c: Case) => {
    if (!confirm(`Permanently delete "${c.title}" and all its data?`)) return;
    try {
      await deleteCase(c.id);
      setCases(prev => prev.filter(x => x.id !== c.id));
      toast.success('Case deleted.');
    } catch { toast.error('Failed to delete case.'); }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FolderOpen className="w-6 h-6" style={{ color: '#1e3a5f' }} />
          <h1 className="text-xl font-semibold" style={{ color: '#0f2044' }}>Case History</h1>
        </div>
        <button className="btn-primary text-sm" onClick={() => navigate('/create-case')}>
          + New Case
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="card p-5 shimmer h-24" />)}
        </div>
      ) : cases.length === 0 ? (
        <div className="card p-10 text-center text-slate-400">
          <FolderOpen className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p>No cases found. Create a case or load the demo from the dashboard.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {cases.map(c => (
            <div key={c.id} className="card p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-slate-800">{c.title}</span>
                    {c.is_demo && (
                      <span className="px-1.5 py-0.5 rounded text-xs bg-purple-50 text-purple-600 border border-purple-200">
                        Demo
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 mb-2">
                    Ref: {c.reference_id}
                    {c.incident_date && ` · Incident: ${c.incident_date}`}
                    {' · '}Created: {new Date(c.created_at).toLocaleDateString()}
                  </div>
                  {c.description && (
                    <p className="text-sm text-slate-600 line-clamp-2">{c.description}</p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                    <span>{c.statement_count} statement{c.statement_count !== 1 ? 's' : ''}</span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    className="btn-secondary text-xs"
                    onClick={() => navigate(`/case/${c.id}`)}
                  >
                    <Eye className="w-3.5 h-3.5" /> Open
                  </button>
                  <button
                    className="btn-secondary text-xs"
                    onClick={() => navigate(`/case/${c.id}/results`)}
                  >
                    <BarChart2 className="w-3.5 h-3.5" /> Results
                  </button>
                  <button
                    className="p-2 text-slate-400 hover:text-red-500 border border-slate-200 rounded-lg transition-colors"
                    onClick={() => handleDelete(c)}
                    title="Delete case"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
