const io = require('socket.io-client');
const socket = io('http://127.0.0.1:5000', { transports: ['websocket'] });
socket.on('connect', () => {
    console.log('Successfully connected!');
});
socket.on('status', (data) => {
    console.log('Received status:', typeof data, data);
});
socket.on('error', (err) => console.log('Error:', err));
socket.on('connect_error', (err) => console.log('Connect Error:', err.message));
