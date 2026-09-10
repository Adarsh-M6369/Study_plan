import React from 'react';
import { Layers, Sparkles, Loader2, Target, Sliders } from 'lucide-react';

export const DifficultySelector = ({
  difficulty,
  setDifficulty,
  topic,
  setTopic,
  customInstructions,
  setCustomInstructions,
  onGenerate,
  loading,
  hasActiveDoc
}) => {
  const tiers = [
    {
      id: 'Beginner',
      label: 'Beginner',
      desc: 'Direct recall, foundational terminology & intuitive analogies',
      badge: 'Recall & Basics',
      color: 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300'
    },
    {
      id: 'Intermediate',
      label: 'Intermediate',
      desc: 'Application, conceptual synthesis & multi-step deduction',
      badge: 'Application & Analysis',
      color: 'border-sky-500/40 bg-sky-950/20 text-sky-300'
    },
    {
      id: 'Advanced',
      label: 'Advanced',
      desc: 'Edge cases, rigorous mechanisms & challenging distractors',
      badge: 'Deep Mastery & Edge Cases',
      color: 'border-indigo-500/40 bg-indigo-950/20 text-indigo-300'
    }
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-6">
      <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
        <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
          <Sliders className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-100">Generation Parameters</h2>
          <p className="text-xs text-slate-400">Select academic difficulty tier and trigger the LangGraph pipeline</p>
        </div>
      </div>

      {/* Difficulty Tier Radio Cards */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
          <Target className="w-3.5 h-3.5 text-sky-400" />
          <span>Select Academic Difficulty Tier</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {tiers.map((tier) => (
            <button
              key={tier.id}
              type="button"
              onClick={() => setDifficulty(tier.id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                difficulty === tier.id
                  ? 'border-sky-500 bg-sky-500/10 shadow-lg shadow-sky-500/10'
                  : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-sm text-slate-100">{tier.label}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${tier.color}`}>
                  {tier.badge}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{tier.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Topic & Guidance Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Study Guide Title / Focus Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Distributed Systems & Consensus Protocols"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Custom Prompt Guidance (Optional)</label>
          <input
            type="text"
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="e.g. Focus on edge cases and algorithm complexity"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
          />
        </div>
      </div>

      {/* Generate Action Button */}
      <button
        onClick={onGenerate}
        disabled={loading}
        className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-sky-500 via-sky-400 to-indigo-400 hover:from-sky-400 hover:to-indigo-300 text-slate-950 font-extrabold text-sm shadow-xl shadow-sky-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2.5 transition-all hover:scale-[1.01]"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Running LangGraph Pipeline (Stratified Retrieval &rarr; Reasoner &rarr; Synthesis)...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 fill-slate-950" />
            <span>Generate Full Study Pack (20 MCQs, 5 Q&As, Roadmap & Summaries)</span>
          </>
        )}
      </button>
    </div>
  );
};
