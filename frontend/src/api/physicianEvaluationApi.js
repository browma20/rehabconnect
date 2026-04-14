import apiClient from './apiClient';

/**
 * Physician Evaluation API client
 */
class PhysicianEvaluationApi {
  /**
   * Create a physician evaluation
   * @param {string} patientId - Patient ID
   * @param {Object} evaluationData - Evaluation data
   * @param {string} evaluationData.physician_id - Physician ID
   * @param {string} [evaluationData.evaluation_datetime] - Evaluation datetime (ISO string)
   * @param {string} [evaluationData.notes] - Evaluation notes
   * @returns {Promise<Object>} Created evaluation data
   */
  async createPhysicianEvaluation(patientId, evaluationData) {
    return apiClient.post(`/patients/${patientId}/physician-evaluations`, evaluationData);
  }

  /**
   * Get physician evaluations for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Array of physician evaluations
   */
  async getPhysicianEvaluations(patientId) {
    return apiClient.get(`/patients/${patientId}/physician-evaluations`);
  }

  /**
   * Get first-day compliance for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} First-day compliance data
   */
  async getFirstDayCompliance(patientId) {
    return apiClient.get(`/patients/${patientId}/compliance/first-day`);
  }
}

export const physicianEvaluationApi = new PhysicianEvaluationApi();
export default physicianEvaluationApi;