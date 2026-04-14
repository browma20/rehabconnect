import apiClient from './apiClient';

/**
 * Therapy Minutes API client
 */
class TherapyMinutesApi {
  /**
   * Add a therapy session
   * @param {string} patientId - Patient ID
   * @param {Object} sessionData - Session data
   * @param {string} sessionData.therapy_type - Type of therapy (PT/OT/ST)
   * @param {number} sessionData.minutes - Minutes of therapy
   * @param {string} sessionData.therapist_id - Therapist ID
   * @param {string} [sessionData.timestamp] - Session timestamp (ISO string)
   * @returns {Promise<Object>} Created session data
   */
  async addTherapySession(patientId, sessionData) {
    return apiClient.post(`/patients/${patientId}/therapy-sessions`, sessionData);
  }

  /**
   * Get therapy sessions for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Array of therapy sessions
   */
  async getTherapySessions(patientId) {
    return apiClient.get(`/patients/${patientId}/therapy-sessions`);
  }

  /**
   * Get daily compliance for a patient
   * @param {string} patientId - Patient ID
   * @param {string} [date] - Date in YYYY-MM-DD format (defaults to today)
   * @returns {Promise<Object>} Daily compliance data
   */
  async getDailyCompliance(patientId, date) {
    const params = date ? `?date=${date}` : '';
    return apiClient.get(`/patients/${patientId}/compliance/daily${params}`);
  }

  /**
   * Get rolling compliance for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Rolling compliance data
   */
  async getRollingCompliance(patientId) {
    return apiClient.get(`/patients/${patientId}/compliance/rolling`);
  }

  /**
   * Get therapy summary for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Therapy summary data
   */
  async getTherapySummary(patientId) {
    return apiClient.get(`/patients/${patientId}/therapy-summary`);
  }
}

export const therapyMinutesApi = new TherapyMinutesApi();
export default therapyMinutesApi;