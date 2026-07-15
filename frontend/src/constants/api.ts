import Constants from 'expo-constants';

const getBackendUrl = (): string => {
  const hostUri = Constants.expoConfig?.hostUri;
  if (!hostUri) {
    // Fallback to localhost
    return 'http://localhost:8000';
  }
  // hostUri typically looks like "192.168.88.7:8081" or "192.168.x.x:19000"
  const ip = hostUri.split(':')[0];
  return `http://${ip}:8000`;
};

export const API_BASE_URL = getBackendUrl();
export const API_ROUTES = {
  dashboardSummary: `${API_BASE_URL}/api/dashboard/summary`,
  annotationQueue: `${API_BASE_URL}/api/get_annotation_queue`,
  annotateTransaction: (id: number) => `${API_BASE_URL}/api/transactions/${id}/annotate`,
  uploadStatement: `${API_BASE_URL}/api/upload-statement`,
  generateReport: `${API_BASE_URL}/api/reports/generate`,
  downloadReport: `${API_BASE_URL}/api/reports/download`,
  sendReport: `${API_BASE_URL}/api/reports/send`,
  recipients: `${API_BASE_URL}/api/recipients`,
  deleteRecipient: (id: number) => `${API_BASE_URL}/api/recipients/${id}`,
  chat: `${API_BASE_URL}/api/chat`,
};
