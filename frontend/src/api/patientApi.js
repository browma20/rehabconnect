import apiClient from './apiClient';

/**
 * Patient API client
 */
class PatientApi {
  /**
   * Create a new patient
   * @param {Object} patientData - Patient data
   * @param {string} patientData.patient_id - Unique patient identifier
   * @param {string} patientData.name - Patient name
   * @param {string} [patientData.admission_datetime] - Admission datetime (ISO string)
   * @returns {Promise<Object>} Created patient data
   */
  async createPatient(patientData) {
    return apiClient.post('/patients', patientData);
  }

  /**
   * Get patient details
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Patient data
   */
  async getPatient(patientId) {
    return apiClient.get(`/patients/${patientId}`);
  }

  /**
   * Update patient information
   * @param {string} patientId - Patient ID
   * @param {Object} updateData - Fields to update
   * @returns {Promise<Object>} Updated patient data
   */
  async updatePatient(patientId, updateData) {
    return apiClient.put(`/patients/${patientId}`, updateData);
  }

  /**
   * Delete a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Success message
   */
  async deletePatient(patientId) {
    return apiClient.delete(`/patients/${patientId}`);
  }

  /**
   * List all patients
   * @returns {Promise<Array>} Array of patients
   */
  async listPatients() {
    return apiClient.get('/patients');
  }
}

export const patientApi = new PatientApi();
export default patientApi;