FROM node:20-alpine AS build

WORKDIR /app

# Copy the frontend app package files
COPY ad-personalizer-frontend/package*.json ./
RUN npm ci

# Copy the rest of the frontend source code
COPY ad-personalizer-frontend/ ./
RUN npm run build

# Use Nginx to serve the built static assets
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the custom Nginx config for routing and backend proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets from the builder stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
