# /frontend/Dockerfile
# A simple Dockerfile for running the Next.js frontend in development mode.

# Use the official Node.js 18 image as the base.
FROM node:18-alpine

# Set the working directory inside the container.
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker layer caching.
COPY package*.json ./

# Install all dependencies.
RUN npm install

# Copy the rest of the application source code into the container.
COPY . .

# Expose port 3000 to allow communication with the Next.js dev server.
EXPOSE 3000

# The command to start the development server.
CMD ["npm", "run", "dev"]
