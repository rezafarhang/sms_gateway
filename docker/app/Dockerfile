FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Configure Debian mirror for Iran (using Iranian mirrors)
RUN echo "deb http://mirror.arvancloud.ir/debian trixie main" > /etc/apt/sources.list && \
    echo "deb http://mirror.arvancloud.ir/debian trixie-updates main" >> /etc/apt/sources.list && \
    echo "deb http://mirror.arvancloud.ir/debian-security trixie-security main" >> /etc/apt/sources.list

WORKDIR /app

#RUN apt-get update && apt-get install -y \
#    gcc \
#    postgresql-client \
#    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY docker/app/pip-packages ./pip-packages

# Install from local packages (offline mode)
RUN pip install --no-cache-dir --no-index --find-links=./pip-packages -r requirements.txt

COPY . .

RUN chmod +x docker/app/entrypoint.sh

ENTRYPOINT ["docker/app/entrypoint.sh"]
