import apiClient from './apiClient';

/**
 * Risk Assessment API client
 */
class RiskApi {
  /**
   * Get risk score for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Patient risk data
   */
  async getPatientRisk(patientId) {
    return apiClient.get(`/patients/${patientId}/risk`);
  }

  /**
   * Get unit-level risk summary
   * @param {Array<string>} patientIds - Array of patient IDs
   * @returns {Promise<Object>} Unit risk summary data
   */
  async getUnitRiskSummary(patientIds) {
    return apiClient.post('/unit/risk-summary', { patient_ids: patientIds });
  }

  /**
   * Get high-risk patients
   * @param {number} [threshold=60] - Risk score threshold
   * @returns {Promise<Object>} High-risk patients data
   */
  async getHighRiskPatients(threshold = 60) {
    return apiClient.get(`/patients/high-risk?threshold=${threshold}`);
  }
}

export const riskApi = new RiskApi();
export default riskApi;