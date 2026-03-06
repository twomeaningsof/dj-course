# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.5.1
# Use specific alpine version for reproducibility and smaller size
FROM node:${NODE_VERSION}-alpine AS base

# Reduce process privileges
USER node
WORKDIR /app

# Dependencies stage
FROM base AS deps
USER root
COPY package*.json ./
# Install dependencies including devDependencies for build/dev
RUN --mount=type=cache,target=/root/.npm npm ci

# Development stage
FROM base AS dev
USER root
COPY --from=deps /app/node_modules ./node_modules
COPY . .
USER node 
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Builder stage for production
FROM base AS builder
USER root
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine AS prod
COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /app/package.json /usr/share/nginx/html/version.txt 
# Optional: Add custom nginx.conf if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
