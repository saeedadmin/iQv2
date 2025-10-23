# Dockerfile for n8n on Render
FROM node:18-alpine

# Install dependencies
RUN apk add --no-cache python3 make g++

# Create app directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S n8n -u 1001

# Change ownership
RUN chown -R n8n:nodejs /usr/src/app
USER n8n

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:10000/healthz || exit 1

# Start n8n
CMD ["npm", "start"]