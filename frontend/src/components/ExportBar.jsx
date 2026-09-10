import React, { useState } from 'react';
import { FileDown, Download, Loader2, Sparkles, Check } from 'lucide-react';
import { exportPDF, exportCSV } from '../services/api';

export const ExportBar = ({ studyPack }) => {
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingCsv, setDownloadingCsv] = useState(false);
  const [pdfDone, setPdfDone] = useState(false);
  const [csvDone, setCsvDone] = useState(false);

  if (!studyPack) {
    return null;
  }

  const handleExportPDF = async () => {
    setDownloadingPdf(true);
    setPdfDone(false);
    try {
      await exportPDF(studyPack);
      setPdfDone(true);
      setTimeout(() => setPdfDone(false), 3000);
    } catch (err) {
      console.error('PDF export error:', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExportCSV = async () => {
    if (!studyPack.mcqs || studyPack.mcqs.length === 0) return;
    setDownloadingCsv(true);
    setCsvDone(false);
    try {
      await exportCSV(studyPack.mcqs);
      setCsvDone(true);
      setTimeout(() => setCsvDone(false), 3000);
    } catch (err) {
      console.error('CSV export error:', err);
    } finally {
      setDownloadingCsv(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-slate-900 via-sky-950/40 to-slate-900 border border-sky-500/30 rounded-2xl p-6 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-4">
      <div>
        <div className="flex items-center space-x-2 mb-1">
          <Sparkles className="w-4 h-4 text-sky-400" />
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
          className="flex-1 md:flex-none px-5 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20 disabled:opacity-50 transition-all hover:scale-[1.02]"
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
          className="flex-1 md:flex-none px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs flex items-center justify-center space-x-2 shadow-md disabled:opacity-50 transition-all hover:scale-[1.02]"
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
              <Download className="w-4 h-4 text-sky-400" />
              <span>Export Anki/Quizlet CSV</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
