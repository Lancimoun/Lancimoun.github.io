# Serves the single-page portfolio. Static file, no build step, no dependencies.
# GitHub Pages is the primary host; this exists so the site can also run on
# Railway when Pages/Actions is unavailable.
FROM python:3.12-slim
WORKDIR /site
COPY index.html ./
# Railway injects $PORT. Bind all interfaces so the platform can route to it.
CMD ["sh", "-c", "python -m http.server ${PORT:-8080} --bind 0.0.0.0"]
