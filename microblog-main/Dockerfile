FROM python:3.11-slim

WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết (gcc, libpq-dev)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python từ requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Cấu hình biến môi trường Flask
ENV FLASK_APP=microblog.py
EXPOSE 5000

# Cấp quyền và chạy file khởi động boot.sh
RUN chmod +x boot.sh
ENTRYPOINT ["./boot.sh"]FROM python:3.11-slim

WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết (gcc, libpq-dev)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python từ requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Cấu hình biến môi trường Flask
ENV FLASK_APP=microblog.py
EXPOSE 5000

# Cấp quyền và chạy file khởi động boot.sh
RUN chmod +x boot.sh
ENTRYPOINT ["./boot.sh"]