# Dockerfile for n8n on Render
FROM node:20-alpine

# Install dependencies
RUN apk add --no-cache curl

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

# Expose port
EXPOSE 8443

# Health check - more lenient timing
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8443/ || exit 1

# Start n8n
CMD ["npm", "start"]