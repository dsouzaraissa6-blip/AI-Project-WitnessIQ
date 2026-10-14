// Classification badge component
import type { Classification, ReviewStatus } from '../types';

export function ClassificationBadge({ classification }: { classification: Classification }) {
  const map: Record<Classification, { label: string; className: string }> = {
    potential_inconsistency: { label: 'Potential Inconsistency', className: 'badge-inconsistency' },
    difference_for_review: { label: 'Difference — Review', className: 'badge-review' },
    one_witness_only: { label: 'One Witness Only', className: 'badge-one-witness' },
    similar: { label: 'Similar', className: 'badge-similar' },
    ambiguous: { label: 'Ambiguous', className: 'badge-ambiguous' },
  };
  const { label, className } = map[classification] ?? { label: classification, className: 'badge-ambiguous' };
  return <span className={className}>{label}</span>;
}

export function ReviewBadge({ status }: { status: ReviewStatus }) {
  if (!status) return <span className="badge-ambiguous">Pending Review</span>;
  const map: Record<string, { label: string; className: string }> = {
    relevant: { label: 'Relevant Discrepancy', className: 'badge-inconsistency' },
    not_meaningful: { label: 'Not Meaningful', className: 'badge-similar' },
    needs_investigation: { label: 'Needs Investigation', className: 'badge-review' },
    uncertain: { label: 'Uncertain', className: 'badge-ambiguous' },
  };
  const { label, className } = map[status] ?? { label: status, className: 'badge-ambiguous' };
  return <span className={className}>{label}</span>;
}

export function MethodBadge({ method }: { method: string }) {
  const label = method === 'rule_based' ? 'Rule-based' :
    method === 'sentence_transformer' ? 'ML Model' :
    method === 'ml_assisted' ? 'ML Assisted' :
    method === 'tfidf_cosine' ? 'TF-IDF' : method;
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-slate-100 text-slate-600 border border-slate-200">
      {label}
    </span>
  );
}
