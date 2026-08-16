import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  HelpCircle, 
  XCircle, 
  Activity, 
  Database, 
  BrainCircuit, 
  Search, 
  FileText, 
  Cpu, 
  CheckCircle2, 
  Clock, 
  ChevronRight,
  ExternalLink,
  Sparkles
} from 'lucide-react';
import confetti from 'canvas-confetti';

const PRESETS = [
  {
    id: 'esi-covered',
    label: '💉 Epidural Injection (LCD 36920)',
    procedure_code: '64483',
    diagnosis_codes: 'M54.16',
    state: 'TX',
    patient_age: 55,
    clinical_notes: 'Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy was tried for 8 weeks without relief.',
  },
  {
    id: 'hcv-screening',
    label: '🩺 Hepatitis C Screening (NCD 361 RAG)',
    procedure_code: '87556',
    diagnosis_codes: 'Z11.59',
    state: 'TX',
    patient_age: 52,
    clinical_notes: 'Screening for Hepatitis C Virus (HCV) in asymptomatic high-risk adult patient. Patient was born between 1945 and 1965 with history of blood transfusion.',
  },
  {
    id: 'breast-reconstruction',
    label: '🎗️ Breast Reconstruction (NCD 64 RAG)',
    procedure_code: '11952',
    diagnosis_codes: 'C50.919',
    state: 'TX',
    patient_age: 48,
    clinical_notes: 'Patient with breast cancer undergoing breast reconstruction following radical mastectomy. Surgical pathology confirmed invasive ductal carcinoma.',
  },
  {
    id: 'trigger-point-noncovered',
    label: '❌ Joint Pain (LCD 39662 Excluded)',
    procedure_code: '20552',
    diagnosis_codes: 'M25.50',
    state: 'TX',
    patient_age: 40,
    clinical_notes: 'Routine consultation for general unspecified joint pain without muscle trigger points.',
  },
  {
    id: 'outside-jurisdiction',
    label: '🗺️ Outside Jurisdiction (CA)',
    procedure_code: '64483',
    diagnosis_codes: 'M54.17',
    state: 'CA',
    patient_age: 63,
    clinical_notes: 'Lumbosacral radiculopathy.',
  },
];

