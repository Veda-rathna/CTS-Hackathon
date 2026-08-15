import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, ShieldCheck, Database, Bot, Sparkles } from 'lucide-react';

const STEPS = [
  { label: 'Validating Prior Authorization Request & Codes', duration: 1500, icon: ShieldCheck },
  { label: 'Resolving Governing CMS NCD/LCD Coverage Policies', duration: 2500, icon: Database },
  { label: 'Running Deterministic SQL Code Matching Engine', duration: 2500, icon: CheckCircle2 },
  { label: 'Orchestrating 4-Agent Semantic Evaluation Pipeline', duration: 4500, icon: Bot },
  { label: 'Fusing Evidence & Adjudicating Final Coverage Decision', duration: 2000, icon: Sparkles },
];

export default function EvaluationLoader({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep < STEPS.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
      }, STEPS[currentStep].duration);
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  return (
    <div className="healthcare-card p-8 bg-white border border-slate-200 text-center space-y-6 max-w-md mx-auto my-8 shadow-md">
      <div className="relative inline-flex items-center justify-center">
        <div className="w-16 h-16 rounded-full bg-sky-50 border-2 border-sky-200 flex items-center justify-center text-sky-600">
          <RefreshCw className="w-8 h-8 animate-spin" />
        </div>
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-800">
          Adjudicating Prior Authorization
        </h3>
        <p className="text-xs text-slate-500">
          Evaluating clinical evidence against CMS Medicare Policies
        </p>
      </div>

      {/* Steps checklist */}
      <div className="space-y-2 text-left pt-2 border-t border-slate-100">
        {STEPS.map((step, idx) => {
          const StepIcon = step.icon;
          const isDone = idx < currentStep;
          const isCurrent = idx === currentStep;

          return (
            <div
              key={idx}
              className={`flex items-center gap-3 p-2.5 rounded-xl text-xs transition-all ${
                isCurrent
                  ? 'bg-sky-50 text-sky-900 border border-sky-200 font-semibold'
                  : isDone
                  ? 'text-emerald-700 font-medium'
                  : 'text-slate-400 opacity-60'
              }`}
            >
              <div className="flex-shrink-0">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : isCurrent ? (
                  <RefreshCw className="w-4 h-4 text-sky-600 animate-spin" />
                ) : (
                  <StepIcon className="w-4 h-4 text-slate-300" />
                )}
              </div>
              <span className="truncate">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
