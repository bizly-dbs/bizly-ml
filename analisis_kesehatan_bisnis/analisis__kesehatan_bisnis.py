# -*- coding: utf-8 -*-
"""Analisis__Kesehatan_Bisnis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1w5nLeGtuicUT4EkGi3mcx7NvYUGJBUnA

# Import Library

Impor library yang diperlukan
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping

import warnings
warnings.filterwarnings("ignore")

"""# Data Loading & Persiapan Awal

Menggabungkan file CSV
"""

file_paths = [
    'umkm_dataset/data_transaksi_umkm_2022.csv',
    'umkm_dataset/data_transaksi_umkm_2023.csv',
    'umkm_dataset/data_transaksi_umkm_2024.csv',
    'umkm_dataset/data_transaksi_umkm_2025.csv',
    'umkm_dataset/data_transaksi_umkm_nasi_padang.csv'
]

dfs = []
for file_path in file_paths:
    df = pd.read_csv(file_path)
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

"""Cek struktur dasar DataFrame"""

df.info()

df.head()

"""# Data Preprocessing & Ekstraksi Fitur Harian

 Mengolah semua transaksi lalu menghasilkan DataFrame “daily” yang berisi ringkasan (aggregate) setiap hari per toko

Standarisasi nama kolom
"""

df.columns = df.columns.str.lower()

"""Konversi tanggal menjadi tipe datetime"""

df['tanggal'] = pd.to_datetime(df['tanggal'])

"""Memisahkan nominal menjadi kolom “pemasukan” dan “pengeluaran”"""

df['pengeluaran'] = df.apply(lambda row: row['nominal'] if row['jenis'] == 'pengeluaran' else 0, axis=1)
df['pemasukan'] = df.apply(lambda row: row['nominal'] if row['jenis'] == 'pemasukan' else 0, axis=1)

"""Tambah kolom 'periode_minggu' (akhir periode Senin)"""

df['periode_minggu'] = df['tanggal'].dt.to_period('W-MON').apply(lambda r: r.start_time)

"""Agregasi per minggu"""

weekly = (
    df
    .groupby(['nama toko', 'periode_minggu'])
    .agg({
        'pemasukan':   'sum',
        'pengeluaran': 'sum',
        'nominal':     'count'   # ini akan jadi jumlah_transaksi
    })
    .rename(columns={'nominal': 'jumlah_transaksi'})
    .reset_index()
)

"""Tambahkan kolom 'laba_bersih' & 'rasio_keuangan'"""

weekly['laba_bersih'] = weekly['pemasukan'] - weekly['pengeluaran']
weekly['rasio_keuangan'] = weekly['pemasukan'] / (weekly['pengeluaran'] + 1)

"""hitung jumlah hari rugi perminggu"""

harian = (
    df
    .groupby(['nama toko', 'tanggal'])
    .agg({'pemasukan': 'sum', 'pengeluaran': 'sum'})
    .reset_index()
)
harian['flag_rugi'] = (harian['pengeluaran'] > harian['pemasukan']).astype(int)
harian['periode_minggu'] = harian['tanggal'].dt.to_period('W-MON').apply(lambda r: r.start_time)

hari_rugi_per_minggu = (
    harian
    .groupby(['nama toko', 'periode_minggu'])['flag_rugi']
    .sum()
    .reset_index(name='jumlah_hari_rugi')
)

"""Merge jumlah_hari_rugi ke weekly"""

weekly = weekly.merge(
    hari_rugi_per_minggu,
    on=['nama toko', 'periode_minggu'],
    how='left'
)

weekly['jumlah_hari_rugi'] = weekly['jumlah_hari_rugi'].fillna(0).astype(int)

weekly.head()

"""Menentukan Label Multi‐Kelas"""

def kategori_laba(row):
    rasio = row['rasio_keuangan']
    if rasio >= 1.2:
        return 'Sehat'
    elif rasio >= 1.0:
        return 'Cukup Sehat'
    elif rasio >= 0.8:
        return 'Perlu Perhatian'
    else:
        return 'Perlu Penanganan Khusus'

weekly['label_kelas'] = weekly.apply(kategori_laba, axis=1)

# Tampilkan distribusi label
print(weekly['label_kelas'].value_counts())

weekly.head()

"""# Data Preparation

Persiapan Data untuk Model

Membuat fitur turunan

Untuk `rasio_transaksi`
> *"Rasio ini saya gunakan untuk mengukur efisiensi aktivitas transaksi terhadap pengeluaran. Semakin tinggi nilainya, berarti setiap unit pengeluaran menghasilkan lebih banyak transaksi. Penambahan +1 pada penyebut bertujuan untuk menghindari pembagian dengan nol ketika tidak ada pengeluaran. Konsep dasarnya mirip dengan rasio efisiensi dalam analisis keuangan, meskipun ini disesuaikan untuk konteks data mingguan."*

Untuk `persen_pengeluaran`
> *"Rasio ini menunjukkan seberapa besar proporsi pengeluaran dibanding total arus kas (pemasukan + pengeluaran). Ini berguna untuk memahami dominasi belanja terhadap keseluruhan aktivitas keuangan. Nilai kecil 1e-9 ditambahkan untuk mencegah error pembagian nol. Ini mirip dengan pendekatan proporsi dalam laporan keuangan atau rasio cost-to-income di sektor keuangan."*

