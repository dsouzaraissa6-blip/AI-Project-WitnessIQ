// About / Methodology page
import { Scale, Cpu, AlertTriangle, BookOpen, GitBranch } from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <BookOpen className="w-6 h-6" style={{ color: '#1e3a5f' }} />
        <h1 className="text-xl font-semibold" style={{ color: '#0f2044' }}>Methodology & Limitations</h1>
      </div>

      <div className="mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <div className="font-semibold text-amber-800 mb-1">Important Disclaimer</div>
            <p className="text-sm text-amber-700">
              WitnessIQ is an investigative document-assistance tool. It does not determine
              guilt, assess credibility, or establish what actually happened. All automated
              results require human expert review. This system must not be used as the sole
              basis for any investigative or legal conclusion.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-5">
        {/* Overview */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Scale className="w-5 h-5" style={{ color: '#1e3a5f' }} />
            <h2 className="font-semibold text-slate-800">System Overview</h2>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed mb-3">
            WitnessIQ applies Natural Language Processing (NLP) and machine learning techniques
            to extract factual claims from witness statements and identify textual differences
            that may warrant investigator attention.
          </p>
          <p className="text-sm text-slate-600 leading-relaxed">
            The system is designed to assist investigators by surfacing potential discrepancies
            in large volumes of text — a task that is time-consuming when performed manually.
            It does not replace human judgement.
          </p>
        </div>

        {/* AI/ML Pipeline */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5" style={{ color: '#1e3a5f' }} />
            <h2 className="font-semibold text-slate-800">AI/ML Pipeline</h2>
          </div>

          <div className="space-y-4">
            <div className="border-l-4 border-blue-400 pl-4">
              <div className="font-medium text-sm text-slate-800 mb-1">
                Step 1: Named Entity Recognition (NER)
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>Model:</strong> spaCy en_core_web_sm (pretrained, CNN-based NER pipeline).<br />
                <strong>Extracts:</strong> PERSON, GPE (geopolitical), LOC, ORG, DATE, TIME, CARDINAL entities.<br />
                <strong>Supplemented by:</strong> Rule-based regex patterns for clothing (color + garment type),
                vehicles (color + vehicle type), location details (entrance/exit/lane), and time expressions.<br />
                <strong>Fallback:</strong> If spaCy is unavailable, the rule-based patterns are used alone.
              </p>
            </div>

            <div className="border-l-4 border-indigo-400 pl-4">
              <div className="font-medium text-sm text-slate-800 mb-1">
                Step 2: Semantic Similarity
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>Model:</strong> all-MiniLM-L6-v2 (sentence-transformers library, pretrained on natural language inference data).<br />
                <strong>Method:</strong> Sentences from each pair of statements are embedded into 384-dimensional vectors.
                Cosine similarity is computed for all sentence pairs.<br />
                <strong>Threshold:</strong> 0.50 (configurable). Pairs above this threshold are considered potentially related.<br />
                <strong>Fallback:</strong> If sentence-transformers is unavailable, TF-IDF cosine similarity is used.<br />
                <strong>IMPORTANT:</strong> Similarity scores measure linguistic relatedness, not factual consistency.
                A high score does not mean the sentences agree; a low score does not mean they contradict each other.
              </p>
            </div>

            <div className="border-l-4 border-green-400 pl-4">
              <div className="font-medium text-sm text-slate-800 mb-1">
                Step 3: Structured Fact Comparison
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>Method:</strong> Deterministic rule-based comparison of extracted entity values.<br />
                <strong>Time comparison:</strong> Times are normalized to minutes-since-midnight and compared.
                Differences ≤10 minutes are classified as "difference for review" (approximation is common).
                Differences &gt;10 minutes in related sentences are classified as "potential inconsistency".<br />
                <strong>Attribute comparison:</strong> Colors, clothing items, and vehicle descriptions are
                compared using exact and fuzzy matching (grey/gray treated as equivalent).<br />
                <strong>Location details:</strong> Entrance/exit/lane references are compared across statements.
              </p>
            </div>

            <div className="border-l-4 border-amber-400 pl-4">
              <div className="font-medium text-sm text-slate-800 mb-1">
                Step 4: Classification and Explanation
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Each flagged item is assigned one of five classifications:
              </p>
              <ul className="text-xs text-slate-600 mt-1 space-y-0.5 list-disc list-inside">
                <li><strong>Potential Inconsistency:</strong> Related claims with differing factual values.</li>
                <li><strong>Difference Requiring Review:</strong> Values differ but relatedness is uncertain, or the difference is small.</li>
                <li><strong>One Witness Only:</strong> A detail mentioned by only one witness.</li>
                <li><strong>Similar:</strong> Matching or near-identical values across statements.</li>
                <li><strong>Ambiguous:</strong> Insufficient information to compare.</li>
              </ul>
              <p className="text-xs text-slate-500 mt-2">
                Every result includes the source sentences, extracted values, detection method, and explanation.
              </p>
            </div>
          </div>
        </div>

        {/* Limitations */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-5 h-5" style={{ color: '#1e3a5f' }} />
            <h2 className="font-semibold text-slate-800">Known Limitations</h2>
          </div>
          <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
            <li>Entity extraction accuracy depends on sentence structure and vocabulary.</li>
            <li>The system cannot determine whether two witnesses observed the same person or event.</li>
            <li>Paraphrase detection depends on the semantic similarity threshold; some related sentences may not be matched.</li>
            <li>Negations are extracted but not deeply reasoned about (e.g., "did not see" vs. "saw").</li>
            <li>Numbers not following recognised patterns (e.g., written-out numbers) may not be parsed.</li>
            <li>Context-dependent ambiguity (e.g., approximate times) is partially addressed but not fully resolved.</li>
            <li>No contradiction classifier model is integrated; discrepancies rely on rule-based comparison and semantic proximity.</li>
            <li>The system has not been validated against ground-truth investigative datasets.</li>
          </ul>
        </div>

        {/* Tech stack */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-800 mb-3">Technology Stack</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            {[
              { name: 'React + Vite', role: 'Frontend framework' },
              { name: 'TypeScript', role: 'Type safety' },
              { name: 'Tailwind CSS', role: 'Styling' },
              { name: 'FastAPI', role: 'REST API' },
              { name: 'Python 3.11+', role: 'Backend runtime' },
              { name: 'spaCy', role: 'NER pipeline' },
              { name: 'sentence-transformers', role: 'Semantic embeddings' },
              { name: 'SQLite + SQLAlchemy', role: 'Persistence' },
              { name: 'Pydantic v2', role: 'Data validation' },
            ].map(t => (
              <div key={t.name} className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                <div className="font-medium text-slate-700">{t.name}</div>
                <div className="text-slate-500">{t.role}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