export default function App() {
  const [procedureCode, setProcedureCode] = useState('64483');
  const [diagnosisCodes, setDiagnosisCodes] = useState('M54.16');
  const [state, setState] = useState('TX');
  const [patientAge, setPatientAge] = useState(55);
  const [clinicalNotes, setClinicalNotes] = useState(
    'Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy was tried for 8 weeks without relief.'
  );
  
  const [loading, setLoading] = useState(false);
  const [activePreset, setActivePreset] = useState('esi-covered');
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('criteria');
  const [apiConnected, setApiConnected] = useState(true);

  const applyPreset = (preset) => {
    setActivePreset(preset.id);
    setProcedureCode(preset.procedure_code);
    setDiagnosisCodes(preset.diagnosis_codes);
    setState(preset.state);
    setPatientAge(preset.patient_age);
    setClinicalNotes(preset.clinical_notes);
  };

  const handleTriage = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    const payload = {
      procedure_code: procedureCode.trim(),
      diagnosis_codes: diagnosisCodes.split(',').map((c) => c.trim()).filter(Boolean),
      state: state || null,
      patient_age: patientAge ? parseInt(patientAge, 10) : null,
      clinical_notes: clinicalNotes.trim() || null,
    };

    try {
      const res = await fetch('/api/v1/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`API Error (${res.status}): ${errText}`);
      }

      const data = await res.json();
      setResponse(data);
      setApiConnected(true);

      if (data.decision === 'APPROVE') {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 }
        });
      }
    } catch (err) {
      console.error('Triage request failed:', err);
      setError(err.message);
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision) => {
    switch (decision) {
      case 'APPROVE':
        return <ShieldCheck className="w-8 h-8 text-emerald-400" />;
      case 'PEND':
        return <AlertTriangle className="w-8 h-8 text-amber-400" />;
      case 'REQUEST_MORE_INFORMATION':
        return <HelpCircle className="w-8 h-8 text-blue-400" />;
      case 'DENY':
        return <XCircle className="w-8 h-8 text-rose-400" />;
      default:
        return <Activity className="w-8 h-8 text-slate-400" />;
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Bar */}
      <header className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <BrainCircuit className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Prior Authorization Triage & Policy Companion
            </h1>
            <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
              <span>CMS Coverage Decision Engine</span>
              <span>•</span>
              <span className="text-cyan-400 font-medium">Bedrock Qwen LLM</span>
              <span>•</span>
              <span className="text-emerald-400 font-medium">Neon PostgreSQL pgvector</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/60 border border-slate-800 text-xs">
            <span className={`w-2.5 h-2.5 rounded-full ${apiConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-medium">{apiConnected ? 'API Connected' : 'API Offline'}</span>
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-semibold transition"
          >
            <span>Swagger API</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form & Presets */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-panel p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" />
                Clinical Case Presets
              </h2>
            </div>

            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className={`btn-preset ${activePreset === p.id ? 'active' : ''}`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleTriage} className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    HCPCS Procedure Code
                  </label>
                  <input
                    type="text"
                    required
                    value={procedureCode}
                    onChange={(e) => setProcedureCode(e.target.value)}
                    placeholder="e.g. 64483, 87556"
                    className="input-field font-mono font-semibold text-cyan-300"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    State Jurisdiction
                  </label>
                  <select
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="input-field font-mono font-semibold text-slate-200"
                  >
                    <option value="TX font-mono">TX (Texas)</option>
                    <option value="CA">CA (California)</option>
                    <option value="FL">FL (Florida)</option>
                    <option value="NY">NY (New York)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    ICD-10 Diagnosis Code(s)
                  </label>
                  <input
                    type="text"
                    required
                    value={diagnosisCodes}
                    onChange={(e) => setDiagnosisCodes(e.target.value)}
                    placeholder="e.g. M54.16, Z11.59"
                    className="input-field font-mono text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Patient Age
                  </label>
                  <input
                    type="number"
                    value={patientAge}
                    onChange={(e) => setPatientAge(e.target.value)}
                    placeholder="55"
                    className="input-field text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Clinical Documentation / Notes
                </label>
                <textarea
                  rows={4}
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  placeholder="Enter patient history, MRI findings, conservative therapy..."
                  className="input-field"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full justify-center py-3.5 text-base mt-4"
              >
                {loading ? (
                  <>
                    <Activity className="w-5 h-5 animate-spin" />
                    <span>Evaluating Policy Matrix...</span>
                  </>
                ) : (
                  <>
                    <BrainCircuit className="w-5 h-5" />
                    <span>Evaluate Prior Authorization</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Output & Dashboard */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="glass-panel p-6 border-rose-500/40 bg-rose-950/20 text-rose-300 flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-rose-200">Evaluation Error</h3>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          {!response && !error && !loading && (
            <div className="glass-panel p-12 text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto text-cyan-400">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-semibold text-slate-200">Ready for Evaluation</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Select a preset or enter custom procedure & diagnosis codes to run the 2-Layer Hybrid Decision Engine.
              </p>
            </div>
          )}

          {response && (
            <div className="space-y-6">
              {/* Decision Header Banner */}
              <div className={`decision-card ${response.decision}`}>
                {getDecisionIcon(response.decision)}
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-extrabold tracking-wide uppercase">
                      {response.decision}
                    </span>
                    <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-900/60 border border-white/10 text-slate-300">
                      Score: {(response.evidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 font-medium leading-relaxed">
                    {response.reason}
                  </p>
                </div>
              </div>

              {/* Policy Identification Metadata */}
              <div className="glass-panel p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 block font-semibold uppercase">NCD Policy</span>
                  <span className="font-mono text-cyan-300 font-bold">
                    {response.policy_path?.ncd?.policy_id || 'NOT_ADDRESSED'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block font-semibold uppercase">LCD Policy</span>
                  <span className="font-mono text-cyan-300 font-bold">
                    {response.policy_path?.lcd?.policy_id || 'NOT_ADDRESSED'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block font-semibold uppercase">Article</span>
                  <span className="font-mono text-cyan-300 font-bold">
                    {response.policy_path?.article?.policy_id || 'NOT_ADDRESSED'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block font-semibold uppercase">Jurisdiction</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {response.policy_path?.jurisdiction?.result || 'NOT_ADDRESSED'}
                  </span>
                </div>
              </div>

              {/* Detail Inspector Tabs */}
              <div className="glass-panel p-6 space-y-6">
                <div className="flex border-b border-slate-800 gap-6">
                  <button
                    onClick={() => setActiveTab('criteria')}
                    className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                      activeTab === 'criteria'
                        ? 'border-cyan-400 text-cyan-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <FileText className="w-4 h-4" />
                    Evaluated Criteria ({response.criteria?.length || 0})
                  </button>

                  <button
                    onClick={() => setActiveTab('rag')}
                    className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                      activeTab === 'rag'
                        ? 'border-cyan-400 text-cyan-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Database className="w-4 h-4" />
                    RAG Vector Evidence ({response.rag_evidence?.length || 0})
                  </button>

                  <button
                    onClick={() => setActiveTab('json')}
                    className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                      activeTab === 'json'
                        ? 'border-cyan-400 text-cyan-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Cpu className="w-4 h-4" />
                    Raw Payload
                  </button>
                </div>

                {/* Tab 1: Criteria */}
                {activeTab === 'criteria' && (
                  <div className="space-y-4">
                    {response.criteria?.length === 0 ? (
                      <p className="text-sm text-slate-400 italic">No formal criteria were generated for this policy path.</p>
                    ) : (
                      response.criteria?.map((c, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-3">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className={`eval-type-badge ${c.evaluator}`}>{c.evaluator}</span>
                              <span className="font-mono text-xs font-semibold text-slate-300">{c.criterion_id}</span>
                            </div>
                            <span className={`status-badge ${c.status}`}>{c.status}</span>
                          </div>

                          <p className="text-sm font-medium text-slate-200">{c.criterion}</p>

                          {c.explanation && (
                            <p className="text-xs text-slate-400 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 font-mono">
                              {c.explanation}
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Tab 2: RAG Vector Evidence */}
                {activeTab === 'rag' && (
                  <div className="space-y-4">
                    {!response.rag_evidence || response.rag_evidence.length === 0 ? (
                      <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
                        <Database className="w-6 h-6 text-slate-500 mx-auto" />
                        <p className="text-sm text-slate-300 font-medium">RAG Vector Retrieval: Bypassed</p>
                        <p className="text-xs text-slate-500">
                          Coverage was resolved deterministically by SQL code table matching without requiring unstructured text chunk search.
                        </p>
                      </div>
                    ) : (
                      response.rag_evidence.map((rag, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-mono font-semibold text-cyan-300">
                              {rag.policy_type} {rag.policy_id} — {rag.section || 'Coverage Indications'}
                            </span>
                            <span className="font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                              Similarity: {(rag.similarity_score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                            "{rag.text}"
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Tab 3: JSON Payload */}
                {activeTab === 'json' && (
                  <pre className="p-4 rounded-xl bg-slate-950 font-mono text-xs text-cyan-300 overflow-x-auto max-h-96 border border-slate-800">
                    {JSON.stringify(response, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