Rumus ini bukan dari literatur tunggal, tapi merupakan bentuk praktik umum dalam data analysis — konsepnya terinspirasi dari rasio efisiensi dan rasio aktivitas keuangan. [Financial Analysis Ratio](https://www.jurnal.id/id/blog/rumus-rasio-keuangan-untuk-analisis-rasio-keuangan-perusahaan/?utm_source=chatgpt.com)
"""

# Buat fitur turunan:
weekly['rasio_transaksi'] = weekly['jumlah_transaksi'] / (weekly['pengeluaran'] + 1)
weekly['persen_pengeluaran'] = weekly['pengeluaran'] / (weekly['pemasukan'] + weekly['pengeluaran'] + 1e-9)

# Pilih fitur yang TIDAK memuat pemasukan/pengeluaran secara mentah
features = [
    'pemasukan',
    'pengeluaran',
    'jumlah_transaksi',
    'jumlah_hari_rugi',
    'rasio_transaksi',
    'persen_pengeluaran'
]

X = weekly[features]
y = weekly['label_kelas']

"""Encode Label Menjadi Numerik"""

le = LabelEncoder()
y_enc = le.fit_transform(y)
print("Mapping label:", dict(zip(le.classes_, le.transform(le.classes_))))

# One-hot encoding untuk klasifikasi multi-kelas
y_cat = to_categorical(y_enc)

"""Normalisasi"""

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

"""Split data menjadi training & testing"""

X_train, X_test, y_train_cat, y_test_cat, y_train_enc, y_test_enc = train_test_split(
    X_scaled, y_cat, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

"""pembuatan Model"""

model = Sequential([
    Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(4, activation='softmax')  # 4 kelas output
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

"""Pelatihan Model"""

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True,
    verbose=1
)

history = model.fit(
    X_train, y_train_cat,
    epochs=100,
    batch_size=16,
    validation_split=0.1,
    verbose=1,
    callbacks=[early_stop]
)

test_loss, test_acc = model.evaluate(X_test, y_test_cat)
print(f"\nTest Accuracy: {test_acc:.4f}")

# Prediksi kelas dari probabilitas
y_pred_probs = model.predict(X_test)
y_pred_classes = np.argmax(y_pred_probs, axis=1)

# Laporan klasifikasi
print("\n=== Classification Report (Neural Network Multi-Kelas) ===")
print(classification_report(y_test_enc, y_pred_classes, target_names=le.classes_))

# Confusion matrix
print("=== Confusion Matrix ===")
print(confusion_matrix(y_test_enc, y_pred_classes))

plt.figure(figsize=(10, 5))
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Accuracy per Epoch')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.show()

!pip install tensorflowjs

import os
import json

os.makedirs('analisis_kesehatan_bisnis/model_tfjs', exist_ok=True)

model.export('analisis_kesehatan_bisnis/model_tfjs/saved_model')

scaler_params = {
    'scale_': scaler.scale_.tolist(),
    'min_': scaler.min_.tolist(),
    'data_min_': scaler.data_min_.tolist(),
    'data_max_': scaler.data_max_.tolist(),
    'data_range_': scaler.data_range_.tolist(),
    'n_samples_seen_': scaler.n_samples_seen_
}
with open('analisis_kesehatan_bisnis/model_tfjs/scaler_params.json', 'w') as f:
    json.dump(scaler_params, f)

label_classes = le.classes_.tolist()
with open('analisis_kesehatan_bisnis/model_tfjs/label_classes.json', 'w') as f:
    json.dump(label_classes, f)

!tensorflowjs_converter --input_format=tf_saved_model --output_format=tfjs_graph_model --signature_name=serving_default --saved_model_tags=serve analisis_kesehatan_bisnis/model_tfjs/saved_model analisis_kesehatan_bisnis/model_tfjs

"""inference Model"""

def prediksi_kondisi_keuangan(data_baru: pd.DataFrame):
    print(">> Mulai prediksi")

    data_baru['rasio_transaksi'] = data_baru['jumlah_transaksi'] / (data_baru['pengeluaran'] + 1)
    data_baru['persen_pengeluaran'] = data_baru['pengeluaran'] / (data_baru['pemasukan'] + data_baru['pengeluaran'] + 1e-9)

    features = [
        'pemasukan',
        'pengeluaran',
        'jumlah_transaksi',
        'jumlah_hari_rugi',
        'rasio_transaksi',
        'persen_pengeluaran'
    ]
    X_new = data_baru[features]
    X_new_scaled = scaler.transform(X_new)

    print(">> Transformasi selesai, mulai prediksi")
    y_probs = model.predict(X_new)
    print(">> Probabilitas:", y_probs)

    y_pred_class = np.argmax(y_probs, axis=1)
    label_pred = le.inverse_transform(y_pred_class)

    print(">> Hasil kelas:", label_pred)
    return label_pred[0], data_baru['rasio_transaksi'], data_baru['persen_pengeluaran']

# Contoh data baru yang ingin diprediksi
data_baru = pd.DataFrame([{
    'pemasukan': 4000000,
    'pengeluaran': 3950000,
    'jumlah_transaksi': 10,
    'jumlah_hari_rugi': 6
}])

# Panggil fungsi prediksi dan tampilkan hasil
hasil = prediksi_kondisi_keuangan(data_baru)
print("Prediksi kondisi keuangan:", hasil)

import shutil

shutil.make_archive('model_tfjs_export', 'zip', 'analisis_kesehatan_bisnis/model_tfjs')

weekly.tail()