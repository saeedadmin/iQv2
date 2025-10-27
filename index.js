/**
 * N8N Main Entry Point
 * Starts the N8N workflow automation server
 */

console.log('🚀 Starting N8N server...');
console.log(`📊 N8N Configuration:`);
console.log(`   - Host: ${process.env.N8N_HOST || '0.0.0.0'}`);
console.log(`   - Port: ${process.env.N8N_PORT || '8443'}`);
console.log(`   - Protocol: ${process.env.N8N_PROTOCOL || 'https'}`);

// Set environment variables
process.env.N8N_HOST = process.env.N8N_HOST || '0.0.0.0';
process.env.N8N_PORT = process.env.N8N_PORT || '8443';
process.env.N8N_PROTOCOL = process.env.N8N_PROTOCOL || 'https';
process.env.N8N_EDITOR_BASE_URL = process.env.N8N_EDITOR_BASE_URL || 'https://iqv2.onrender.com';

// Start N8N using spawn for better process management
const { spawn } = require('child_process');
const n8nProcess = spawn('n8n', ['start'], { 
  stdio: 'inherit',
  env: process.env
});

n8nProcess.on('error', (error) => {
  console.error('❌ Failed to start N8N process:', error);
  process.exit(1);
});

n8nProcess.on('exit', (code) => {
  console.log(`N8N process exited with code ${code}`);
  process.exit(code);
});

console.log('✅ N8N server is starting...');