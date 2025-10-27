# Dockerfile for n8n on Render
FROM node:20-alpine

# Install dependencies
RUN apk add --no-cache python3 make g++

# Create app directory
WORKDIR /usr/src/app

# Copy N8N package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy N8N application code
COPY . ./

# Set working directory for the startup command
WORKDIR /usr/src/app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S n8n -u 1001

# Change ownership
RUN chown -R n8n:nodejs /usr/src/app
USER n8n

# Expose port
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8443/healthz || exit 1

# Start n8n
CMD ["npm", "start"]