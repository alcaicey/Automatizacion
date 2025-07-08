// src/static/js/utils/api.js

/**
 * Realiza una solicitud a la API.
 * @param {string} url - La URL del endpoint.
 * @param {object} [options={}] - Opciones para fetch.
 * @returns {Promise<any>} - La respuesta de la API en formato JSON.
 */
export async function fetchData(url, options = {}) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
} 