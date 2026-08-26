# FILE PURPOSE: Container image for the Flask app (TDR §9).
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. FROM python:3.12-slim.
# 2. Set ENV PYTHONUNBUFFERED=1, PYTHONDONTWRITEBYTECODE=1,
#    PIP_NO_CACHE_DIR=1 so logs stream immediately and pip doesn't cache
#    wheels inside the image layer.
# 3. WORKDIR /code.
# 4. COPY requirements.txt first and RUN pip install -r requirements.txt
#    BEFORE copying the rest of the source, so dependency installs are
#    Docker-layer-cached across rebuilds.
# 5. COPY . . after the pip install step.
# 6. EXPOSE 5000.
# 7. CMD should run Gunicorn in production form:
#    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app — docker-compose.yml overrides
#    this with the Flask dev server for local dev with live reload.
#
# DEBUGGING:
# # RUN echo "[DEBUG] image build reached this layer"
#
# OFFLINE DOCKER TEST CASES:
# - `docker build .` succeeds with zero network access beyond the pip
#   install step.
# - The built image's CMD starts Gunicorn bound to 0.0.0.0:5000.
