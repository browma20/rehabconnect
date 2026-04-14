import apiClient from './apiClient';

/**
 * Functional Assessment API client
 */
class FunctionalApi {
  /**
   * Add a functional score
   * @param {string} patientId - Patient ID
   * @param {Object} scoreData - Score data
   * @param {string} scoreData.score_type - Type of functional score
   * @param {number} scoreData.score_value - Score value
   * @param {string} scoreData.assessor_id - Assessor ID
   * @param {string} [scoreData.assessment_date] - Assessment date (ISO string)
   * @returns {Promise<Object>} Created score data
   */
  async addFunctionalScore(patientId, scoreData) {
    return apiClient.post(`/patients/${patientId}/functional-scores`, scoreData);
  }

  /**
   * Get functional scores for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Array of functional scores
   */
  async getFunctionalScores(patientId) {
    return apiClient.get(`/patients/${patientId}/functional-scores`);
  }

  /**
   * Get functional summary for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Functional summary data
   */
  async getFunctionalSummary(patientId) {
    return apiClient.get(`/patients/${patientId}/functional-summary`);
  }

  /**
   * Get functional compliance for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Functional compliance data
   */
  async getFunctionalCompliance(patientId) {
    return apiClient.get(`/patients/${patientId}/compliance/functional`);
  }
}

export const functionalApi = new FunctionalApi();
export default functionalApi;