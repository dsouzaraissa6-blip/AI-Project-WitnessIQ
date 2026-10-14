// Analysis Results page — the main analysis display
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, Filter, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, Info, Eye, Zap, FileText
} from 'lucide-react';
import { getCase, getAnalysis, submitReview, getReportUrl } from '../api/client';
import type { Case, AnalysisResult, DiscrepancyItem, Classification, ReviewStatus } from '../types';
import { ClassificationBadge, ReviewBadge, MethodBadge } from '../components/Badges';
import toast from 'react-hot-toast';

const FILTERS: { label: string; value: Classification | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Potential Inconsistencies', value: 'potential_inconsistency' },
  { label: 'Differences', value: 'difference_for_review' },
  { label: 'One Witness', value: 'one_witness_only' },
  { label: 'Similar', value: 'similar' },
];

function SummaryCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: React.ElementType; color: string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
        <Icon className="w-4 h-4" style={{ color }} />
        {label}
      </div>
      <div className="text-2xl font-bold" style={{ color: '#0f2044' }}>{value}</div>
    </div>
  );
}

function DiscrepancyCard({ disc, onReview }: {
  disc: DiscrepancyItem;
  onReview: (id: string, decision: ReviewStatus, note: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [decision, setDecision] = useState<ReviewStatus>(disc.review_status ?? null);
  const [note, setNote] = useState(disc.review_note ?? '');
  const [saving, setSaving] = useState(false);

  const handleSaveReview = async () => {
    if (!decision) { toast.error('Select a decision first.'); return; }
    setSaving(true);
    try {
      await onReview(disc.id, decision, note);
      setShowReview(false);
      toast.success('Review saved.');
    } catch {
      toast.error('Failed to save review. Please try again.');
    } finally { setSaving(false); }
  };

  const isIssue = disc.classification === 'potential_inconsistency' || disc.classification === 'difference_for_review';

  return (
    <div className={`card overflow-hidden ${isIssue ? 'border-l-4 border-l-amber-400' : ''}`}>
      {/* Header row */}
      <div
        className="p-4 cursor-pointer hover:bg-slate-50 flex items-start gap-3"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{disc.category}</span>
            <ClassificationBadge classification={disc.classification} />
            <MethodBadge method={disc.detection_method} />
            {disc.similarity_score != null && (
              <span className="text-xs text-slate-400">
                sim: {(disc.similarity_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          {/* A vs B values */}
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium text-slate-700">{disc.witness_a_label}:</span>
            <span className={`px-2 py-0.5 rounded text-xs ${disc.classification === 'similar' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {disc.witness_a_text || '(not mentioned)'}
            </span>
            {disc.witness_b_text && disc.witness_b_text !== '(not mentioned)' && (
              <>
                <span className="text-slate-400">vs</span>
                <span className="font-medium text-slate-700">{disc.witness_b_label}:</span>
                <span className={`px-2 py-0.5 rounded text-xs ${disc.classification === 'similar' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
                  {disc.witness_b_text}
                </span>
              </>
            )}
          </div>
          {disc.review_status && (
            <div className="mt-1">
              <ReviewBadge status={disc.review_status} />
            </div>
          )}
        </div>
        <div className="shrink-0 text-slate-400">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-100 p-4 space-y-4">
          {/* Explanation */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <p className="text-xs text-slate-600 leading-relaxed">{disc.explanation}</p>
          </div>

          {/* Source passages side by side */}
          {(disc.witness_a_sentence || disc.witness_b_sentence) && (
            <div>
              <div className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wider">Source Passages</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {disc.witness_a_sentence && (
                  <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                    <div className="text-xs font-medium text-blue-600 mb-1">{disc.witness_a_label}</div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      "{disc.witness_a_sentence}"
                    </p>
                  </div>
                )}
                {disc.witness_b_sentence && disc.witness_b_sentence !== '' && (
                  <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
                    <div className="text-xs font-medium text-indigo-600 mb-1">{disc.witness_b_label}</div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      "{disc.witness_b_sentence}"
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Review */}
          <div className="border-t border-slate-100 pt-3">
            {!showReview ? (
              <button
                className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800"
                onClick={() => setShowReview(true)}
              >
                <Eye className="w-3.5 h-3.5" />
                {disc.review_status ? 'Update Review Decision' : 'Add Review Decision'}
              </button>
            ) : (
              <div className="space-y-3">
                <div className="text-xs font-medium text-slate-600">Human Review Decision</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: 'relevant', label: 'Relevant Discrepancy' },
                    { value: 'not_meaningful', label: 'Not Meaningful' },
                    { value: 'needs_investigation', label: 'Needs Investigation' },
                    { value: 'uncertain', label: 'Uncertain' },
                  ].map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`px-3 py-1 text-xs rounded-md border transition-colors ${
                        decision === opt.value
                          ? 'bg-slate-800 text-white border-slate-800'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                      onClick={() => setDecision(opt.value as ReviewStatus)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <textarea
                  className="input-field text-xs min-h-16"
                  placeholder="Optional note…"
                  value={note}
                  onChange={e => setNote(e.target.value)}
                />
                <div className="flex gap-2">
                  <button
                    className="btn-primary text-xs py-1.5"
                    onClick={handleSaveReview}
                    disabled={saving}
                  >
                    {saving ? 'Saving…' : 'Save Decision'}
                  </button>
                  <button
                    className="btn-secondary text-xs py-1.5"
                    onClick={() => setShowReview(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            {disc.review_note && (
              <div className="mt-2 text-xs text-slate-500 italic">Note: {disc.review_note}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalysisResults() {
  const { id } = useParams<{ id: string }>();
  const caseId = Number(id);
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Classification | 'all'>('all');
  const [activeTab, setActiveTab] = useState<'discrepancies' | 'facts' | 'semantic' | 'model'>('discrepancies');

  useEffect(() => {
    Promise.all([getCase(caseId), getAnalysis(caseId)])
      .then(([c, a]) => { setCaseData(c); setAnalysis(a); })
      .catch(() => {
        toast.error('No analysis found. Run analysis from the workspace first.');
        navigate(`/case/${caseId}`);
      })
      .finally(() => setLoading(false));
  }, [caseId]);

  const handleReview = async (discrepancyId: string, decision: ReviewStatus, note: string) => {
    if (!decision) return;
    await submitReview(caseId, discrepancyId, { decision, note });
    setAnalysis(a => {
      if (!a) return a;
      return {
        ...a,
        discrepancies: a.discrepancies.map(d =>
          d.id === discrepancyId ? { ...d, review_status: decision, review_note: note } : d
        ),
      };
    });
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-4">
        {[1,2,3,4].map(i => <div key={i} className="card p-6 shimmer h-24" />)}
      </div>
    );
  }

  if (!analysis || !caseData) return null;

  const filtered = filter === 'all'
    ? analysis.discrepancies
    : analysis.discrepancies.filter(d => d.classification === filter);

  // Group extracted facts by witness
  const factsByWitness = analysis.extracted_facts.reduce<Record<string, typeof analysis.extracted_facts>>((acc, f) => {
    (acc[f.witness_label] ??= []).push(f);
    return acc;
  }, {});

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <button
            className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 shrink-0"
            onClick={() => navigate(`/case/${caseId}`)}
          >
            <ArrowLeft className="w-4 h-4" /> Workspace
          </button>
          <span className="text-slate-300">/</span>
          <h1 className="text-base font-semibold text-slate-800 truncate">{caseData.title} — Results</h1>
        </div>
        <div className="flex gap-2 shrink-0">
          <a
            href={getReportUrl(caseId, 'csv')}
            className="btn-secondary text-xs"
            download
          >
            <Download className="w-3.5 h-3.5" /> CSV
          </a>
        </div>
      </div>

      {/* Demo label */}
      {caseData.is_demo && (
        <div className="mb-5 p-2.5 rounded-lg border border-purple-200 bg-purple-50 text-xs text-purple-700">
          This is a demonstration case using entirely fictional data for illustration purposes.
        </div>
      )}

      {/* Disclaimer */}
      <div className="mb-5 p-3 rounded-lg border border-amber-200 bg-amber-50 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-800">
          Results are automated observations for investigator review only. This system does not
          determine credibility, guilt, or factual accuracy. All flagged items require human judgement.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <SummaryCard label="Statements" value={analysis.summary.statements_analyzed} icon={FileText} color="#1e3a5f" />
        <SummaryCard label="Related Pairs" value={analysis.summary.related_pairs_found} icon={Zap} color="#6366f1" />
        <SummaryCard label="Discrepancies" value={analysis.summary.discrepancies_flagged} icon={AlertTriangle} color="#d97706" />
        <SummaryCard label="Unique Details" value={analysis.summary.unique_details_count} icon={Info} color="#059669" />
      </div>

      {/* Method info bar */}
      <div className="mb-5 p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-2 text-xs text-slate-600">
        <CheckCircle className="w-4 h-4 text-slate-400 shrink-0" />
        <span><strong>Analysis method:</strong> {analysis.summary.analysis_method}</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200 mb-5">
        {[
          { key: 'discrepancies', label: `Discrepancies (${analysis.discrepancies.length})` },
          { key: 'semantic', label: `Semantic Matches (${analysis.semantic_matches.length})` },
          { key: 'facts', label: `Extracted Facts (${analysis.extracted_facts.length})` },
          { key: 'model', label: 'Model Info' },
        ].map(tab => (
          <button
            key={tab.key}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Discrepancies tab */}
      {activeTab === 'discrepancies' && (
        <div>
          {/* Filter */}
          <div className="flex flex-wrap gap-2 mb-4">
            {FILTERS.map(f => (
              <button
                key={f.value}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  filter === f.value
                    ? 'bg-slate-800 text-white border-slate-800'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
                onClick={() => setFilter(f.value)}
              >
                <Filter className="w-3 h-3 inline mr-1" />
                {f.label}
              </button>
            ))}
          </div>

          {filtered.length === 0 ? (
            <div className="card p-8 text-center text-slate-400">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
              <p className="text-sm">No items match the selected filter.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map(disc => (
                <DiscrepancyCard key={disc.id} disc={disc} onReview={handleReview} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Semantic matches tab */}
      {activeTab === 'semantic' && (
        <div className="space-y-3">
          {analysis.semantic_matches.length === 0 ? (
            <div className="card p-8 text-center text-slate-400 text-sm">
              No semantic matches found above the similarity threshold.
            </div>
          ) : (
            analysis.semantic_matches.map((m, i) => (
              <div key={i} className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <MethodBadge method={m.match_method} />
                  <span className="text-xs text-slate-500">
                    Similarity: <strong>{(m.similarity_score * 100).toFixed(1)}%</strong>
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                    <div className="text-xs font-medium text-blue-600 mb-1">{m.witness_a} (sent. {m.sentence_a_index + 1})</div>
                    <p className="text-xs text-slate-700">"{m.sentence_a}"</p>
                  </div>
                  <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
                    <div className="text-xs font-medium text-indigo-600 mb-1">{m.witness_b} (sent. {m.sentence_b_index + 1})</div>
                    <p className="text-xs text-slate-700">"{m.sentence_b}"</p>
                  </div>
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  Note: Similarity score indicates linguistic relatedness only — not factual agreement or contradiction.
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Extracted facts tab */}
      {activeTab === 'facts' && (
        <div className="space-y-5">
          {Object.entries(factsByWitness).map(([witness, facts]) => (
            <div key={witness} className="card p-4">
              <h3 className="font-medium text-sm text-slate-800 mb-3">{witness}</h3>
              <div className="flex flex-wrap gap-2">
                {facts.map((f, i) => (
                  <div key={i} className="group relative">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs border cursor-pointer
                      ${f.entity_type === 'TIME' ? 'bg-blue-50 border-blue-200 text-blue-700' :
                        f.entity_type === 'CLOTHING' ? 'bg-purple-50 border-purple-200 text-purple-700' :
                        f.entity_type === 'VEHICLE' ? 'bg-green-50 border-green-200 text-green-700' :
                        f.entity_type === 'LOCATION_DETAIL' ? 'bg-orange-50 border-orange-200 text-orange-700' :
                        f.entity_type === 'NEGATION' ? 'bg-red-50 border-red-200 text-red-700' :
                        'bg-slate-50 border-slate-200 text-slate-600'}`}
                    >
                      <span className="uppercase tracking-wider text-[10px] opacity-60">{f.entity_type}</span>
                      {f.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Model info tab */}
      {activeTab === 'model' && (
        <div className="card p-5">
          <h3 className="font-medium text-sm text-slate-800 mb-4">AI/ML Model Information</h3>
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="font-medium text-slate-700 mb-2">Named Entity Recognition (NER)</div>
              <div className="space-y-1 text-slate-600">
                <div>Model: {(analysis.model_info as {spacy?: {model?: string; available?: boolean; fallback?: string}})?.spacy?.model ?? 'Not loaded'}</div>
                <div>Status: {(analysis.model_info as {spacy?: {available?: boolean}})?.spacy?.available ? '✓ Active' : `⚠ Unavailable — using rule-based fallback`}</div>
                <div>Extracts: PERSON, GPE, LOC, ORG, DATE, TIME + rule-based patterns for clothing, vehicles, locations</div>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="font-medium text-slate-700 mb-2">Semantic Similarity</div>
              <div className="space-y-1 text-slate-600">
                <div>Model: {(analysis.model_info as {sentence_transformer?: {model_name?: string}})?.sentence_transformer?.model_name ?? 'TF-IDF fallback'}</div>
                <div>Status: {(analysis.model_info as {sentence_transformer?: {available?: boolean}})?.sentence_transformer?.available ? '✓ Active' : `⚠ Unavailable — using TF-IDF cosine similarity`}</div>
                <div>
                  Threshold: {Number((analysis.model_info as { sentence_transformer?: { threshold?: number } })
                    ?.sentence_transformer?.threshold ?? 0.5).toFixed(2)}.
                  Scores indicate linguistic relatedness only.
                </div>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="font-medium text-slate-700 mb-2">Discrepancy Detection</div>
              <div className="space-y-1 text-slate-600">
                <div>Method: Rule-based comparison of extracted entities</div>
                <div>Covers: Time differences (minutes), color/attribute mismatches, location details, vehicle descriptions</div>
                <div>Limitations: Requires entity extraction to succeed. Paraphrase detection depends on similarity threshold.</div>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
              <div className="font-medium text-amber-800 mb-1">Important Limitations</div>
              <ul className="list-disc list-inside space-y-1 text-amber-700">
                <li>Automated flags are observations, not proven contradictions.</li>
                <li>Similarity scores do not measure truthfulness.</li>
                <li>The system cannot determine which witness is correct.</li>
                <li>Results depend on the quality and completeness of entity extraction.</li>
                <li>All results require human expert review.</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
