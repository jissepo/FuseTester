# Use latest stable Node.js Alpine for smaller image size
FROM node:alpine

# Set working directory
WORKDIR /app

# Create app user for security
RUN addgroup -g 1001 -S nodejs && \
  adduser -S fusetester -u 1001

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create data directory and set permissions before switching user
RUN mkdir -p /app/data && \
    chown -R fusetester:nodejs /app && \
    chmod -R 755 /app && \
    chmod 777 /app/data

USER fusetester

# Create a volume mount point that will be writable
VOLUME ["/app/data"]

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => { process.exit(1) })"

# Start the application
CMD ["node", "server.js"]
