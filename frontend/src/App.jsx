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
import { ConnectorsView } from './components/ConnectorsView';
import { HistoryView } from './components/HistoryView';
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
  PlugZap,
  History,
  LayoutDashboard,
  Menu,
  X
} from 'lucide-react';

function AuthenticatedWorkspace({ backendHealth }) {
  const { getToken } = useAuth();
  const { user } = useUser();

  const [activeTab, setActiveTab] = useState('studio'); // 'studio' | 'connectors' | 'history'
  const [activeDoc, setActiveDoc] = useState(null);
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [customInstructions, setCustomInstructions] = useState('');
  const [studyPack, setStudyPack] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnectorsModalOpen, setIsConnectorsModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

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

  const navItems = [
    { id: 'studio', label: 'Study Studio', icon: LayoutDashboard, badge: null },
    { id: 'connectors', label: 'MCP Connectors', icon: PlugZap, badge: 'Live MCP' },
    { id: 'history', label: 'Saved Packs', icon: History, badge: null },
  ];

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      <Navbar
        backendHealth={backendHealth}
        onOpenConnectors={() => setActiveTab('connectors')}
      />

      {/* Quick Modal fallback if triggered from elsewhere */}
      <ConnectorsModal
        isOpen={isConnectorsModalOpen}
        onClose={() => setIsConnectorsModalOpen(false)}
        token={getToken}
      />

      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col md:flex-row gap-6">
        {/* ========================================================= */}
        {/* SIDE TABS / SIDEBAR NAVIGATION */}
        {/* ========================================================= */}
        <aside className="w-full md:w-64 shrink-0 space-y-4">
          {/* User Info Card in Sidebar */}
          <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 text-slate-950 font-black text-sm flex items-center justify-center shadow-md shadow-sky-500/20">
              {user?.firstName?.[0] || 'S'}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-slate-200 truncate">{user?.fullName || 'Active Scholar'}</p>
              <p className="text-[10px] text-slate-400 font-mono truncate">{user?.primaryEmailAddress?.emailAddress || 'student@studyguide.ai'}</p>
            </div>
          </div>

          {/* Side Navigation Tabs */}
          <nav className="p-2 rounded-2xl bg-slate-900/50 border border-slate-800/80 space-y-1">
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Workspace Navigation
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20 font-extrabold scale-[1.01]'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-slate-950' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                        isActive
                          ? 'bg-slate-950 text-sky-300'
                          : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* MCP Status Widget in Sidebar */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950/30 border border-slate-800/80 space-y-2.5 hidden md:block">
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold">
              <PlugZap className="w-3.5 h-3.5" />
              <span>MCP Protocol Active</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              External tools (NewsAPI, Wikipedia, ArXiv) are actively linked to enrich study packs.
            </p>
            <button
              onClick={() => setActiveTab('connectors')}
              className="w-full py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-bold transition-all text-center"
            >
              Configure Connectors &rarr;
            </button>
          </div>
        </aside>

        {/* ========================================================= */}
        {/* MAIN CONTENT AREA ACCORDING TO ACTIVE SIDE TAB */}
        {/* ========================================================= */}
        <main className="flex-1 min-w-0 space-y-6">
          {/* TAB 1: CONNECTORS SIDE TAB VIEW */}
          {activeTab === 'connectors' && (
            <ConnectorsView token={getToken} />
          )}

          {/* TAB 2: SAVED HISTORY SIDE TAB VIEW */}
          {activeTab === 'history' && (
            <HistoryView
              token={getToken}
              onSelectPack={(pack) => {
                setStudyPack(pack);
                setActiveTab('studio');
              }}
            />
          )}

          {/* TAB 3: STUDY STUDIO MAIN WORKSPACE */}
          {activeTab === 'studio' && (
            <div className="space-y-8 animate-fadeIn">
              {/* Workspace Title & Welcome */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-0.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Study Studio & Practice Exam</span>
                  </div>
                  <h1 className="text-2xl font-black text-slate-100 tracking-tight">
                    Whole-Document Study Pack Generator
                  </h1>
                </div>
              </div>

              {/* Step 1: Ingestion Zone */}
              <section>
                <div className="flex items-center space-x-2 mb-3">
                  <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 font-bold text-xs flex items-center justify-center">
                    1
                  </span>
                  <h2 className="text-base font-bold text-slate-200">Ingest Lecture Notes / PDF (up to 150 pages)</h2>
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
            </div>
          )}
        </main>
      </div>
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
