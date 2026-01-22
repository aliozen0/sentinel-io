# GPU Performance Benchmark

🚀 io-Guard için örnek test projesi. Bu proje, Wizard üzerinden uzak GPU'ya deploy edilmek üzere tasarlanmıştır.

## 📁 Proje Yapısı

```
test_project/
├── main.py           # Ana entry point - benchmark runner
├── utils.py          # Yardımcı fonksiyonlar (Timer, matrix ops)
├── config.py         # Konfigürasyon ayarları
├── requirements.txt  # Bağımlılıklar (opsiyonel)
└── README.md         # Bu dosya
```

## 🎯 Ne Yapar?

1. **CPU Matrix Benchmark**: Matrix çarpımı performans testi
2. **Memory Bandwidth**: Bellek okuma/yazma hızı
3. **ML Inference Simulation**: Batch processing simülasyonu

## 🚀 Çalıştırma

```bash
# Doğrudan çalıştırma
python main.py

# Özel ayarlarla
BENCH_MATRIX_SIZE=200 BENCH_ITERATIONS=10 python main.py
```

## 📊 Örnek Çıktı

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

   GPU Performance Benchmark v1.0.0
   io-Guard test project for GPU performance testing

🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

============================================================
🖥️  CPU Matrix Multiplication Benchmark
============================================================
   Matrix Size: 100x100
   Iterations: 5
   ...
   ✅ Average Time: 0.0234s
   ⚡ Performance: 8.54 GFLOPS
```

## 🔧 io-Guard Entegrasyonu

Bu proje, io-Guard Wizard'ın aşağıdaki özelliklerini test eder:

- ✅ Multi-file project upload
- ✅ ZIP extraction
- ✅ Entry point detection (`main.py`)
- ✅ requirements.txt handling
- ✅ Remote execution via SSH/SFTP

## 📝 Lisans

MIT - io-Guard Test Project
