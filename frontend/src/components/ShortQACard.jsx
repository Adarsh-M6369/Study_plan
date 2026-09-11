import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp, CheckCircle, Sparkles } from 'lucide-react';

export const ShortQACard = ({ shortQas = [] }) => {
  const [openIds, setOpenIds] = useState({});

  if (!shortQas || shortQas.length === 0) {
    return null;
  }

  const toggleAccordion = (id) => {
    setOpenIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="bg-[#141b2d] border border-[#232f48] rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-4">
      <div className="flex items-center space-x-3 pb-4 border-b border-[#232f48]">
        <div className="w-9 h-9 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-100">Conceptual Short Q&As (5 Questions)</h2>
          <p className="text-xs text-slate-400">Test core mechanisms with comprehensive model answers</p>
        </div>
      </div>

      <div className="space-y-3">
        {shortQas.map((qa, idx) => {
          const isOpen = !!openIds[qa.id || idx];

          return (
            <div
              key={qa.id || idx}
              className="rounded-xl border border-[#232f48] bg-[#080b11]/60 overflow-hidden transition-all"
            >
              <button
                type="button"
                onClick={() => toggleAccordion(qa.id || idx)}
                className="w-full p-4 text-left flex items-center justify-between hover:bg-[#1d273e]/50 transition-colors"
              >
                <div className="flex items-start space-x-3 pr-4">
                  <span className="w-6 h-6 rounded-md bg-amber-400/10 text-amber-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 border border-amber-400/20">
                    Q{qa.id || idx + 1}
                  </span>
                  <h4 className="text-sm font-bold text-slate-200 leading-snug">{qa.question}</h4>
                </div>
                {isOpen ? (
                  <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                )}
              </button>

              {isOpen && (
                <div className="p-4 pt-0 border-t border-[#232f48] mt-2 space-y-3">
                  <div className="p-3.5 rounded-lg bg-[#141b2d] border border-[#232f48] text-xs text-slate-200 leading-relaxed">
                    <span className="font-bold text-emerald-400 block mb-1">Model Solution / Answer:</span>
                    {qa.model_answer}
                  </div>

                  {qa.key_points && qa.key_points.length > 0 && (
                    <div className="pl-1">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                        Key Evaluation Criteria:
                      </span>
                      <ul className="space-y-1">
                        {qa.key_points.map((pt, pIdx) => (
                          <li key={pIdx} className="text-xs text-slate-300 flex items-center space-x-2">
                            <CheckCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                            <span>{pt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

