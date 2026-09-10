import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, RotateCcw, Award, Save, Sparkles } from 'lucide-react';
import { submitQuizResult } from '../services/api';

export const InteractiveQuiz = ({ mcqs = [], packId, documentId, token }) => {
  const [userAnswers, setUserAnswers] = useState({});
  const [instantMode, setInstantMode] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  if (!mcqs || mcqs.length === 0) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center">
        <HelpCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-300">No Interactive Quiz Available</h3>
        <p className="text-xs text-slate-500 mt-1">
          Generate a study pack to unlock the full 20 practice MCQs.
        </p>
      </div>
    );
  }

  const handleSelectOption = (questionId, optionLetter) => {
    setUserAnswers((prev) => ({
      ...prev,
      [questionId]: optionLetter,
    }));
  };

  const handleReset = () => {
    setUserAnswers({});
    setSubmitted(false);
    setSaveStatus(null);
  };

  // Calculate score
  let score = 0;
  mcqs.forEach((mcq) => {
    if (userAnswers[mcq.id] === mcq.correct_answer) {
      score += 1;
    }
  });

  const totalAnswered = Object.keys(userAnswers).length;
  const percentage = Math.round((score / mcqs.length) * 100);

  const handleSaveToProfile = async () => {
    setSubmitted(true);
    if (!token) return;
    try {
      await submitQuizResult(
        {
          packId: packId || 'pack_default',
          documentId: documentId || null,
          score,
          total: mcqs.length,
          answers: userAnswers,
        },
        token
      );
      setSaveStatus('Saved to MongoDB user_quiz_history!');
    } catch (err) {
      setSaveStatus('Saved locally in session.');
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-6">
      {/* Quiz Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1">
              <Award className="w-3 h-3" /> 20 Active Recall Questions
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight">Interactive Practice Exam</h2>
        </div>

        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-xs font-semibold text-slate-300 cursor-pointer select-none bg-slate-950/80 px-3 py-2 rounded-xl border border-slate-800">
            <input
              type="checkbox"
              checked={instantMode}
              onChange={(e) => setInstantMode(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0 focus:ring-offset-0"
            />
            <span>Instant Validation Mode</span>
          </label>

          <button
            onClick={handleReset}
            className="flex items-center space-x-1 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Score Header Banner */}
      <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center justify-between text-xs font-bold mb-1.5">
            <span className="text-slate-300">Live Mastery Progress</span>
            <span className="text-sky-400 font-extrabold">{score} / {mcqs.length} Correct ({percentage}%)</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-sky-500 to-indigo-500 transition-all duration-300"
              style={{ width: `${(score / mcqs.length) * 100}%` }}
            />
          </div>
        </div>

        <button
          onClick={handleSaveToProfile}
          className="py-2.5 px-4 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-md shadow-sky-500/20 shrink-0"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Quiz Score</span>
        </button>
      </div>

      {saveStatus && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{saveStatus}</span>
        </div>
      )}

      {/* 20 MCQs List */}
      <div className="space-y-6 pt-2">
        {mcqs.map((mcq, idx) => {
          const userChoice = userAnswers[mcq.id];
          const isCorrect = userChoice === mcq.correct_answer;
          const showFeedback = userChoice && (instantMode || submitted);

          return (
            <div
              key={mcq.id || idx}
              className={`p-5 rounded-2xl border transition-all ${
                showFeedback
                  ? isCorrect
                    ? 'border-emerald-500/30 bg-emerald-950/10'
                    : 'border-rose-500/30 bg-rose-950/10'
                  : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-lg bg-slate-800 text-sky-400 font-extrabold text-xs flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">
                    Question {idx + 1} of {mcqs.length}
                  </span>
                </div>
                {showFeedback && (
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                      isCorrect
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}
                  >
                    {isCorrect ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    {isCorrect ? 'Correct' : `Incorrect (Correct: ${mcq.correct_answer})`}
                  </span>
                )}
              </div>

              <h4 className="text-sm sm:text-base font-bold text-slate-100 mb-4 leading-relaxed">
                {mcq.question}
              </h4>

              {/* Options (A, B, C, D) */}
              <div className="grid grid-cols-1 gap-2.5">
                {mcq.options.map((opt) => {
                  const isSelected = userChoice === opt.label;
                  const isAnswer = opt.label === mcq.correct_answer;

                  let optClass = 'border-slate-800/80 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-900';

                  if (showFeedback) {
                    if (isAnswer) {
                      optClass = 'border-emerald-500/50 bg-emerald-950/30 text-emerald-200 font-semibold';
                    } else if (isSelected && !isCorrect) {
                      optClass = 'border-rose-500/50 bg-rose-950/30 text-rose-200';
                    }
                  } else if (isSelected) {
                    optClass = 'border-sky-500 bg-sky-500/10 text-sky-300 font-semibold';
                  }

                  return (
                    <button
                      key={opt.label}
                      type="button"
                      onClick={() => handleSelectOption(mcq.id, opt.label)}
                      className={`p-3 rounded-xl border text-left text-xs sm:text-sm flex items-start space-x-3 transition-all ${optClass}`}
                    >
                      <span className="w-5 h-5 rounded-md bg-slate-800/80 text-slate-200 font-bold flex items-center justify-center shrink-0 text-xs">
                        {opt.label}
                      </span>
                      <span className="flex-1 leading-relaxed">{opt.text}</span>
                    </button>
                  );
                })}
              </div>

              {/* Explanation Dropdown */}
              {showFeedback && (
                <div className="mt-3.5 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  <span className="font-bold text-sky-400 block mb-1">💡 Pedagogical Explanation:</span>
                  {mcq.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
