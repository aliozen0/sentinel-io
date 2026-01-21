FROM node:20-alpine

WORKDIR /app

# Force cache bust
ENV REBUILD_FLAG=1

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

# Development Mode (No Build Step)
EXPOSE 3000
CMD ["npm", "run", "dev"]
