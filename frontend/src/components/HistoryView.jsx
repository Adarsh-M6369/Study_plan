import React, { useState, useEffect } from 'react';
import { getStudyHistory } from '../services/api';
import { BookOpen, Calendar, Award, ArrowRight, RefreshCw, Layers, Sparkles } from 'lucide-react';

export const HistoryView = ({ token, onSelectPack }) => {
  const [packs, setPacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStudyHistory(token);
      setPacks(data.study_packs || []);
    } catch (err) {
      console.error('Failed to load study pack history:', err);
      setError('Failed to fetch study pack history.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#080b11] via-[#141b2d] to-[#080b11] border border-[#232f48] flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-1">
            <BookOpen className="w-4 h-4" />
            <span>MongoDB Multi-Tenant History</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight">
            Saved Study Guides & Packs
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Access and review previously synthesized study materials and practice exams.
          </p>
        </div>

        <button
          onClick={loadHistory}
          disabled={loading}
          className="p-3 rounded-xl bg-[#141b2d] hover:bg-[#1d273e] text-slate-300 border border-[#232f48] transition-all"
          title="Refresh History"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-400' : ''}`} />
        </button>
      </div>

      {/* List */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 text-amber-400 animate-spin" />
          <p className="text-sm font-medium">Fetching your study guides from MongoDB...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      ) : packs.length === 0 ? (
        <div className="py-16 text-center text-slate-400 bg-[#141b2d] rounded-2xl border border-[#232f48]">
          <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-300">No study packs generated yet.</p>
          <p className="text-xs text-slate-500 mt-1">Ingest lecture slides or paste text in the Study Studio tab to generate your first pack.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {packs.map((pack, idx) => (
            <div
              key={pack.id || idx}
              className="p-5 rounded-2xl bg-[#141b2d] border border-[#232f48] hover:border-amber-400/40 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-400/10 text-amber-300 border border-amber-400/20">
                    {pack.difficulty || 'Intermediate'}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {pack.mcqs?.length || 20} MCQs &bull; {pack.short_qas?.length || 5} Q&As
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-100">{pack.title || 'Study Guide'}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">
                  {pack.summary_notes?.slice(0, 140) || 'Comprehensive whole-document curriculum notes.'}...
                </p>
              </div>

              <button
                onClick={() => onSelectPack(pack)}
                className="w-full py-2 px-3 rounded-xl bg-[#080b11] hover:bg-amber-400 hover:text-slate-950 text-slate-200 border border-[#232f48] text-xs font-bold transition-all flex items-center justify-center space-x-2"
              >
                <span>Open in Study Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

