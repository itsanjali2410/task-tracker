# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
ARG REACT_APP_BACKEND_URL=http://backend:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the static build
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/build ./build

# Create .env file from build args if needed
ARG REACT_APP_BACKEND_URL=http://backend:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"]
