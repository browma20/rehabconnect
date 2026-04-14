const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const buildUrl = (endpoint) => `${API_BASE_URL}${endpoint}`;

const parseJsonSafely = async (response) => {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
};

const requestJson = async (endpoint, options = {}) => {
  const response = await fetch(buildUrl(endpoint), {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload = await parseJsonSafely(response);

  if (!response.ok) {
    const message = payload?.error || `HTTP ${response.status}: ${response.statusText}`;
    const error = new Error(message);
    error.status = response.status;
    error.details = payload;
    throw error;
  }

  return payload;
};

const unwrapData = (payload) => {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return payload.data;
  }
  return payload;
};

const postWithFallback = async (primaryEndpoint, fallbackEndpoint, body) => {
  try {
    return await requestJson(primaryEndpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  } catch (error) {
    if (error?.status !== 404 || !fallbackEndpoint) {
      throw error;
    }
    return requestJson(fallbackEndpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
};

const getWithFallback = async (primaryEndpoint, fallbackEndpoint) => {
  try {
    return await requestJson(primaryEndpoint, { method: 'GET' });
  } catch (error) {
    if (error?.status !== 404 || !fallbackEndpoint) {
      throw error;
    }
    return requestJson(fallbackEndpoint, { method: 'GET' });
  }
};

export const suggestAssignment = async (sessionId) => {
  const payload = await postWithFallback(
    '/automation/suggest_assignment',
    '/automation/suggest-assignment',
    { session_id: sessionId }
  );
  return unwrapData(payload);
};

export const suggestReschedule = async (sessionId) => {
  const payload = await postWithFallback(
    '/automation/suggest_reschedule',
    '/automation/suggest-reschedule',
    { session_id: sessionId }
  );
  return unwrapData(payload);
};

export const submitOverride = async ({
  sessionId,
  overrideType,
  overrideValue,
  session_id,
  override_type,
  override_value,
}) => {
  const sid = sessionId || session_id;
  const type = overrideType || override_type;
  const value = overrideValue || override_value;

  const payload = await requestJson('/automation/override', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sid,
      override_type: type,
      override_value: value,
    }),
  });
  return unwrapData(payload);
};

export const getAuditTrail = async (sessionId) => {
  const encoded = encodeURIComponent(sessionId);
  const payload = await getWithFallback(
    `/automation/audit?session_id=${encoded}`,
    `/automation/audit/${encoded}`
  );
  return unwrapData(payload);
};

// Backward-compatible aliases for existing UI usage.
export const logOverride = submitOverride;

export const logManualAction = async (payload) => {
  const response = await requestJson('/automation/manual-action', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return unwrapData(response);
};

const automationApi = {
  suggestAssignment,
  suggestReschedule,
  submitOverride,
  getAuditTrail,
  logOverride,
  logManualAction,
};

export default automationApi;
export { automationApi };
