import React, { useState } from 'react';
import { BookOpen, Key, Compass, CheckCircle, Clock, ChevronRight } from 'lucide-react';

export const StudyPackDashboard = ({ studyPack }) => {
  const [activeTab, setActiveTab] = useState('summary'); // 'summary', 'glossary', 'roadmap'

  if (!studyPack) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center">
        <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-300">No Study Pack Generated Yet</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Upload your lecture notes above and click Generate to produce a full curriculum guide.
        </p>
      </div>
    );
  }

  const { title, difficulty, summary_notes, glossary = [], roadmap = [] } = studyPack;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
              {difficulty || 'Intermediate'} Tier
            </span>
            <span className="text-xs text-slate-500">&bull; Verified Schema Output</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight">{title}</h2>
        </div>

        {/* Tab Controls */}
        <div className="flex p-1 bg-slate-950/80 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('summary')}
            className={`flex items-center space-x-1.5 py-2 px-3.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'summary'
                ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Summary Notes</span>
          </button>
          <button
            onClick={() => setActiveTab('glossary')}
            className={`flex items-center space-x-1.5 py-2 px-3.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'glossary'
                ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>Glossary ({glossary.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('roadmap')}
            className={`flex items-center space-x-1.5 py-2 px-3.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'roadmap'
                ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Roadmap ({roadmap.length})</span>
          </button>
        </div>
      </div>

      {/* Summary View */}
      {activeTab === 'summary' && (
        <div className="prose prose-invert max-w-none prose-headings:text-sky-300 prose-strong:text-slate-100 prose-p:text-slate-300 prose-p:leading-relaxed prose-li:text-slate-300 text-sm">
          <div className="bg-slate-950/50 p-6 rounded-xl border border-slate-800/80 whitespace-pre-line font-sans leading-relaxed">
            {summary_notes || 'Summary notes generated for this curriculum.'}
          </div>
        </div>
      )}

      {/* Glossary View */}
      {activeTab === 'glossary' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {glossary.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center space-x-2 mb-1.5">
                    <span className="w-5 h-5 rounded-md bg-sky-500/10 text-sky-400 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <h4 className="font-bold text-sm text-sky-300">{item.term}</h4>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed pl-7">{item.definition}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roadmap View */}
      {activeTab === 'roadmap' && (
        <div className="space-y-3">
          {roadmap.map((step, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-sky-500/30 transition-all flex items-start space-x-4 group"
            >
              <div className="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 font-extrabold text-sm flex items-center justify-center shrink-0 group-hover:bg-sky-500 group-hover:text-slate-950 transition-all">
                {step.step_number || idx + 1}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                  <h4 className="font-bold text-sm text-slate-100">{step.topic}</h4>
                  <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded-md border border-slate-800">
                    <Clock className="w-3 h-3 text-sky-400" />
                    {step.estimated_minutes} mins
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{step.action_item}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
