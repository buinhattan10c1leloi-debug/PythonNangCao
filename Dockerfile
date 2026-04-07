# Sử dụng Python 3.11 để ổn định hơn với các thư viện AI hiện tại
FROM python:3.11-slim

# Cài đặt các gói phụ thuộc hệ thống (Thêm g++ để build grpcio)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt các thư viện
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn pymysql cryptography

# Sao chép mã nguồn ứng dụng
COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./

# Cấp quyền thực thi và thiết lập môi trường
RUN chmod a+x boot.sh
ENV FLASK_APP=microblog.py

# Biên dịch ngôn ngữ
RUN flask translate compile

EXPOSE 5000

# Chỉ giữ lại MỘT lệnh ENTRYPOINT duy nhất
ENTRYPOINT ["./boot.sh"]