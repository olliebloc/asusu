import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
});

export async function translateUrl(videoUrl, targetLanguages, sourceLanguage = null) {
  const response = await client.post('/translate', {
    video_url: videoUrl,
    target_languages: targetLanguages,
    source_language: sourceLanguage,
  });
  return response.data;
}

export async function translateFile(file, targetLanguages, sourceLanguage = null) {
  const formData = new FormData();
  formData.append('video_file', file);
  formData.append('target_languages', targetLanguages.join(','));
  if (sourceLanguage) formData.append('source_language', sourceLanguage);
  const response = await client.post('/translate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getJobStatus(jobId) {
  const response = await client.get(`/jobs/${jobId}`);
  return response.data;
}

export async function getLanguages() {
  const response = await client.get('/languages');
  return response.data;
}

export default client;
