from config.settings import settings  # Mengambil konfigurasi threshold dari settings.yaml


def normalize_thresholds(thresholds):  # Fungsi untuk mengubah threshold menjadi dictionary biasa
    if hasattr(thresholds, "model_dump"):  # Mengecek apakah thresholds adalah object Pydantic v2
        thresholds = thresholds.model_dump()  # Mengubah Pydantic model menjadi dictionary

    return {  # Mengembalikan threshold dalam format dictionary
        "high": float(thresholds["high"]),  # Mengubah high threshold menjadi float
        "medium": float(thresholds["medium"]),  # Mengubah medium threshold menjadi float
        "low": float(thresholds["low"])  # Mengubah low threshold menjadi float
    }  # Menutup dictionary


def validate_thresholds(thresholds):  # Fungsi validasi threshold
    low = thresholds["low"]  # Mengambil threshold low
    medium = thresholds["medium"]  # Mengambil threshold medium
    high = thresholds["high"]  # Mengambil threshold high

    min_allowed = settings["min_allowed_threshold"]  # Mengambil batas minimal threshold dari config
    max_allowed = settings["max_allowed_threshold"]  # Mengambil batas maksimal threshold dari config

    if not (min_allowed <= low < medium < high <= max_allowed):  # Mengecek urutan dan batas threshold
        raise ValueError(  # Mengembalikan error jika threshold tidak valid
            f"Threshold tidak valid. Aturan: {min_allowed} <= low < medium < high <= {max_allowed}"  # Pesan error
        )  # Menutup raise error

    return thresholds  # Mengembalikan threshold jika valid


def get_thresholds(preset=None, custom_thresholds=None):  # Fungsi memilih threshold yang dipakai
    if preset is not None:  # Jika user memilih preset, preset diprioritaskan
        presets = settings["presets"]  # Ambil daftar preset

        if preset not in presets:  # Validasi nama preset
            raise ValueError(f"Preset threshold tidak dikenal: {preset}")  # Error jika preset salah

        thresholds = normalize_thresholds(presets[preset])  # Ambil threshold dari preset
        threshold_source = preset  # Simpan sumber threshold

    elif custom_thresholds is not None:  # Jika tidak ada preset, baru pakai custom threshold
        thresholds = normalize_thresholds(custom_thresholds)  # Ambil custom threshold
        threshold_source = "custom"  # Sumber threshold custom

    else:  # Jika tidak ada preset dan custom
        default_preset = settings["default_preset"]  # Ambil preset default
        thresholds = normalize_thresholds(settings["default_thresholds"])  # Ambil threshold default
        threshold_source = default_preset  # Sumber threshold default

    thresholds = validate_thresholds(thresholds)  # Validasi threshold

    return thresholds, threshold_source  # Return threshold dan sumbernyangembalikan threshold dan sumbernya


def build_decision(overall_score, preset=None, custom_thresholds=None):  # Fungsi utama membuat keputusan
    thresholds, threshold_source = get_thresholds(  # Mengambil threshold yang akan dipakai
        preset=preset,  # Preset dari request
        custom_thresholds=custom_thresholds  # Custom threshold dari request
    )  # Menutup pemanggilan get_thresholds

    round_decimals = settings["round_decimals"]  # Mengambil jumlah digit pembulatan
    score = round(float(overall_score), round_decimals)  # Membulatkan overall_score

    high_threshold = thresholds["high"]  # Mengambil threshold high
    medium_threshold = thresholds["medium"]  # Mengambil threshold medium
    low_threshold = thresholds["low"]  # Mengambil threshold low

    if score >= high_threshold:  # Mengecek apakah skor masuk kategori high
        return {  # Mengembalikan keputusan high similarity
            "overall_score": score,  # Score utama
            "decision": {  # Detail keputusan
                "status": "high_similarity",  # Status high similarity
                "risk_level": "high",  # Risiko tinggi
                "requires_review": True,  # Perlu review manual
                "reason": f"Kandidat dengan skor tertinggi melebihi threshold high {high_threshold} menggunakan mode {threshold_source}"  # Alasan keputusan
            }  # Menutup decision
        }  # Menutup response

    if score >= medium_threshold:  # Mengecek apakah skor masuk kategori medium
        return {  # Mengembalikan keputusan medium similarity
            "overall_score": score,  # Score utama
            "decision": {  # Detail keputusan
                "status": "medium_similarity",  # Status medium similarity
                "risk_level": "medium",  # Risiko sedang
                "requires_review": True,  # Perlu review manual
                "reason": f"Kandidat dengan skor tertinggi melebihi threshold medium {medium_threshold} menggunakan mode {threshold_source}"  # Alasan keputusan
            }  # Menutup decision
        }  # Menutup response

    if score >= low_threshold:  # Mengecek apakah skor masuk kategori low
        return {  # Mengembalikan keputusan low similarity
            "overall_score": score,  # Score utama
            "decision": {  # Detail keputusan
                "status": "low_similarity",  # Status low similarity
                "risk_level": "low",  # Risiko rendah
                "requires_review": False,  # Tidak wajib review manual
                "reason": f"Kandidat dengan skor tertinggi melebihi threshold low {low_threshold} menggunakan mode {threshold_source}"  # Alasan keputusan
            }  # Menutup decision
        }  # Menutup response

    return {  # Mengembalikan keputusan jika tidak signifikan
        "overall_score": score,  # Score utama
        "decision": {  # Detail keputusan
            "status": "no_significant_similarity",  # Status tidak signifikan
            "risk_level": "very_low",  # Risiko sangat rendah
            "requires_review": False,  # Tidak perlu review manual
            "reason": f"Kandidat dengan skor tertinggi berada di bawah threshold low {low_threshold} menggunakan mode {threshold_source}"  # Alasan keputusan
        }  # Menutup decision
    }  # Menutup response