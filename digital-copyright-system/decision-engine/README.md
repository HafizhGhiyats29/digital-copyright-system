# Decision Engine - Penjelasan Kode Per Fungsi

Decision engine adalah service yang mengubah skor kemiripan gambar menjadi keputusan sistem. Service ini tidak menghitung similarity. Similarity sudah dihitung oleh `similarity-check-service`; decision engine hanya membaca skor lalu menentukan apakah gambar termasuk aman, perlu review manual, atau berisiko tinggi.

## Gambaran Alur

```text
Upload Service
  -> mengirim overall_score, clip_score, cnn_score
  -> Decision Engine
    -> pilih threshold preset/custom
    -> validasi threshold
    -> cek high / medium / possible / low / very low
    -> kirim hasil keputusan
```

Output decision engine dipakai oleh upload service untuk menentukan:

- `allowed`: metadata boleh didaftarkan.
- `review_required`: perlu approval manual.
- `blocked`: registrasi ditolak karena kemiripan tinggi.

## Struktur Folder

```text
decision-engine/
  app.py
  config/
    settings.py
    settings.yaml
  routers/
    decision_router.py
  schemas/
    decision_schema.py
  services/
    decision_service.py
  utils/
    internal_auth.py
    logger.py
```

## `app.py`

### `app = FastAPI(title="Upload Service")`

Membuat instance aplikasi FastAPI.

Catatan:
- Secara fungsi sudah benar, tetapi title masih tertulis `"Upload Service"`.
- Supaya konsisten, lebih baik nanti diganti menjadi `"Decision Engine"`.

Alasan menggunakan FastAPI:
- mudah membuat REST API,
- validasi request otomatis melalui Pydantic,
- cocok untuk microservice kecil.

### `app.include_router(decision_router)`

Mendaftarkan router decision ke aplikasi.

Artinya endpoint dari `routers/decision_router.py` akan aktif di service ini.

Alasannya:
- `app.py` tetap ringkas.
- Endpoint dikelompokkan di folder `routers`.

### `health()`

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Fungsi ini menyediakan health check.

Kegunaan:
- memastikan service hidup,
- dipakai saat debugging,
- bisa dipakai Docker atau monitoring untuk cek status service.

Output:

```json
{
  "status": "ok"
}
```

## `config/settings.py`

### `BASE_DIR`

```python
BASE_DIR = Path(__file__).resolve().parent
```

Menyimpan path folder `config`.

Alasannya:
- path file config tidak bergantung pada dari mana command dijalankan.
- lebih aman dibanding path relatif manual.

### `SETTINGS_PATH`

```python
SETTINGS_PATH = BASE_DIR / "settings.yaml"
```

Menentukan lokasi file `settings.yaml`.

### `settings = yaml.safe_load(file)`

Membaca isi YAML menjadi dictionary Python.

Contoh:

```yaml
default_preset: "balanced"
presets:
  balanced:
    high: 0.85
    medium: 0.70
    low: 0.55
```

akan menjadi:

```python
settings["default_preset"]
settings["presets"]["balanced"]["high"]
```

Alasan menggunakan YAML:
- threshold mudah dibaca manusia,
- bisa diubah tanpa mengubah logic Python,
- cocok untuk konfigurasi preset.

## `config/settings.yaml`

### `default_preset`

Preset default jika request tidak mengirim preset atau custom threshold.

```yaml
default_preset: "balanced"
```

Alasannya:
- sistem tetap punya perilaku default.
- user tidak wajib selalu memilih preset.

### `presets`

Berisi threshold final score.

Contoh balanced:

```yaml
balanced:
  high: 0.85
  medium: 0.70
  low: 0.55
```

Maknanya:
- `score >= 0.85`: high similarity.
- `score >= 0.70`: medium similarity.
- `score >= 0.55`: low similarity.
- `score < 0.55`: very low atau no significant similarity.

Alasannya:
- threshold dibuat bertingkat agar hasil tidak hanya hitam-putih.
- sistem bisa membedakan risiko tinggi, sedang, rendah, dan sangat rendah.

### `min_allowed_threshold` dan `max_allowed_threshold`

Membatasi custom threshold dari user.

Alasannya:
- mencegah user mengisi threshold terlalu rendah atau terlalu tinggi.
- menjaga urutan threshold tetap masuk akal.

### `round_decimals`

Menentukan jumlah angka desimal pada response.

Alasannya:
- response lebih rapi,
- frontend tidak perlu menampilkan angka desimal terlalu panjang.

