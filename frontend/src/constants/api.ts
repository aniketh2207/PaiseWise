export const API_BASE_URL = "https://REPLACE_WITH_DEPLOYED_BACKEND_URL";
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
