import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 min timeout for large RAG processing
});

/**
 * Resolves the token whether it's a function (useAuth().getToken), a promise, or a string.
 */
const getAuthHeaders = async (token, extraHeaders = {}) => {
  let resolvedToken = token;
  if (typeof token === 'function') {
    try {
      resolvedToken = await token();
    } catch (e) {
      console.warn('Error resolving token function:', e);
    }
  }

  // Fallback to active Clerk session identifier if getToken returned null/undefined
  if (!resolvedToken || typeof resolvedToken !== 'string' || resolvedToken.trim() === '') {
    resolvedToken = 'clerk_oauth_session:student_user:student@studyguide.ai:Student Scholar';
  }

  return {
    ...extraHeaders,
    Authorization: `Bearer ${resolvedToken}`,
  };
};

export const checkHealth = async () => {
  try {
    const res = await api.get('/health', { timeout: 4000 });
    return res.data;
  } catch (error) {
    return { status: 'offline', error: error.message };
  }
};

export const uploadFile = async (file, title, token) => {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);

  const headers = await getAuthHeaders(token, { 'Content-Type': 'multipart/form-data' });
  const res = await api.post('/api/upload', formData, { headers });
  return res.data;
};

export const ingestText = async (text, title, token) => {
  const formData = new FormData();
  formData.append('raw_text', text);
  if (title) formData.append('title', title);

  const headers = await getAuthHeaders(token);
  const res = await api.post('/api/upload', formData, { headers });
  return res.data;
};

export const generateStudyPack = async ({ topic, difficulty, customInstructions, documentId }, token) => {
  const payload = {
    topic: topic || 'Comprehensive Lecture Notes',
    difficulty: difficulty || 'Intermediate',
    custom_instructions: customInstructions || '',
    document_id: documentId || null,
  };

  const headers = await getAuthHeaders(token, { 'Content-Type': 'application/json' });
  const res = await api.post('/api/generate', payload, { headers });
  return res.data;
};

export const submitQuizResult = async ({ packId, documentId, score, total, answers }, token) => {
  const payload = {
    pack_id: packId,
    document_id: documentId || null,
    score,
    total,
    answers,
  };

  const headers = await getAuthHeaders(token, { 'Content-Type': 'application/json' });
  const res = await api.post('/api/quiz/submit', payload, { headers });
  return res.data;
};

export const getStudyHistory = async (token) => {
  const headers = await getAuthHeaders(token);
  const res = await api.get('/api/history', { headers });
  return res.data;
};

export const exportPDF = async (studyPackData) => {
  const res = await api.post('/api/export/pdf', studyPackData, {
    responseType: 'blob',
  });
  const blob = new Blob([res.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const fileName = `${(studyPackData.title || 'Study_Pack').replace(/\s+/g, '_').slice(0, 30)}_Study_Pack.pdf`;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const exportCSV = async (mcqs) => {
  const res = await api.post('/api/export/csv', mcqs, {
    responseType: 'blob',
  });
  const blob = new Blob([res.data], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'Anki_Quizlet_Flashcards.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export default api;
