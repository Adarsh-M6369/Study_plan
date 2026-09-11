import React, { useState, useEffect } from 'react';
import {
  Plug,
  PlugZap,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sliders,
  Terminal,
  Globe,
  Newspaper,
  BookMarked,
  GraduationCap,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  X,
  Play,
  Activity,
  Layers
} from 'lucide-react';
import {
  getMCPConnectors,
  connectMCPConnector,
  disconnectMCPConnector,
  testMCPConnector,
  executeMCPTool
} from '../services/api';

const ICON_MAP = {
  Newspaper: Newspaper,
  BookMarked: BookMarked,
  GraduationCap: GraduationCap,
  Globe: Globe,
  Terminal: Terminal,
};

export const ConnectorsModal = ({ isOpen, onClose, token }) => {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [configForms, setConfigForms] = useState({});
  const [expandedConnector, setExpandedConnector] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [executingTool, setExecutingTool] = useState(null);
  const [toolResults, setToolResults] = useState({});

  useEffect(() => {
    if (isOpen) {
      loadConnectors();
    }
  }, [isOpen]);

  const loadConnectors = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMCPConnectors(token);
      setConnectors(data.connectors || []);
      // Initialize config forms
      const initialConfigs = {};
      (data.connectors || []).forEach((c) => {
        initialConfigs[c.id] = { ...(c.active_config || {}) };
        // set defaults if not set
        (c.config_fields || []).forEach((f) => {
          if (initialConfigs[c.id][f.key] === undefined && f.default !== undefined) {
            initialConfigs[c.id][f.key] = f.default;
          }
        });
      });
      setConfigForms(initialConfigs);
    } catch (err) {
      console.error('Failed to load MCP connectors:', err);
      setError('Failed to fetch MCP connectors from server.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (connectorId, key, value) => {
    setConfigForms((prev) => ({
      ...prev,
      [connectorId]: {
        ...(prev[connectorId] || {}),
        [key]: value,
      },
    }));
  };

  const handleConnect = async (connectorId) => {
    try {
      const config = configForms[connectorId] || {};
      await connectMCPConnector(connectorId, config, token);
      setConnectors((prev) =>
        prev.map((c) => (c.id === connectorId ? { ...c, connected: true, status: 'connected' } : c))
      );
    } catch (err) {
      console.error('Connect error:', err);
      alert(`Failed to connect: ${err.message}`);
    }
  };

  const handleDisconnect = async (connectorId) => {
    try {
      await disconnectMCPConnector(connectorId, token);
      setConnectors((prev) =>
        prev.map((c) => (c.id === connectorId ? { ...c, connected: false, status: 'disconnected' } : c))
      );
    } catch (err) {
      console.error('Disconnect error:', err);
      alert(`Failed to disconnect: ${err.message}`);
    }
  };

  const handleTest = async (connectorId) => {
    setTestingId(connectorId);
    setTestResults((prev) => ({ ...prev, [connectorId]: null }));
    try {
      const config = configForms[connectorId] || {};
      const res = await testMCPConnector(connectorId, config, token);
      setTestResults((prev) => ({ ...prev, [connectorId]: res }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: { status: 'error', message: err.message },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleRunSampleTool = async (connectorId, toolName) => {
    setExecutingTool(`${connectorId}_${toolName}`);
    try {
      const res = await executeMCPTool(connectorId, toolName, { query: 'Quantum Computing' }, token);
      setToolResults((prev) => ({
        ...prev,
        [connectorId]: res.tool_result,
      }));
    } catch (err) {
      setToolResults((prev) => ({
        ...prev,
        [connectorId]: { status: 'error', error: err.message },
      }));
    } finally {
      setExecutingTool(null);
    }
  };

  if (!isOpen) return null;

  const categories = ['All', 'News & Current Affairs', 'Reference & Encyclopedia', 'Academic Research', 'Web Knowledge', 'Custom Protocol'];
  const filteredConnectors = selectedCategory === 'All'
    ? connectors
    : connectors.filter((c) => c.category === selectedCategory);

  const connectedCount = connectors.filter((c) => c.connected).length;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-fadeIn">
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <PlugZap className="w-5 h-5 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-slate-100">Model Context Protocol (MCP) Connectors</h2>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  <span>{connectedCount} Connected</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Integrate real-time external knowledge, encyclopedias, and custom stdio MCP tools into your study generation workflow.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Category Filters */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/30 flex items-center space-x-2 overflow-x-auto no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-sky-500 text-slate-950 font-bold shadow-md shadow-sky-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Connectors Grid Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-7 h-7 text-sky-400 animate-spin" />
              <p className="text-sm font-medium">Loading MCP Connectors & Handlers...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
              {error}
            </div>
          ) : filteredConnectors.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm">No connectors found in this category.</p>
            </div>
          ) : (
            filteredConnectors.map((connector) => {
              const IconComponent = ICON_MAP[connector.icon] || Plug;
              const isConnected = connector.connected;
              const isExpanded = expandedConnector === connector.id;
              const testRes = testResults[connector.id];
              const toolRes = toolResults[connector.id];

              return (
                <div
                  key={connector.id}
                  className={`rounded-xl border transition-all duration-200 ${
                    isConnected
                      ? 'bg-slate-900/90 border-sky-500/40 shadow-lg shadow-sky-950/30'
                      : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    {/* Left Icon & Info */}
                    <div className="flex items-start space-x-4">
                      <div
                        className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                          isConnected
                            ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-inner'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        <IconComponent className="w-6 h-6 stroke-[2]" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2.5 flex-wrap">
                          <h3 className="font-bold text-slate-100 text-base">{connector.name}</h3>
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                            {connector.category}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1 ${
                              isConnected
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                              }`}
                            />
                            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
                          {connector.description}
                        </p>

                        {/* Tools list badges */}
                        <div className="flex items-center space-x-2 pt-1 flex-wrap gap-y-1">
                          <span className="text-[11px] font-semibold text-slate-400">MCP Tools:</span>
                          {(connector.tools || []).map((t) => (
                            <span
                              key={t.name}
                              className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                            >
                              {t.name}()
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2.5 self-end sm:self-center shrink-0">
                      <button
                        onClick={() => handleTest(connector.id)}
                        disabled={testingId === connector.id}
                        className="px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center space-x-1.5"
                      >
                        <Activity className={`w-3.5 h-3.5 text-sky-400 ${testingId === connector.id ? 'animate-spin' : ''}`} />
                        <span>{testingId === connector.id ? 'Testing...' : 'Test Connection'}</span>
                      </button>

                      {isConnected ? (
                        <button
                          onClick={() => handleDisconnect(connector.id)}
                          className="px-4 py-2 rounded-lg text-xs font-bold bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={() => handleConnect(connector.id)}
                          className="px-4 py-2 rounded-lg text-xs font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 shadow-md shadow-sky-500/20 transition-all hover:scale-[1.02]"
                        >
                          Connect
                        </button>
                      )}

                      <button
                        onClick={() => setExpandedConnector(isExpanded ? null : connector.id)}
                        className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                        title="Configure Settings"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Test Results Output */}
                  {testRes && (
                    <div className="px-5 pb-3">
                      <div
                        className={`p-3 rounded-lg text-xs flex items-center justify-between ${
                          testRes.status === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          {testRes.status === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                          )}
                          <span>{testRes.message}</span>
                        </div>
                        {testRes.latency_ms && (
                          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-900/60 border border-emerald-500/30">
                            {testRes.latency_ms} ms
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Expandable Configuration & Tool Runner */}
                  {isExpanded && (
                    <div className="border-t border-slate-800/80 p-5 bg-slate-950/40 space-y-4">
                      <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                        <Sliders className="w-3.5 h-3.5 text-sky-400" />
                        <span>Connector Settings & Parameters</span>
                      </div>

                      {/* Config Form Fields */}
                      {(connector.config_fields || []).length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {connector.config_fields.map((field) => (
                            <div key={field.key} className="space-y-1">
                              <label className="text-xs font-semibold text-slate-300">{field.label}</label>
                              {field.type === 'select' ? (
                                <select
                                  value={configForms[connector.id]?.[field.key] || field.default || ''}
                                  onChange={(e) => handleConfigChange(connector.id, field.key, e.target.value)}
                                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                                >
                                  {field.options.map((opt) => (
                                    <option key={opt} value={opt}>
                                      {opt}
                                    </option>
                                  ))}
                                </select>
                              ) : (
                                <input
                                  type={field.type === 'password' ? 'password' : 'text'}
                                  value={configForms[connector.id]?.[field.key] || ''}
                                  onChange={(e) => handleConfigChange(connector.id, field.key, e.target.value)}
                                  placeholder={field.placeholder}
                                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                                />
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-400">No additional configuration required for this connector.</p>
                      )}

                      {/* Interactive Tool Playground */}
                      <div className="pt-2 border-t border-slate-800/50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold text-slate-300">Live Tool Playground</span>
                          <span className="text-[10px] text-slate-400">Click to execute a live sample query</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {(connector.tools || []).map((t) => (
                            <button
                              key={t.name}
                              onClick={() => handleRunSampleTool(connector.id, t.name)}
                              disabled={executingTool === `${connector.id}_${t.name}`}
                              className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-[11px] font-mono text-indigo-300 border border-indigo-500/20 hover:border-indigo-500/40 transition-all flex items-center space-x-1.5"
                            >
                              <Play className="w-3 h-3 text-indigo-400" />
                              <span>{t.name}()</span>
                            </button>
                          ))}
                        </div>

                        {/* Tool Result Preview */}
                        {toolRes && (
                          <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-slate-800 max-h-48 overflow-y-auto">
                            <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
                              {JSON.stringify(toolRes, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/70 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            <span>Active connectors are automatically queried during study pack synthesis.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
