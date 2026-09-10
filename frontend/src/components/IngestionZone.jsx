import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, Sparkles, BookOpen } from 'lucide-react';
import { uploadFile, ingestText } from '../services/api';

export const IngestionZone = ({ token, onIngestionSuccess, activeDoc }) => {
  const [activeTab, setActiveTab] = useState('pdf'); // 'pdf' or 'text'
  const [file, setFile] = useState(null);
  const [docTitle, setDocTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Only PDF files are supported for file upload.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
      if (!docTitle) {
        setDocTitle(selected.name.replace(/\.pdf$/i, '').replace(/[_-]/g, ' '));
      }
    }
  };

  const handleUploadPDF = async () => {
    if (!file) {
      setError('Please select a PDF document first.');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const data = await uploadFile(file, docTitle, token);
      setSuccessMsg(data.message || 'Successfully parsed and indexed document!');
      onIngestionSuccess({
        documentId: data.document_id,
        title: data.title,
        pageCount: data.page_count,
        chunkCount: data.chunk_count,
        chapters: data.chapters || []
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload document.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngestText = async () => {
    if (!rawText.trim()) {
      setError('Please paste your lecture notes or syllabus content.');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const data = await ingestText(rawText, docTitle || 'Lecture Syllabus', token);
      setSuccessMsg(data.message || 'Text successfully chunked and indexed!');
      onIngestionSuccess({
        documentId: data.document_id,
        title: data.title,
        pageCount: data.page_count,
        chunkCount: data.chunk_count,
        chapters: data.chapters || [docTitle || 'General Notes']
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to ingest text.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      {/* Tabs */}
      <div className="flex space-x-2 p-1.5 bg-slate-950/80 rounded-xl border border-slate-800/80 max-w-md mb-6">
        <button
          onClick={() => { setActiveTab('pdf'); setError(null); }}
          className={`flex-1 flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all ${
            activeTab === 'pdf'
              ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Lecture PDF</span>
        </button>
        <button
          onClick={() => { setActiveTab('text'); setError(null); }}
          className={`flex-1 flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all ${
            activeTab === 'text'
              ? 'bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Raw Text / Notes</span>
        </button>
      </div>

      {/* Active Document Indicator */}
      {activeDoc && (
        <div className="mb-6 p-4 rounded-xl bg-sky-950/30 border border-sky-800/40 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-sky-500/20 border border-sky-500/30 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-100">{activeDoc.title}</p>
              <p className="text-xs text-sky-300">
                {activeDoc.pageCount} page(s) &bull; {activeDoc.chunkCount} semantic chunks indexed
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Ready for Generation
          </span>
        </div>
      )}

      {/* PDF Upload Tab */}
      {activeTab === 'pdf' && (
        <div className="space-y-4">
          <div className="border-2 border-dashed border-slate-700 hover:border-sky-500/50 rounded-2xl p-8 text-center transition-all bg-slate-950/40 group">
            <input
              type="file"
              accept=".pdf"
              id="pdf-upload"
              className="hidden"
              onChange={handleFileChange}
            />
            <label htmlFor="pdf-upload" className="cursor-pointer flex flex-col items-center">
              <div className="w-14 h-14 rounded-2xl bg-slate-800/80 group-hover:bg-sky-500/10 group-hover:text-sky-400 text-slate-400 flex items-center justify-center mb-4 transition-all">
                <UploadCloud className="w-7 h-7" />
              </div>
              <p className="text-sm font-semibold text-slate-200">
                {file ? file.name : 'Click to select or drag & drop lecture PDF'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Strict limit: up to <strong className="text-sky-400">150 pages</strong> per upload
              </p>
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Document Focus Title (Optional)</label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="e.g. Distributed Systems & Consensus Protocols"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <button
            onClick={handleUploadPDF}
            disabled={loading || !file}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-500 to-sky-400 hover:from-sky-400 hover:to-sky-300 text-slate-950 font-bold text-sm shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Parsing PDF & Chunking Across Chapters...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 fill-slate-950" />
                <span>Ingest & Index Lecture PDF</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Raw Text Tab */}
      {activeTab === 'text' && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Topic / Lesson Title</label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="e.g. Chapter 4: Photosynthesis & Cellular Respiration"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Paste Syllabus Notes / Lecture Excerpts</label>
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste reading passages, lecture transcripts, syllabus bullet points, or review summaries here..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 font-mono leading-relaxed"
            />
          </div>

          <button
            onClick={handleIngestText}
            disabled={loading || !rawText.trim()}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-500 to-sky-400 hover:from-sky-400 hover:to-sky-300 text-slate-950 font-bold text-sm shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Indexing Notes...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 fill-slate-950" />
                <span>Ingest & Index Text</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Status Messages */}
      {error && (
        <div className="mt-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start space-x-2.5">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mt-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-start space-x-2.5">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
