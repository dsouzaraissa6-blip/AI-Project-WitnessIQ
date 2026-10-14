// WitnessIQ — Axios API client
import axios from 'axios';
import type { Case, Statement, AnalysisResult, ReviewUpdate } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000, // 2 min — model download can be slow on first run
});

// ─── Cases ────────────────────────────────────────────────────────────────────

export const getCases = () =>
  api.get<{ cases: Case[]; total: number }>('/cases/').then(r => r.data);

export const getCase = (id: number) =>
  api.get<Case>(`/cases/${id}`).then(r => r.data);

export const createCase = (payload: {
  title: string;
  reference_id: string;
  incident_date?: string;
  description?: string;
  is_demo?: boolean;
}) => api.post<Case>('/cases/', payload).then(r => r.data);

export const deleteCase = (id: number) =>
  api.delete(`/cases/${id}`);

// ─── Statements ───────────────────────────────────────────────────────────────

export const getStatements = (caseId: number) =>
  api.get<Statement[]>(`/cases/${caseId}/statements/`).then(r => r.data);

export const addStatement = (caseId: number, payload: {
  witness_label: string;
  content: string;
  filename?: string;
}) => api.post<Statement>(`/cases/${caseId}/statements/`, payload).then(r => r.data);

export const uploadStatement = (caseId: number, witnessLabel: string, file: File) => {
  const form = new FormData();
  form.append('witness_label', witnessLabel);
  form.append('file', file);
  return api.post<Statement>(`/cases/${caseId}/statements/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export const deleteStatement = (caseId: number, statementId: number) =>
  api.delete(`/cases/${caseId}/statements/${statementId}`);

// ─── Analysis ─────────────────────────────────────────────────────────────────

export const runAnalysis = (caseId: number) =>
  api.post<AnalysisResult>(`/cases/${caseId}/analyze`).then(r => r.data);

export const getAnalysis = (caseId: number) =>
  api.get<AnalysisResult>(`/cases/${caseId}/analysis`).then(r => r.data);

// ─── Review ───────────────────────────────────────────────────────────────────

export const submitReview = (caseId: number, discrepancyId: string, payload: ReviewUpdate) =>
  api.post(`/cases/${caseId}/analysis/review/${discrepancyId}`, payload).then(r => r.data);

// ─── Reports ──────────────────────────────────────────────────────────────────

export const getReportUrl = (caseId: number, format: 'csv' | 'pdf') =>
  `/api/v1/cases/${caseId}/report?format=${format}`;

// ─── Demo ─────────────────────────────────────────────────────────────────────

export const loadDemo = () =>
  api.post<{ case_id: number; message: string; statement_count: number }>('/demo/load').then(r => r.data);
