import { writable } from 'svelte/store';

export const user = writable(null); // { username, id, chips }
export const currentTable = writable(null); // table_id
export const tableState = writable(null); // Full table state
export const socket = writable(null);

export function connectWebSocket(tableId) {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://localhost:8000/ws/${tableId}`);

        const timeout = setTimeout(() => {
            reject(new Error('Connection timeout'));
            ws.close();
        }, 5000);

        ws.onopen = () => {
            console.log('Connected to table', tableId);
            clearTimeout(timeout);
            socket.set(ws);
            resolve(ws);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
            if (data.type === 'update') {
                tableState.set(data.state);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            clearTimeout(timeout);
            reject(new Error('Connection failed'));
        };

        ws.onclose = () => {
            console.log('Disconnected');
            socket.set(null);
        };
    });
}
