import apiClient from './apiClient';

/**
 * Integration API client for data import/export
 */
class IntegrationApi {
  /**
   * Export patient data as CSV
   * @param {string} patientId - Patient ID
   * @returns {Promise<Blob>} CSV file blob
   */
  async exportPatientCsv(patientId) {
    const response = await apiClient.request(`/patients/${patientId}/export/csv`, {
      responseType: 'blob'
    });
    return response.blob();
  }

  /**
   * Export patient data as FHIR Bundle
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} FHIR Bundle
   */
  async exportPatientFhir(patientId) {
    return apiClient.get(`/patients/${patientId}/export/fhir`);
  }

  /**
   * Export patient data as HL7 message
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} HL7 message data
   */
  async exportPatientHl7(patientId) {
    return apiClient.get(`/patients/${patientId}/export/hl7`);
  }

  /**
   * Import data from CSV file
   * @param {File} csvFile - CSV file to import
   * @returns {Promise<Object>} Import result
   */
  async importCsv(csvFile) {
    return apiClient.upload('/import/csv', csvFile);
  }

  /**
   * Import data from FHIR Bundle
   * @param {Object} fhirBundle - FHIR Bundle to import
   * @returns {Promise<Object>} Import result
   */
  async importFhir(fhirBundle) {
    return apiClient.post('/import/fhir', fhirBundle);
  }

  /**
   * Import data from HL7 message
   * @param {string} hl7Message - HL7 message string
   * @returns {Promise<Object>} Import result
   */
  async importHl7(hl7Message) {
    return apiClient.post('/import/hl7', { hl7_message: hl7Message });
  }
}

export const integrationApi = new IntegrationApi();
export default integrationApi;