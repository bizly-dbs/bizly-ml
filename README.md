# Bizly ML - Analisis Kesehatan dan Forecasting

Machine learning untuk analisis kesehatan bisnis dan peramalan penjualan, dibuat menggunakan Flask dan TensorFlow.

## Fitur

- Analisis Kesehatan Bisnis
- Peramalan Penjualan
- Endpoint API RESTful

## Persyaratan

- Python 3.10+
- pip (Python package manager)

## Instalasi

1. Clone repository:
```bash
git clone https://github.com/bizly-dbs/bizly-ml.git
cd bizly-ml
```

2. Buat dan aktifkan virtual environment (direkomendasikan):
```bash
python -m venv venv
# Untuk Windows
venv\Scripts\activate
# Untuk Unix atau MacOS
source venv/bin/activate
```

3. Install dependensi:
```bash
pip install -r requirements.txt
```

## Menjalankan Secara Lokal

1. Jalankan server Flask:
```bash
python app.py
```

Server akan berjalan di `http://localhost:5000`

## Dokumentasi API

### Base URL
- Lokal: `http://localhost:5000`
- Production: `https://bizly.rafess.my.id`

### 1. Analisis Kesehatan Bisnis

#### Endpoint
- **Path**: `/analyze`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body
```json
{
    "pemasukan": 1000000,
    "pengeluaran": 500000,
    "jumlah_transaksi": 100,
    "jumlah_hari_rugi": 5
}
```

#### Response
```json
{
    "health_status": "Sehat",
    "confidence": 0.95
}
```

### 2. Forecasting Penjualan

#### Endpoint
- **Path**: `/predict`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Parameter Query
- `n_days` (opsional): Jumlah hari untuk peramalan (1-30, default: 7)

#### Request Body
```json
[
    {
        "date": "2024-01-01",
        "total_sales": 1000
    },
    {
        "date": "2024-01-02",
        "total_sales": 1200
    }
]
```

#### Response
```json
[
    1150.5,
    1200.3,
    1250.1
]
```

## Penanganan Error

API mengembalikan kode status HTTP dan pesan error yang sesuai:

- 400: Bad Request (input tidak valid)
- 500: Internal Server Error

## Contoh Penggunaan

### Analisis Kesehatan Bisnis
```bash
curl -X POST http://localhost:5000/analyze \
-H "Content-Type: application/json" \
-d '{
    "pemasukan": 1000000,
    "pengeluaran": 500000,
    "jumlah_transaksi": 100,
    "jumlah_hari_rugi": 5
}'
```

### Peramalan Penjualan
```bash
curl -X POST "http://localhost:5000/predict?n_days=7" \
-H "Content-Type: application/json" \
-d '[
    {
        "date": "2024-01-01",
        "total_sales": 1000
    },
    {
        "date": "2024-01-02",
        "total_sales": 1200
    }
]'
```


