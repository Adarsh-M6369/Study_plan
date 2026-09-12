import React, { useState } from 'react';
import { FileDown, Download, Loader2, Sparkles, Check } from 'lucide-react';
import { exportPDF, exportCSV } from '../services/api';

export const ExportBar = ({ studyPack, token }) => {
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingCsv, setDownloadingCsv] = useState(false);
  const [pdfDone, setPdfDone] = useState(false);
  const [csvDone, setCsvDone] = useState(false);
  const [exportError, setExportError] = useState(null);

  if (!studyPack) {
    return null;
  }

  const handleExportPDF = async () => {
    setDownloadingPdf(true);
    setPdfDone(false);
    setExportError(null);
    try {
      await exportPDF(studyPack, token);
      setPdfDone(true);
      setTimeout(() => setPdfDone(false), 3000);
    } catch (err) {
      console.error('PDF export error:', err);
      setExportError(err.message || 'Failed to download PDF. Please try again.');
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExportCSV = async () => {
    if (!studyPack.mcqs || studyPack.mcqs.length === 0) return;
    setDownloadingCsv(true);
    setCsvDone(false);
    setExportError(null);
    try {
      await exportCSV(studyPack.mcqs, token);
      setCsvDone(true);
      setTimeout(() => setCsvDone(false), 3000);
    } catch (err) {
      console.error('CSV export error:', err);
      setExportError(err.message || 'Failed to export CSV. Please try again.');
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setDownloadingCsv(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="bg-gradient-to-r from-[#080b11] via-[#141b2d] to-[#080b11] border border-amber-400/30 rounded-2xl p-6 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <h3 className="font-extrabold text-base text-slate-100">Study Guide Export Center</h3>
          </div>
          <p className="text-xs text-slate-400">
            Download printable ReportLab PDF study pack or export flashcards for Anki / Quizlet
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* PDF Download Button */}
          <button
            onClick={handleExportPDF}
            disabled={downloadingPdf}
            className="flex-1 md:flex-none px-5 py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs flex items-center justify-center space-x-2 shadow-lg shadow-amber-500/20 disabled:opacity-50 transition-all hover:scale-[1.02]"
          >
            {downloadingPdf ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating PDF...</span>
              </>
            ) : pdfDone ? (
              <>
                <Check className="w-4 h-4" />
                <span>PDF Downloaded!</span>
              </>
            ) : (
              <>
                <FileDown className="w-4 h-4" />
                <span>Download Study Pack PDF</span>
              </>
            )}
          </button>

          {/* CSV Anki Flashcards Export */}
          <button
            onClick={handleExportCSV}
            disabled={downloadingCsv || !studyPack.mcqs?.length}
            className="flex-1 md:flex-none px-5 py-3 rounded-xl bg-[#141b2d] hover:bg-[#1d273e] text-slate-200 border border-[#232f48] font-bold text-xs flex items-center justify-center space-x-2 shadow-md disabled:opacity-50 transition-all hover:scale-[1.02]"
          >
            {downloadingCsv ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Exporting CSV...</span>
              </>
            ) : csvDone ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" />
                <span>Flashcards Exported!</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 text-amber-400" />
                <span>Export Anki/Quizlet CSV</span>
              </>
            )}
          </button>
        </div>
      </div>

      {exportError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold animate-fadeIn">
          {exportError}
        </div>
      )}
    </div>
  );
};

