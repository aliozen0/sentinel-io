FROM python:3.9-slim

WORKDIR /app

# 1. ADIM: Derleme araçlarını yükleyin
# Bazı python paketleri (chromadb, bcrypt vb.) derleme gerektirebilir. Slim imajlarda bu eksik olabilir.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. ADIM: Torch'u "CPU" sürümüyle ve özel sunucudan yükleyin
# requirements.txt içinde 'sentence-transformers' olduğu için torch zorunlu.
# Standart indirme 888MB (GPU dahil) iken, bu CPU sürümü yaklaşık 200MB'dır.
# Bu adım 'ConnectionResetError' hatasını çözer.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 3. ADIM: Kalan gereksinimleri yükleyin
COPY requirements.txt .

# Torch zaten yüklü olduğu için pip bunu tekrar indirmeyecek, sadece diğerlerini kuracak.
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# 4. ADIM: Kodları kopyala ve başlat
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]