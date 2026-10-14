// Case Workspace page — view statements, add new ones, run analysis
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Plus, Trash2, Upload, BarChart2, FileText, AlertTriangle, CheckCircle
} from 'lucide-react';
import {
  getCase, getStatements, addStatement, uploadStatement, deleteStatement, runAnalysis
} from '../api/client';
import type { Case, Statement } from '../types';
import toast from 'react-hot-toast';

const DEFAULT_LABELS = ['Witness A', 'Witness B', 'Witness C', 'Witness D', 'Witness E'];

export default function CaseWorkspace() {
  const { id } = useParams<{ id: string }>();
  const caseId = Number(id);
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Add statement form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newContent, setNewContent] = useState('');
  const [addMode, setAddMode] = useState<'text' | 'file'>('text');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [addLoading, setAddLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([getCase(caseId), getStatements(caseId)])
      .then(([c, s]) => { setCaseData(c); setStatements(s); })
      .catch(() => toast.error('Failed to load case data.'))
      .finally(() => setLoading(false));
  }, [caseId]);

  const nextLabel = () => {
    const used = new Set(statements.map(s => s.witness_label));
    return DEFAULT_LABELS.find(l => !used.has(l)) ?? `Witness ${statements.length + 1}`;
  };

  const handleAddStatement = async (e: React.FormEvent) => {
    e.preventDefault();
    const label = newLabel.trim() || nextLabel();

    if (addMode === 'text') {
      if (!newContent.trim() || newContent.trim().length < 10) {
        toast.error('Statement must be at least 10 characters.');
        return;
      }
      setAddLoading(true);
      try {
        const stmt = await addStatement(caseId, { witness_label: label, content: newContent.trim() });
        setStatements(s => [...s, stmt]);
        setNewContent('');
        setNewLabel('');
        setShowAddForm(false);
        toast.success(`${label}'s statement added.`);
      } catch { toast.error('Failed to add statement.'); }
      finally { setAddLoading(false); }
    } else {
      if (!selectedFile) { toast.error('Please select a file.'); return; }
      setAddLoading(true);
      try {
        const stmt = await uploadStatement(caseId, label, selectedFile);
        setStatements(s => [...s, stmt]);
        setSelectedFile(null);
        setNewLabel('');
        setShowAddForm(false);
        toast.success(`${label}'s statement uploaded.`);
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        toast.error(msg || 'Failed to upload file.');
      } finally { setAddLoading(false); }
    }
  };

  const handleDeleteStatement = async (stmt: Statement) => {
    if (!confirm(`Remove ${stmt.witness_label}'s statement?`)) return;
    try {
      await deleteStatement(caseId, stmt.id);
      setStatements(s => s.filter(x => x.id !== stmt.id));
      toast.success('Statement removed.');
    } catch { toast.error('Failed to remove statement.'); }
  };

  const handleAnalyze = async () => {
    if (statements.length < 2) {
      toast.error('Add at least two witness statements before analyzing.');
      return;
    }
    setAnalyzing(true);
    const toastId = toast.loading('Running AI analysis… This may take a moment on first run while models load.');
    try {
      await runAnalysis(caseId);
      toast.dismiss(toastId);
      toast.success('Analysis complete.');
      navigate(`/case/${caseId}/results`);
    } catch (err: unknown) {
      toast.dismiss(toastId);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || 'Analysis failed. Check backend logs.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-4">
        {[1,2,3].map(i => <div key={i} className="card p-6 shimmer h-32" />)}
      </div>
    );
  }

  if (!caseData) return <div className="p-8 text-center text-slate-500">Case not found.</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Back */}
      <button className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 mb-5" onClick={() => navigate('/')}>
        <ArrowLeft className="w-4 h-4" /> Dashboard
      </button>

      {/* Case header */}
      <div className="card p-5 mb-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-xl font-semibold" style={{ color: '#0f2044' }}>{caseData.title}</h1>
              {caseData.is_demo && (
                <span className="px-2 py-0.5 rounded text-xs bg-purple-50 text-purple-600 border border-purple-200">
                  Demo — Fictional Data
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 mb-2">Ref: {caseData.reference_id}
              {caseData.incident_date && ` · Date: ${caseData.incident_date}`}
            </div>
            {caseData.description && (
              <p className="text-sm text-slate-600">{caseData.description}</p>
            )}
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              className="btn-secondary text-sm"
              onClick={() => navigate(`/case/${caseId}/results`)}
            >
              <BarChart2 className="w-4 h-4" /> Results
            </button>
            <button
              className="btn-primary text-sm"
              onClick={handleAnalyze}
              disabled={analyzing || statements.length < 2}
              title={statements.length < 2 ? 'Add at least 2 statements first' : ''}
            >
              <BarChart2 className="w-4 h-4" />
              {analyzing ? 'Analyzing…' : 'Analyze Statements'}
            </button>
          </div>
        </div>
      </div>

      {/* Analysis requirement notice */}
      {statements.length < 2 && (
        <div className="mb-5 p-3 rounded-lg border border-blue-200 bg-blue-50 flex items-center gap-2 text-xs text-blue-700">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          Add at least two witness statements to enable analysis.
        </div>
      )}
      {statements.length >= 2 && (
        <div className="mb-5 p-3 rounded-lg border border-green-200 bg-green-50 flex items-center gap-2 text-xs text-green-700">
          <CheckCircle className="w-4 h-4 shrink-0" />
          {statements.length} statements ready. Click "Analyze Statements" to begin.
        </div>
      )}

      {/* Statements grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {statements.map(stmt => (
          <div key={stmt.id} className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-400" />
                <span className="font-medium text-sm text-slate-800">{stmt.witness_label}</span>
                {stmt.filename && (
                  <span className="text-xs text-slate-400">{stmt.filename}</span>
                )}
              </div>
              <button
                className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                onClick={() => handleDeleteStatement(stmt)}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed line-clamp-6 whitespace-pre-wrap">
              {stmt.content}
            </p>
            <div className="mt-2 text-xs text-slate-400">
              {stmt.content.split(/[.!?]+/).filter(Boolean).length} sentence(s) · {stmt.content.split(/\s+/).length} words
            </div>
          </div>
        ))}

        {/* Add statement card */}
        {!showAddForm && (
          <button
            className="card p-4 border-dashed border-2 border-slate-200 text-slate-400 hover:border-blue-300 hover:text-blue-500 transition-all text-sm flex flex-col items-center justify-center min-h-32 gap-2"
            onClick={() => { setShowAddForm(true); setNewLabel(nextLabel()); }}
          >
            <Plus className="w-6 h-6" />
            Add Witness Statement
          </button>
        )}
      </div>

      {/* Add statement form */}
      {showAddForm && (
        <div className="card p-5 mb-6">
          <h3 className="font-medium text-sm text-slate-800 mb-4">Add Witness Statement</h3>
          <form onSubmit={handleAddStatement} className="space-y-3">
            <div>
              <label className="label" htmlFor="witness-label">Witness Label</label>
              <input
                id="witness-label"
                className="input-field"
                value={newLabel}
                onChange={e => setNewLabel(e.target.value)}
                placeholder="e.g. Witness A"
              />
            </div>

            {/* Mode toggle */}
            <div className="flex gap-2">
              <button
                type="button"
                className={`px-3 py-1.5 text-xs rounded-md border ${addMode === 'text' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
                onClick={() => setAddMode('text')}
              >
                Paste Text
              </button>
              <button
                type="button"
                className={`px-3 py-1.5 text-xs rounded-md border flex items-center gap-1 ${addMode === 'file' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
                onClick={() => setAddMode('file')}
              >
                <Upload className="w-3 h-3" /> Upload File (.txt / .pdf)
              </button>
            </div>

            {addMode === 'text' ? (
              <textarea
                className="input-field min-h-32 resize-y text-xs"
                placeholder="Paste the witness statement here…"
                value={newContent}
                onChange={e => setNewContent(e.target.value)}
              />
            ) : (
              <div>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".txt,.pdf"
                  className="hidden"
                  onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
                />
                <button
                  type="button"
                  className="btn-secondary text-xs"
                  onClick={() => fileRef.current?.click()}
                >
                  <Upload className="w-3 h-3" />
                  {selectedFile ? selectedFile.name : 'Choose file…'}
                </button>
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <button type="submit" className="btn-primary text-xs" disabled={addLoading}>
                {addLoading ? 'Adding…' : 'Add Statement'}
              </button>
              <button
                type="button"
                className="btn-secondary text-xs"
                onClick={() => { setShowAddForm(false); setNewContent(''); setSelectedFile(null); }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
