FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for mysqlclient and locales
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate Thai locale
RUN sed -i -e 's/# th_TH.UTF-8 UTF-8/th_TH.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=th_TH.UTF-8

ENV LANG th_TH.UTF-8
ENV LC_ALL th_TH.UTF-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]