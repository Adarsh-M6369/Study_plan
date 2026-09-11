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
  Play,
  Activity,
  Layers,
  Search,
  Check
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

export const ConnectorsView = ({ token }) => {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [configForms, setConfigForms] = useState({});
  const [expandedConnector, setExpandedConnector] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [executingTool, setExecutingTool] = useState(null);
  const [toolResults, setToolResults] = useState({});
  const [toolInputs, setToolInputs] = useState({});

  useEffect(() => {
    loadConnectors();
  }, []);

  const loadConnectors = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMCPConnectors(token);
      setConnectors(data.connectors || []);
      const initialConfigs = {};
      (data.connectors || []).forEach((c) => {
        initialConfigs[c.id] = { ...(c.active_config || {}) };
        (c.config_fields || []).forEach((f) => {
          if (initialConfigs[c.id][f.key] === undefined && f.default !== undefined) {
            initialConfigs[c.id][f.key] = f.default;
          }
        });
      });
      setConfigForms(initialConfigs);
    } catch (err) {
      console.error('Failed to load MCP connectors:', err);
      setError('Failed to fetch MCP connectors from backend.');
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

  const handleRunTool = async (connectorId, toolName) => {
    setExecutingTool(`${connectorId}_${toolName}`);
    const query = toolInputs[`${connectorId}_${toolName}`] || 'Space Exploration';
    try {
      const res = await executeMCPTool(connectorId, toolName, { query }, token);
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

  const categories = ['All', 'News & Current Affairs', 'Reference & Encyclopedia', 'Academic Research', 'Web Knowledge', 'Custom Protocol'];

  const filteredConnectors = connectors.filter((c) => {
    const matchesCategory = selectedCategory === 'All' || c.category === selectedCategory;
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const connectedCount = connectors.filter((c) => c.connected).length;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#080b11] via-[#141b2d] to-[#080b11] border border-[#232f48] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
            <PlugZap className="w-4 h-4" />
            <span>Model Context Protocol (MCP) Hub</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight">
            Knowledge Connectors & External Tools
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl">
            Configure live connectors to ingest current science news, Wikipedia encyclopedias, and ArXiv research papers into your generated study guides.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <div className="px-4 py-2.5 rounded-xl bg-[#080b11] border border-[#232f48] text-right">
            <p className="text-[10px] uppercase font-bold text-slate-400">Active Connectors</p>
            <p className="text-lg font-black text-emerald-400 flex items-center justify-end space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{connectedCount} / {connectors.length}</span>
            </p>
          </div>

          <button
            onClick={loadConnectors}
            disabled={loading}
            className="p-3 rounded-xl bg-[#141b2d] hover:bg-[#1d273e] text-slate-300 border border-[#232f48] transition-all"
            title="Refresh Connectors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        {/* Category Tabs */}
        <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-[#141b2d] border border-[#232f48] overflow-x-auto w-full sm:w-auto no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-amber-400 text-slate-950 font-black shadow-md shadow-amber-500/20'
                  : 'text-slate-400 hover:text-amber-300 hover:bg-[#1d273e]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search connectors..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#080b11] border border-[#232f48] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
          />
        </div>
      </div>

      {/* Connectors List */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 text-amber-400 animate-spin" />
          <p className="text-sm font-medium">Scanning MCP Subsystem & Connectors...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      ) : filteredConnectors.length === 0 ? (
        <div className="py-16 text-center text-slate-400 bg-[#141b2d] rounded-2xl border border-[#232f48]">
          <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm">No connectors match your current filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredConnectors.map((connector) => {
            const IconComponent = ICON_MAP[connector.icon] || Plug;
            const isConnected = connector.connected;
            const isExpanded = expandedConnector === connector.id;
            const testRes = testResults[connector.id];
            const toolRes = toolResults[connector.id];

            return (
              <div
                key={connector.id}
                className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                  isConnected
                    ? 'bg-[#141b2d] border-amber-400/40 shadow-lg shadow-amber-950/20'
                    : 'bg-[#141b2d] border-[#232f48] hover:border-slate-700'
                }`}
              >
                {/* Connector Top Info */}
                <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start space-x-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                        isConnected
                          ? 'bg-amber-400/10 text-amber-400 border border-amber-400/30 shadow-inner'
                          : 'bg-[#080b11] text-slate-400 border border-[#232f48]'
                      }`}
                    >
                      <IconComponent className="w-6 h-6 stroke-[2]" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2.5 flex-wrap">
                        <h3 className="font-bold text-slate-100 text-base">{connector.name}</h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#080b11] text-slate-300 border border-[#232f48]">
                          {connector.category}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1 ${
                            isConnected
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-[#080b11] text-slate-400 border border-[#232f48]'
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

                      {/* Tool pills */}
                      <div className="flex items-center space-x-2 pt-1 flex-wrap gap-y-1">
                        <span className="text-[11px] font-semibold text-slate-400">Available MCP Tools:</span>
                        {(connector.tools || []).map((t) => (
                          <span
                            key={t.name}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-400/10 text-amber-300 border border-amber-400/20"
                          >
                            {t.name}()
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2.5 self-end sm:self-center shrink-0">
                    <button
                      onClick={() => handleTest(connector.id)}
                      disabled={testingId === connector.id}
                      className="px-3 py-2 rounded-xl text-xs font-semibold bg-[#080b11] hover:bg-[#1d273e] text-slate-200 border border-[#232f48] transition-all flex items-center space-x-1.5"
                    >
                      <Activity className={`w-3.5 h-3.5 text-amber-400 ${testingId === connector.id ? 'animate-spin' : ''}`} />
                      <span>{testingId === connector.id ? 'Pinging...' : 'Test Connection'}</span>
                    </button>

                    {isConnected ? (
                      <button
                        onClick={() => handleDisconnect(connector.id)}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => handleConnect(connector.id)}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-400 hover:bg-amber-300 text-slate-950 shadow-md shadow-amber-500/20 transition-all hover:scale-[1.02]"
                      >
                        Connect
                      </button>
                    )}

                    <button
                      onClick={() => setExpandedConnector(isExpanded ? null : connector.id)}
                      className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-[#080b11] transition-colors"
                      title="Toggle Configuration"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Test Result Toast */}
                {testRes && (
                  <div className="px-5 pb-3">
                    <div
                      className={`p-3 rounded-xl text-xs flex items-center justify-between ${
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
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#080b11] border border-emerald-500/30">
                          {testRes.latency_ms} ms latency
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Settings & Live Tool Playground Panel */}
                {isExpanded && (
                  <div className="border-t border-[#232f48] p-5 bg-[#080b11]/50 space-y-4">
                    <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                      <Sliders className="w-3.5 h-3.5 text-amber-400" />
                      <span>Connector Settings</span>
                    </div>

                    {/* Form Fields */}
                    {(connector.config_fields || []).length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {connector.config_fields.map((field) => (
                          <div key={field.key} className="space-y-1">
                            <label className="text-xs font-semibold text-slate-300">{field.label}</label>
                            {field.type === 'select' ? (
                              <select
                                value={configForms[connector.id]?.[field.key] || field.default || ''}
                                onChange={(e) => handleConfigChange(connector.id, field.key, e.target.value)}
                                className="w-full px-3 py-2 rounded-xl bg-[#080b11] border border-[#232f48] text-xs text-slate-200 focus:outline-none focus:border-amber-400"
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
                                className="w-full px-3 py-2 rounded-xl bg-[#080b11] border border-[#232f48] text-xs text-slate-200 focus:outline-none focus:border-amber-400"
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No additional configuration required for this connector.</p>
                    )}

                    {/* Live Playground */}
                    <div className="pt-3 border-t border-[#232f48] space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-300">Live Tool Playground</span>
                        <span className="text-[10px] text-slate-400">Execute query and inspect live response</span>
                      </div>

                      <div className="space-y-2">
                        {(connector.tools || []).map((t) => (
                          <div key={t.name} className="flex flex-col sm:flex-row gap-2 items-center">
                            <input
                              type="text"
                              value={toolInputs[`${connector.id}_${t.name}`] || ''}
                              onChange={(e) =>
                                setToolInputs((prev) => ({
                                  ...prev,
                                  [`${connector.id}_${t.name}`]: e.target.value,
                                }))
                              }
                              placeholder={`Query topic for ${t.name}() (e.g. Astrophysics, Botany)...`}
                              className="flex-1 w-full px-3 py-1.5 rounded-xl bg-[#080b11] border border-[#232f48] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                            />
                            <button
                              onClick={() => handleRunTool(connector.id, t.name)}
                              disabled={executingTool === `${connector.id}_${t.name}`}
                              className="px-3 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-xs font-black text-slate-950 transition-all flex items-center space-x-1.5 shrink-0"
                            >
                              <Play className="w-3 h-3 fill-slate-950" />
                              <span>{executingTool === `${connector.id}_${t.name}` ? 'Running...' : `Run ${t.name}()`}</span>
                            </button>
                          </div>
                        ))}
                      </div>

                      {/* Tool Response */}
                      {toolRes && (
                        <div className="p-3 rounded-xl bg-[#080b11] border border-[#232f48] max-h-56 overflow-y-auto">
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
          })}
        </div>
      )}
    </div>
  );
};

