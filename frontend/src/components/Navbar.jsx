import React from 'react';
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/clerk-react';
import { GraduationCap, Activity, ShieldCheck, PlugZap } from 'lucide-react';

export const Navbar = ({ backendHealth, onOpenConnectors }) => {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-[#0b0f19]/80 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <GraduationCap className="w-6 h-6 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <span className="font-extrabold text-lg sm:text-xl tracking-tight bg-gradient-to-r from-sky-400 via-sky-300 to-indigo-300 bg-clip-text text-transparent">
              StudyGuide AI
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
              v1.0 &bull; LangGraph RAG
            </span>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* MCP Connectors Button */}
          <button
            onClick={onOpenConnectors}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-sky-400 border border-sky-500/30 hover:border-sky-500/60 shadow-sm transition-all hover:scale-[1.02]"
            title="Manage Model Context Protocol (MCP) Connectors"
          >
            <PlugZap className="w-4 h-4 text-sky-400 animate-pulse" />
            <span className="font-semibold text-slate-200">Connectors</span>
          </button>

          {/* Backend Health Badge */}
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-900 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full animate-pulse ${
                backendHealth?.status === 'ok' || backendHealth?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span className="text-slate-400">
              {backendHealth?.status === 'ok' || backendHealth?.status === 'healthy' ? 'FastAPI 8000' : 'Connecting Backend...'}
            </span>
          </div>

          {/* Clerk Auth Section */}
          <SignedIn>
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
              <UserButton
                showName={true}
                appearance={{
                  elements: {
                    userButtonBox: "flex-row-reverse text-slate-200 hover:text-sky-300 transition-colors",
                    userButtonOuterIdentifier: "text-sm font-semibold text-slate-200",
                    avatarBox: "w-8 h-8 rounded-full border border-sky-500/30",
                  },
                }}
              />
            </div>
          </SignedIn>

          <SignedOut>
            <div className="flex items-center space-x-2">
              <SignInButton mode="modal">
                <button className="px-4 py-2 text-sm font-semibold text-slate-200 hover:text-sky-300 transition-colors">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="px-4 py-2 text-sm font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold shadow-md shadow-sky-500/20 transition-all hover:scale-[1.02]">
                  Get Started
                </button>
              </SignUpButton>
            </div>
          </SignedOut>
        </div>
      </div>
    </header>
  );
};
