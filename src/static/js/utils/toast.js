// src/static/js/utils/toast.js

/**
 * Muestra un mensaje emergente (toast).
 * En un entorno de prueba, esto podría ser simplemente un console.log.
 * @param {string} message - El mensaje a mostrar.
 * @param {string} [type='info'] - El tipo de toast (info, success, error).
 */
export function showToast(message, type = 'info') {
  console.log(`[TOAST][${type}]: ${message}`);
} 