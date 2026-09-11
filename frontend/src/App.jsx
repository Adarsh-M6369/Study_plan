import React, { useState, useEffect } from 'react';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useAuth, useUser } from '@clerk/clerk-react';
import { Navbar } from './components/Navbar';
import { IngestionZone } from './components/IngestionZone';
import { DifficultySelector } from './components/DifficultySelector';
import { StudyPackDashboard } from './components/StudyPackDashboard';
import { InteractiveQuiz } from './components/InteractiveQuiz';
import { ShortQACard } from './components/ShortQACard';
import { ExportBar } from './components/ExportBar';
import { ConnectorsModal } from './components/ConnectorsModal';
import { checkHealth, generateStudyPack } from './services/api';
import {
  GraduationCap,
  Sparkles,
  BookOpen,
  BrainCircuit,
  FileCheck2,
  ShieldCheck,
  Zap,
  ArrowRight,
  Database,
  Layers,
  PlugZap
} from 'lucide-react';

function AuthenticatedWorkspace({ backendHealth }) {
  const { getToken } = useAuth();
  const { user } = useUser();

  const [activeDoc, setActiveDoc] = useState(null);
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [customInstructions, setCustomInstructions] = useState('');
  const [studyPack, setStudyPack] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnectorsOpen, setIsConnectorsOpen] = useState(false);

  const handleIngestionSuccess = (docInfo) => {
    setActiveDoc(docInfo);
    if (!topic && docInfo.title) {
      setTopic(docInfo.title);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const result = await generateStudyPack(
        {
          topic: topic || activeDoc?.title || 'Comprehensive Lesson Notes',
          difficulty,
          customInstructions,
          documentId: activeDoc?.documentId || null,
        },
        token
      );
      setStudyPack(result);
    } catch (err) {
      console.error('Generation error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to generate study pack.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      <Navbar backendHealth={backendHealth} onOpenConnectors={() => setIsConnectorsOpen(true)} />

      {/* MCP Connectors Modal */}
      <ConnectorsModal
        isOpen={isConnectorsOpen}
        onClose={() => setIsConnectorsOpen(false)}
        token={getToken}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Workspace Title & Welcome */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Sparkles className="w-4 h-4" />
              <span>Multi-Tenant AI Workspace</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
              Study Pack & Practice Exam Studio
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Ingest lecture slides (up to 150 pages), synthesize whole-document study packs, and practice 20 MCQs.
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-900/80 px-4 py-2.5 rounded-xl border border-slate-800 shrink-0">
            <div className="w-8 h-8 rounded-full bg-sky-500/20 text-sky-400 font-bold text-xs flex items-center justify-center border border-sky-500/30">
              {user?.firstName?.[0] || 'S'}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-200">{user?.fullName || 'Active Scholar'}</p>
              <p className="text-[10px] text-slate-400 font-mono">{user?.primaryEmailAddress?.emailAddress || 'student@studyguide.ai'}</p>
            </div>
          </div>
        </div>

        {/* Step 1: Ingestion Zone */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 font-bold text-xs flex items-center justify-center">
              1
            </span>
            <h2 className="text-base font-bold text-slate-200">Ingest Lecture Notes / PDF</h2>
          </div>
          <IngestionZone
            token={getToken}
            onIngestionSuccess={handleIngestionSuccess}
            activeDoc={activeDoc}
          />
        </section>

        {/* Step 2: Generation Parameters */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 font-bold text-xs flex items-center justify-center">
              2
            </span>
            <h2 className="text-base font-bold text-slate-200">Configure & Synthesize Full Curriculum</h2>
          </div>
          <DifficultySelector
            difficulty={difficulty}
            setDifficulty={setDifficulty}
            topic={topic}
            setTopic={setTopic}
            customInstructions={customInstructions}
            setCustomInstructions={setCustomInstructions}
            onGenerate={handleGenerate}
            loading={loading}
            hasActiveDoc={!!activeDoc}
          />
        </section>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm font-medium">
            ❌ {error}
          </div>
        )}

        {/* Generated Study Pack Outputs */}
        {studyPack && (
          <div className="space-y-8 animate-fadeIn">
            {/* Download Bar */}
            <ExportBar studyPack={studyPack} />

            {/* Step 3: Summaries, Glossary & Roadmap */}
            <section>
              <div className="flex items-center space-x-2 mb-3">
                <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <h2 className="text-base font-bold text-slate-200">Curriculum Study Pack & Roadmap</h2>
              </div>
              <StudyPackDashboard studyPack={studyPack} />
            </section>

            {/* Step 4: Conceptual 5 Short Q&As */}
            <section>
              <div className="flex items-center space-x-2 mb-3">
                <span className="w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <h2 className="text-base font-bold text-slate-200">Conceptual Short Questions & Solutions</h2>
              </div>
              <ShortQACard shortQas={studyPack.short_qas} />
            </section>

            {/* Step 5: 20 Practice MCQs */}
            <section>
              <div className="flex items-center space-x-2 mb-3">
                <span className="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-400 font-bold text-xs flex items-center justify-center">
                  5
                </span>
                <h2 className="text-base font-bold text-slate-200">Interactive Practice Exam (20 MCQs)</h2>
              </div>
              <InteractiveQuiz
                mcqs={studyPack.mcqs}
                packId={studyPack.id}
                documentId={activeDoc?.documentId}
                token={getToken}
              />
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

function LandingGate({ backendHealth }) {
  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-sky-500/30 selection:text-sky-200">
      <Navbar backendHealth={backendHealth} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-16 flex flex-col justify-center items-center text-center">
        {/* Badge */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Gen RAG Study Guide Platform</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl font-black tracking-tight max-w-4xl leading-[1.1] mb-6">
          Transform 150-Page Lectures into{' '}
          <span className="bg-gradient-to-r from-sky-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
            Exam-Ready Study Packs
          </span>
        </h1>

        <p className="text-slate-400 text-base sm:text-lg max-w-2xl leading-relaxed mb-8">
          Upload multi-chapter lecture decks or syllabus notes. Our whole-document LangGraph engine
          synthesizes 20 balanced MCQs, 5 Q&As, roadmaps, and Anki flashcards with multi-tenant MongoDB isolation.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <SignUpButton mode="modal">
            <button className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-sky-500 to-sky-400 hover:from-sky-400 hover:to-sky-300 text-slate-950 font-extrabold text-base shadow-xl shadow-sky-500/25 flex items-center justify-center space-x-2 transition-all hover:scale-[1.02]">
              <span>Sign Up with Google, GitHub or Facebook</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </SignUpButton>

          <SignInButton mode="modal">
            <button className="w-full sm:w-auto px-8 py-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-bold text-base transition-all">
              Sign In to Existing Workspace
            </button>
          </SignInButton>
        </div>

        {/* 3 Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100 mb-1.5">Whole-Document Stratified RAG</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Equidistant document segmentation ensures questions span from Chapter 1 to the final topic rather than clustering on one page.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100 mb-1.5">Multi-Tenant MongoDB Isolation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Strict Clerk JWT user isolation for uploaded documents, generated study packs, and student quiz history.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100 mb-1.5">Multi-Format Exports</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Instantly export clean ReportLab PDF study guides and 2-column CSV flashcard decks formatted for Anki and Quizlet.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      const data = await checkHealth();
      setBackendHealth(data);
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <SignedIn>
        <AuthenticatedWorkspace backendHealth={backendHealth} />
      </SignedIn>
      <SignedOut>
        <LandingGate backendHealth={backendHealth} />
      </SignedOut>
    </>
  );
}
