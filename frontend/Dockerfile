# Image for the Vue frontend. It runs the Vite dev server, the same way you
# run it without Docker.
FROM node:22-alpine

WORKDIR /app

# Install packages before copying the code, so Docker can reuse this step
# when only your code changes. This uses npm install instead of npm ci
# because a lock file made on macOS or Windows can miss Linux-only packages.
COPY package.json package-lock.json ./
RUN npm install

COPY . .

# --host makes Vite listen on every network interface. Without it, Vite
# listens only inside the container, and your browser can't reach it.
CMD ["npm", "run", "dev", "--", "--host"]
