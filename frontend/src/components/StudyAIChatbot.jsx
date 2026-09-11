import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  Sparkles,
  X,
  Send,
  Loader2,
  BookOpen,
  GraduationCap,
  PlugZap,
  RotateCcw,
  ExternalLink,
  ShieldCheck,
  Globe,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
  Lightbulb,
  HelpCircle,
  Paperclip
} from 'lucide-react';
import { sendStudyChatMessage } from '../services/api';

const QUICK_STARTERS = [
  "💡 Explain this concept simply with analogies",
  "🎯 Quiz me with 3 conceptual study questions",
  "🔬 Search ArXiv research papers on this topic",
  "📚 What is the exact academic definition & context?"
];

export const StudyAIChatbot = ({ token, activeDoc }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "👋 **Hello Scholar!** I am your **AI Academic Study Tutor & Curriculum Assistant**.\n\nAsk me anything about your lecture notes, academic concepts, formulas, or exam review. I actively query connected **Model Context Protocol (MCP)** tools (Wikipedia, ArXiv, NewsAPI) and your uploaded materials to provide verified educational answers.",
      sources: [
        { type: "Model Context Protocol", title: "Live Connectors (Wikipedia, ArXiv, NewsAPI)" },
        { type: "Course Material", title: activeDoc?.title ? `Active Doc: ${activeDoc.title}` : "Vector RAG Store" }
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setLoading(true);

    try {
      // Build conversation history excluding sources
      const historyPayload = messages.map((m) => ({
        role: m.role,
        content: m.content
      }));

      const res = await sendStudyChatMessage(
        {
          message: text,
          history: historyPayload,
          documentId: activeDoc?.documentId || null
        },
        token
      );

      const botMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.reply,
        sources: res.sources || [],
        isStudyQuestion: res.is_study_question,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Study chat error:', err);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ **Communication Error**: ${err.response?.data?.detail || err.message || 'Failed to connect to AI study backend.'}`,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Clear conversation history?')) {
      setMessages([
        {
          id: 'welcome-reset',
          role: 'assistant',
          content: "Conversation cleared. Ready for your next study or syllabus question!",
          sources: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
  };

  const toggleSourceAccordion = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  return (
    <>
      {/* ========================================================= */}
      {/* 1. FLOATING ACTION BUTTON (RIGHT SIDE OF SCREEN) */}
      {/* ========================================================= */}
      <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-3">
        {!isOpen && (
          <div className="hidden md:flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#141b2d] border border-amber-400/40 text-amber-300 text-xs font-bold shadow-xl animate-bounce">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Ask AI Study Tutor</span>
          </div>
        )}

        <button
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle AI Study Chatbot"
          className="relative group p-4 rounded-2xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black shadow-2xl shadow-amber-500/40 transition-all hover:scale-105 active:scale-95 flex items-center justify-center border border-amber-300"
          title="Open AI Study Assistant (MCP Connected)"
        >
          {isOpen ? (
            <X className="w-6 h-6 stroke-[2.5]" />
          ) : (
            <>
              <GraduationCap className="w-6 h-6 stroke-[2.5]" />
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-[#080b11] animate-pulse" />
            </>
          )}
        </button>
      </div>

      {/* ========================================================= */}
      {/* 2. RIGHT-SIDE AI CHATBOT DRAWER / PANEL */}
      {/* ========================================================= */}
      {isOpen && (
        <div
          className={`fixed z-50 transition-all duration-300 shadow-2xl flex flex-col bg-[#141b2d] border border-[#232f48] rounded-2xl overflow-hidden ${
            isExpanded
              ? 'inset-4 md:inset-x-auto md:right-6 md:top-6 md:bottom-24 md:w-[650px]'
              : 'bottom-24 right-4 sm:right-6 w-[calc(100vw-2rem)] sm:w-[420px] h-[600px] max-h-[82vh]'
          }`}
        >
          {/* Top Header */}
          <div className="p-4 bg-[#080b11] border-b border-[#232f48] flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center shadow-md shadow-amber-500/20 text-slate-950 font-black">
                <GraduationCap className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-extrabold text-sm sm:text-base text-slate-100">AI Study Tutor</h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>MCP Active</span>
                  </span>
                </div>
                <p className="text-[11px] text-amber-300/80 font-medium">
                  {activeDoc?.title ? `Doc: ${activeDoc.title.slice(0, 24)}...` : 'Study Guide & Curriculum Mode'}
                </p>
              </div>
            </div>

            {/* Header Action Icons */}
            <div className="flex items-center space-x-1 text-slate-400">
              <button
                onClick={handleClearHistory}
                className="p-2 rounded-lg hover:bg-[#141b2d] hover:text-slate-200 transition-colors"
                title="Reset Chat"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="hidden md:block p-2 rounded-lg hover:bg-[#141b2d] hover:text-slate-200 transition-colors"
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-lg hover:bg-[#141b2d] hover:text-slate-200 transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Academic Guardrail Notice Banner */}
          <div className="px-4 py-1.5 bg-amber-400/10 border-b border-amber-400/20 text-[11px] font-bold text-amber-300 flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              <span>Academic Guardrails Enforced (Study Inquiries Only)</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Wikipedia &bull; ArXiv &bull; NewsAPI</span>
          </div>

          {/* Message List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#080b11]/70 scroll-smooth">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              const hasSources = msg.sources && msg.sources.length > 0;
              const isSourcesExpanded = !!expandedSources[msg.id];

              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
                >
                  <div className="flex items-center space-x-2 text-[10px] text-slate-400 px-1 font-semibold">
                    <span>{isUser ? 'You' : 'AI Study Tutor'}</span>
                    <span>&bull;</span>
                    <span>{msg.timestamp}</span>
                  </div>

                  <div
                    className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed max-w-[90%] transition-all shadow-md ${
                      isUser
                        ? 'bg-amber-400 text-slate-950 font-semibold rounded-br-none border border-amber-300 shadow-amber-500/10'
                        : 'bg-[#141b2d] text-slate-100 rounded-bl-none border border-[#232f48]'
                    }`}
                  >
                    <div className="whitespace-pre-line font-sans prose prose-invert max-w-none text-inherit prose-headings:text-amber-300 prose-strong:text-slate-100 prose-code:bg-[#080b11] prose-code:text-amber-300 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded">
                      {msg.content}
                    </div>

                    {/* Expandable MCP Sources Accordion */}
                    {hasSources && !isUser && (
                      <div className="mt-3 pt-2.5 border-t border-[#232f48] text-xs">
                        <button
                          onClick={() => toggleSourceAccordion(msg.id)}
                          className="flex items-center space-x-1.5 text-[11px] font-bold text-amber-300 hover:text-amber-200 transition-colors"
                        >
                          <PlugZap className="w-3.5 h-3.5 text-amber-400" />
                          <span>{msg.sources.length} Connected Knowledge Sources</span>
                          {isSourcesExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>

                        {isSourcesExpanded && (
                          <div className="mt-2 space-y-1.5">
                            {msg.sources.map((s, sIdx) => (
                              <div
                                key={sIdx}
                                className="p-2 rounded-lg bg-[#080b11] border border-[#232f48] text-[11px] space-y-0.5"
                              >
                                <div className="flex items-center justify-between font-bold text-amber-400">
                                  <span>{s.type}</span>
                                  {s.url && (
                                    <a
                                      href={s.url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-slate-400 hover:text-amber-300 flex items-center space-x-1"
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                                <p className="font-semibold text-slate-200">{s.title}</p>
                                {s.snippet && (
                                  <p className="text-[10px] text-slate-400 leading-snug line-clamp-2">
                                    {s.snippet}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Typing Loader Indicator */}
            {loading && (
              <div className="flex items-center space-x-2.5 p-3 rounded-2xl bg-[#141b2d] border border-[#232f48] text-xs text-amber-300 w-fit">
                <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                <span className="font-bold">Consulting MCP Connectors & Vector Store...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Suggestions */}
          {messages.length <= 3 && (
            <div className="p-2.5 bg-[#141b2d] border-t border-[#232f48] flex items-center space-x-2 overflow-x-auto no-scrollbar">
              {QUICK_STARTERS.map((starter, qIdx) => (
                <button
                  key={qIdx}
                  onClick={() => handleSendMessage(starter)}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-xl bg-[#080b11] hover:bg-[#1d273e] border border-[#232f48] hover:border-amber-400/40 text-[11px] font-semibold text-slate-300 whitespace-nowrap transition-all"
                >
                  {starter}
                </button>
              ))}
            </div>
          )}

          {/* Chat Input Bar */}
          <div className="p-3 bg-[#141b2d] border-t border-[#232f48]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center space-x-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask any study, exam, formula, or syllabus question..."
                className="flex-1 px-4 py-2.5 rounded-xl bg-[#080b11] border border-[#232f48] text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="p-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black shadow-md shadow-amber-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
                title="Send Question"
              >
                <Send className="w-4 h-4 stroke-[2.5]" />
              </button>
            </form>
            <p className="text-[10px] text-slate-500 text-center mt-1.5 font-medium">
              Guarded for academic topics &bull; Real-time Wikipedia, ArXiv & NewsAPI MCP integration
            </p>
          </div>
        </div>
      )}
    </>
  );
};