## `schemas/decision_schema.py`

File ini berisi schema validasi input dan output decision engine.

### `class ThresholdConfig(BaseModel)`

Schema untuk custom threshold dari user.

Field:

```python
high: float = Field(..., ge=0.0, le=1.0)
medium: float = Field(..., ge=0.0, le=1.0)
low: float = Field(..., ge=0.0, le=1.0)
```

Makna:
- `high`: batas skor risiko tinggi.
- `medium`: batas skor risiko sedang.
- `low`: batas skor risiko rendah.

Validasi:
- semua nilai harus `0.0` sampai `1.0`.

Yang belum dicek di schema:
- urutan `low < medium < high`.

Urutan itu dicek di `validate_thresholds()` pada `decision_service.py`.

Alasannya:
- Pydantic cocok untuk validasi bentuk data dasar.
- Validasi hubungan antar-field lebih jelas dilakukan di service.

### `class DecisionRequest(BaseModel)`

Schema request utama.

Field:

```python
overall_score: float
clip_score: Optional[float]
cnn_score: Optional[float]
preset: Optional[str]
thresholds: Optional[ThresholdConfig]
```

Makna:
- `overall_score`: skor akhir dari similarity service.
- `clip_score`: skor kemiripan berdasarkan embedding CLIP.
- `cnn_score`: skor kemiripan berdasarkan embedding CNN.
- `preset`: mode threshold, misalnya `strict`, `balanced`, `sensitive`.
- `thresholds`: threshold custom dari user.

Alasan field `clip_score` dan `cnn_score` opsional:
- decision engine masih bisa bekerja hanya dengan `overall_score`.
- tetapi jika CLIP/CNN tersedia, keputusan bisa lebih kaya.

### `class DecisionDetail(BaseModel)`

Schema bagian detail keputusan.

Field:

```python
status: str
risk_level: str
requires_review: bool
reason: str
```

Makna:
- `status`: label keputusan, misalnya `high_similarity`.
- `risk_level`: level risiko yang lebih singkat, misalnya `high`.
- `requires_review`: apakah butuh review manual.
- `reason`: alasan yang dapat ditampilkan di frontend.

Alasannya:
- frontend tidak hanya menerima angka.
- user/reviewer bisa memahami mengapa keputusan dibuat.

### `class DecisionResponse(BaseModel)`

Schema response lengkap.

Field:

```python
overall_score: float
clip_score: Optional[float]
cnn_score: Optional[float]
decision: DecisionDetail
```

Alasannya:
- response tetap membawa skor yang dipakai.
- frontend bisa menampilkan skor dan keputusan secara bersamaan.

## `routers/decision_router.py`

### `router = APIRouter()`

Membuat router FastAPI.

Alasannya:
- endpoint decision dipisahkan dari `app.py`.
- struktur service menjadi lebih rapi.

### `create_decision(request: DecisionRequest)`

Endpoint:

```python
@router.post("/decision", response_model=DecisionResponse, dependencies=[Depends(require_internal_api_key)])
async def create_decision(request: DecisionRequest):
```

Fungsi ini menerima request dari service internal, biasanya upload service.

Input:
- `DecisionRequest`

Output:
- `DecisionResponse`

Alur fungsi:
1. FastAPI memvalidasi request memakai `DecisionRequest`.
2. `require_internal_api_key` memastikan request membawa API key internal.
3. Fungsi mencatat log skor yang diterima.
4. Fungsi memanggil `build_decision()`.
5. Hasil decision dikembalikan ke caller.
6. Jika threshold tidak valid, fungsi mengembalikan HTTP 400.

Alasannya:
- endpoint decision tidak boleh dipanggil sembarang client tanpa internal API key.
- validasi threshold error harus dikembalikan sebagai 400 karena masalah berasal dari input request.

### Error Handling `except ValueError`

```python
except ValueError as e:
    logger.warning(...)
    raise HTTPException(status_code=400, detail=str(e))
```

Menangkap error dari:
- preset tidak dikenal,
- threshold tidak valid,
- urutan threshold salah.

Alasannya:
- error validasi tidak boleh menjadi 500.
- client perlu tahu bahwa request-nya yang harus diperbaiki.

## `services/decision_service.py`

File ini adalah inti decision engine.

### `normalize_thresholds(thresholds)`

Fungsi:
- mengubah threshold menjadi dictionary Python biasa.

Kenapa dibutuhkan:
- threshold bisa berasal dari Pydantic model (`ThresholdConfig`) atau dari dictionary YAML.
- function ini menyamakan bentuk keduanya.

