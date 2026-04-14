import apiClient from './apiClient';

/**
 * IDT (Interdisciplinary Team) API client
 */
class IdtApi {
  /**
   * Create an IDT meeting
   * @param {string} patientId - Patient ID
   * @param {Object} meetingData - Meeting data
   * @param {string} meetingData.meeting_datetime - Meeting datetime (ISO string)
   * @param {Array<string>} [meetingData.attendees] - Array of attendee IDs
   * @param {string} [meetingData.notes] - Meeting notes
   * @returns {Promise<Object>} Created meeting data
   */
  async createIdtMeeting(patientId, meetingData) {
    return apiClient.post(`/patients/${patientId}/idt-meetings`, meetingData);
  }

  /**
   * Get IDT meetings for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Array of IDT meetings
   */
  async getIdtMeetings(patientId) {
    return apiClient.get(`/patients/${patientId}/idt-meetings`);
  }

  /**
   * Update IDT meeting notes
   * @param {string} patientId - Patient ID
   * @param {number} meetingId - Meeting ID
   * @param {string} notes - Updated notes
   * @returns {Promise<Object>} Updated meeting data
   */
  async updateMeetingNotes(patientId, meetingId, notes) {
    return apiClient.put(`/patients/${patientId}/idt-meetings/${meetingId}`, { notes });
  }

  /**
   * Get IDT compliance for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} IDT compliance data
   */
  async getIdtCompliance(patientId) {
    return apiClient.get(`/patients/${patientId}/compliance/idt`);
  }
}

export const idtApi = new IdtApi();
export default idtApi;