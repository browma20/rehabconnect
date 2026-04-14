import apiClient from './apiClient';

/**
 * Medical Necessity API client
 */
class MedicalNecessityApi {
  /**
   * Add a medical necessity record
   * @param {string} patientId - Patient ID
   * @param {Object} recordData - Record data
   * @param {string} recordData.justification - Medical necessity justification
   * @param {string} recordData.clinician_id - Clinician ID
   * @param {string} [recordData.assessment_date] - Assessment date (ISO string)
   * @returns {Promise<Object>} Created record data
   */
  async addMedicalNecessityRecord(patientId, recordData) {
    return apiClient.post(`/patients/${patientId}/medical-necessity-records`, recordData);
  }

  /**
   * Get medical necessity records for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Array of medical necessity records
   */
  async getMedicalNecessityRecords(patientId) {
    return apiClient.get(`/patients/${patientId}/medical-necessity-records`);
  }

  /**
   * Get medical necessity compliance for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Medical necessity compliance data
   */
  async getMedicalNecessityCompliance(patientId) {
    return apiClient.get(`/patients/${patientId}/compliance/medical-necessity`);
  }
}

export const medicalNecessityApi = new MedicalNecessityApi();
export default medicalNecessityApi;