Input:
- Pydantic object atau dictionary.

Output:

```python
{
    "high": float,
    "medium": float,
    "low": float
}
```

Alur:
1. Jika object memiliki `model_dump`, berarti kemungkinan Pydantic model.
2. Object diubah menjadi dictionary.
3. Nilai `high`, `medium`, dan `low` dikonversi ke float.

Alasannya:
- logic berikutnya tidak perlu peduli sumber threshold.
- semua threshold diproses dengan format yang sama.

### `validate_thresholds(thresholds)`

Fungsi:
- memastikan threshold berada dalam batas aman dan urutannya benar.

Aturan:

```text
min_allowed <= low < medium < high <= max_allowed
```

Contoh valid:

```text
low = 0.55
medium = 0.70
high = 0.85
```

Contoh tidak valid:

```text
low = 0.80
medium = 0.70
high = 0.85
```

karena `low` lebih besar dari `medium`.

Alasannya:
- threshold harus membentuk rentang risiko yang logis.
- tanpa validasi ini, status keputusan bisa menjadi salah atau membingungkan.

Output:
- threshold yang sama jika valid.

Error:
- `ValueError` jika threshold tidak valid.

### `get_thresholds(preset=None, custom_thresholds=None)`

Fungsi:
- memilih threshold yang akan dipakai untuk decision.

Prioritas:
1. Jika `preset` dikirim, gunakan preset.
2. Jika `preset` tidak dikirim dan `custom_thresholds` dikirim, gunakan custom.
3. Jika keduanya tidak dikirim, gunakan `default_preset`.

Output:

```python
thresholds, threshold_source
```

Contoh:

```python
({"high": 0.85, "medium": 0.70, "low": 0.55}, "balanced")
```

Kenapa preset diprioritaskan:
- user cukup memilih salah satu mode.
- jika preset dipilih, sistem menganggap preset sebagai sumber kebenaran.

Catatan:
- Jika ingin custom selalu mengalahkan preset, logic prioritas ini bisa diubah.
- Saat ini desainnya: pilih salah satu, preset lebih utama jika dua-duanya dikirim.

### `round_optional_score(score, round_decimals)`

Fungsi:
- membulatkan score jika score tersedia.

Input:
- `score`, bisa `None`.
- `round_decimals`, jumlah angka desimal.

Output:
- `None` jika input `None`.
- angka float yang sudah dibulatkan jika input tersedia.

Alasannya:
- `clip_score` dan `cnn_score` opsional.
- fungsi ini mencegah error ketika score tidak dikirim.

### `build_response(score, clip_score, cnn_score, status, risk_level, requires_review, reason)`

Fungsi:
- membuat format response decision yang konsisten.

Output:

```python
{
    "overall_score": score,
    "clip_score": clip_score,
    "cnn_score": cnn_score,
    "decision": {
        "status": status,
        "risk_level": risk_level,
        "requires_review": requires_review,
        "reason": reason
    }
}
```

Alasannya:
- semua cabang keputusan mengembalikan struktur yang sama.
- menghindari duplikasi dictionary response di banyak tempat.
- frontend lebih mudah membaca response.

### `build_decision(overall_score, clip_score=None, cnn_score=None, preset=None, custom_thresholds=None)`

Fungsi utama decision engine.

Input:
- `overall_score`: skor akhir dari similarity service.
- `clip_score`: skor CLIP kandidat terbaik.
- `cnn_score`: skor CNN kandidat terbaik.
- `preset`: mode threshold.
- `custom_thresholds`: threshold manual dari user.

Output:
- dictionary sesuai `DecisionResponse`.

Alur lengkap:

1. Ambil threshold dengan `get_thresholds()`.
2. Bulatkan `overall_score`, `clip_score`, dan `cnn_score`.
3. Cek apakah `overall_score >= high`.
4. Jika iya, return `high_similarity`.
5. Cek apakah `overall_score >= medium`.
6. Jika iya, return `medium_similarity`.
7. Cek apakah `overall_score >= low`.
8. Jika iya, return `low_similarity`.
9. Jika semua tidak terpenuhi, return `no_significant_similarity`.

Urutan ini penting.

Kenapa high dicek dulu:
- risiko paling tinggi harus diprioritaskan.
- jika sudah high, tidak perlu cek medium/low.

`clip_score` dan `cnn_score` tetap dikembalikan pada response sebagai informasi
analisis, tetapi tidak mengubah kategori keputusan. Dengan demikian, preset dan
custom threshold mempunyai perilaku yang konsisten dan mudah diprediksi.

