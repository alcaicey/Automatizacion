import { describe, it, expect, vi } from 'vitest';
import { io } from 'socket.io-client';

describe('Conexión de WebSocket', () => {
  it('debe conectar con el backend en localhost:5000', async () => {
    const socket = io('http://localhost:5000', {
      transports: ['websocket'],
      forceNew: true,
      reconnection: false,
      timeout: 2000, // Timeout de 2 segundos
    });
    
    const onConnect = vi.fn();
    const onConnectError = vi.fn();

    socket.on('connect', onConnect);
    socket.on('connect_error', onConnectError);
    
    // Esperar un tiempo prudencial para la conexión
    await new Promise((resolve) => setTimeout(resolve, 1500));

    expect(onConnect).toHaveBeenCalled();
    expect(onConnectError).not.toHaveBeenCalled();
    
    socket.disconnect();
  }, 3000); // Timeout para el test completo
}); 