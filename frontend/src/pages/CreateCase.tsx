// Create Case page
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FolderPlus } from 'lucide-react';
import { createCase } from '../api/client';
import toast from 'react-hot-toast';

export default function CreateCase() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: '',
    reference_id: '',
    incident_date: '',
    description: '',
  });
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.title.trim()) e.title = 'Case title is required.';
    if (!form.reference_id.trim()) e.reference_id = 'Reference ID is required.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      const created = await createCase({
        title: form.title.trim(),
        reference_id: form.reference_id.trim(),
        incident_date: form.incident_date || undefined,
        description: form.description.trim() || undefined,
      });
      toast.success('Case created successfully.');
      navigate(`/case/${created.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || 'Failed to create case.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <button
        className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 mb-6"
        onClick={() => navigate('/')}
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </button>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <FolderPlus className="w-6 h-6" style={{ color: '#1e3a5f' }} />
          <h1 className="text-xl font-semibold" style={{ color: '#0f2044' }}>Create New Case</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label" htmlFor="case-title">Case Title *</label>
            <input
              id="case-title"
              className="input-field"
              placeholder="e.g. Jewellery Store Incident"
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            />
            {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title}</p>}
          </div>

          <div>
            <label className="label" htmlFor="case-ref">Case Reference ID *</label>
            <input
              id="case-ref"
              className="input-field"
              placeholder="e.g. CASE-2026-001"
              value={form.reference_id}
              onChange={e => setForm(f => ({ ...f, reference_id: e.target.value }))}
            />
            {errors.reference_id && <p className="text-xs text-red-600 mt-1">{errors.reference_id}</p>}
          </div>

          <div>
            <label className="label" htmlFor="case-date">Incident Date (if known)</label>
            <input
              id="case-date"
              type="date"
              className="input-field"
              value={form.incident_date}
              onChange={e => setForm(f => ({ ...f, incident_date: e.target.value }))}
            />
          </div>

          <div>
            <label className="label" htmlFor="case-desc">Incident Description</label>
            <textarea
              id="case-desc"
              className="input-field min-h-24 resize-y"
              placeholder="Brief description of the incident under investigation…"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Creating…' : 'Create Case'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate('/')}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