## Cabang Keputusan Pada `build_decision()`

### 1. `high_similarity`

Kondisi pertama:

```python
score >= high_threshold
```

Makna:
- skor akhir sangat tinggi.
- kandidat dianggap sangat mirip.

Response:
- `risk_level`: `high`
- `requires_review`: `True`

Di upload service, status ini biasanya menjadi `blocked`.

### 2. `medium_similarity`

Kondisi:

```python
score >= medium_threshold
```

Makna:
- kemiripan cukup tinggi,
- belum tentu plagiarisme,
- perlu review manual.

Response:
- `risk_level`: `medium`
- `requires_review`: `True`

### 3. `low_similarity`

Kondisi:

```python
score >= low_threshold
```

Makna:
- ada kemiripan rendah,
- tidak perlu review manual.

Response:
- `risk_level`: `low`
- `requires_review`: `False`

Di upload service, status ini boleh lanjut registrasi.

### 4. `no_significant_similarity`

Kondisi:

```python
score < low_threshold
```

Makna:
- kemiripan tidak signifikan.

Response:
- `risk_level`: `very_low`
- `requires_review`: `False`

## `utils/internal_auth.py`

File ini melindungi service internal agar tidak bebas dipanggil tanpa API key.

### `_load_env_file(path: Path)`

Fungsi:
- membaca file `.env`,
- memasukkan key/value ke `os.environ`,
- tidak menimpa environment variable yang sudah ada.

Alasannya:
- service bisa dijalankan lokal tanpa dependency tambahan seperti `python-dotenv`.
- env dari Docker tetap diprioritaskan.

### `get_internal_api_key()`

Fungsi:
- mengambil nilai `INTERNAL_API_KEY` dari environment.

Output:
- string API key,
- atau string kosong jika belum diset.

### `internal_auth_headers()`

Fungsi:
- membuat header internal auth.

Output:

```python
{"X-Internal-API-Key": api_key}
```

Jika API key tidak ada, return `{}`.

Kegunaan:
- dipakai jika service ini perlu memanggil service internal lain.

### `require_internal_api_key(...)`

Fungsi:
- dependency FastAPI untuk mewajibkan header `X-Internal-API-Key`.

Alur:
1. Ambil expected key dari environment.
2. Jika key belum dikonfigurasi, return HTTP 500.
3. Jika header request tidak sama, return HTTP 401.
4. Jika benar, request boleh lanjut.

Alasannya:
- hanya API Gateway atau service internal yang mengetahui key boleh memanggil endpoint ini.
- mencegah frontend atau client luar memanggil decision engine langsung.

## `utils/logger.py`

### `logging.basicConfig(...)`

Mengatur format log default.

Format:

```text
timestamp | level | decision-engine | message
```

Alasannya:
- log dari setiap service mudah dibedakan.
- membantu debugging alur request antar-service.

### `logger = logging.getLogger(__name__)`

Membuat object logger yang bisa diimport di file lain.

Contoh penggunaan:

```python
logger.info("Decision request received")
logger.warning("Invalid decision request")
```

## Contoh Request

```json
{
  "overall_score": 0.742,
  "clip_score": 0.81,
  "cnn_score": 0.69,
  "preset": "balanced"
}
```

## Contoh Response

```json
{
  "overall_score": 0.742,
  "clip_score": 0.81,
  "cnn_score": 0.69,
  "decision": {
    "status": "medium_similarity",
    "risk_level": "medium",
    "requires_review": true,
    "reason": "Kandidat dengan skor tertinggi melebihi threshold medium 0.7 menggunakan mode balanced"
  }
}
```

## Catatan Untuk Laporan

Bagian paling penting untuk dijelaskan dalam laporan:

1. Decision engine memisahkan kebijakan keputusan dari similarity calculation.
2. Threshold disimpan di config agar bisa disesuaikan dari hasil evaluasi.
3. `overall_score` menjadi satu-satunya dasar kategori keputusan.
4. `clip_score` dan `cnn_score` tetap disertakan sebagai informasi analisis.
5. Preset dan custom threshold memakai aturan kategori yang sama.

## Catatan Perbaikan Kecil

Ada satu hal kecil yang bisa dirapikan nanti:

```python
app = FastAPI(title="Upload Service")
```

Sebaiknya diganti menjadi:

```python
app = FastAPI(title="Decision Engine")
```

Ini tidak mengubah logic, hanya memperbaiki nama di Swagger/OpenAPI.
