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
        thresholds = normalize_thresholds(settings["presets"][default_preset])  # Ambil threshold dari preset default
        threshold_source = default_preset  # Sumber threshold default

    thresholds = validate_thresholds(thresholds)  # Validasi threshold

    return thresholds, threshold_source  # Return threshold dan sumbernyangembalikan threshold dan sumbernya


def get_score_rules(threshold_source=None):  # Mengambil rule tambahan CLIP/CNN sesuai preset aktif
    all_rules = settings.get("score_rules", {})  # Ambil rule jika tersedia
    fallback_rules = {
        "clip_high": 0.88,
        "cnn_high": 0.75,
        "final_high": 0.82,
        "possible_final": 0.65,
        "possible_clip": 0.80,
        "possible_cnn": 0.60,
    }

    if "clip_high" in all_rules:  # Kompatibilitas jika config lama masih flat
        rules = all_rules
    else:
        preset_name = threshold_source if threshold_source in all_rules else settings.get("default_preset", "balanced")
        rules = all_rules.get(preset_name, all_rules.get("balanced", fallback_rules))

    return {  # Return rule dengan fallback aman
        "clip_high": float(rules.get("clip_high", fallback_rules["clip_high"])),
        "cnn_high": float(rules.get("cnn_high", fallback_rules["cnn_high"])),
        "final_high": float(rules.get("final_high", fallback_rules["final_high"])),
        "possible_final": float(rules.get("possible_final", fallback_rules["possible_final"])),
        "possible_clip": float(rules.get("possible_clip", fallback_rules["possible_clip"])),
        "possible_cnn": float(rules.get("possible_cnn", fallback_rules["possible_cnn"])),
    }


def build_custom_score_rules(thresholds):  # Membuat rule CLIP/CNN otomatis dari custom threshold user
    low = thresholds["low"]  # Ambil threshold low custom
    medium = thresholds["medium"]  # Ambil threshold medium custom
    high = thresholds["high"]  # Ambil threshold high custom
    max_allowed = settings["max_allowed_threshold"]  # Batas maksimum threshold dari config

    return {  # Rule turunan agar custom threshold tetap konsisten
        "clip_high": min(high + 0.03, max_allowed),  # CLIP dibuat sedikit lebih ketat dari high karena sensitif pada konsep
        "cnn_high": min(medium + 0.05, max_allowed),  # CNN high dekat medium karena mewakili detail visual
        "final_high": (medium + high) / 2,  # Zona kuat di antara medium dan high
        "possible_final": (low + medium) / 2,  # Zona abu-abu di antara low dan medium
        "possible_clip": min(medium + 0.10, max_allowed),  # CLIP possible cukup tinggi agar semantic-only tidak terlalu mudah lolos
        "possible_cnn": min(low + 0.05, max_allowed),  # CNN possible sedikit di atas low untuk menangkap detail visual awal
    }


def round_optional_score(score, round_decimals):  # Membulatkan score opsional
    if score is None:  # Jika score tidak dikirim
        return None  # Biarkan kosong

    return round(float(score), round_decimals)  # Bulatkan score


def build_response(score, clip_score, cnn_score, status, risk_level, requires_review, reason):  # Helper response
    return {  # Mengembalikan format response decision
        "overall_score": score,  # Score utama
        "clip_score": clip_score,  # Score CLIP jika tersedia
        "cnn_score": cnn_score,  # Score CNN jika tersedia
        "decision": {  # Detail keputusan
            "status": status,  # Status keputusan
            "risk_level": risk_level,  # Level risiko
            "requires_review": requires_review,  # Apakah perlu review manual
            "reason": reason  # Alasan keputusan
        }  # Menutup decision
    }  # Menutup response


def build_decision(overall_score, clip_score=None, cnn_score=None, preset=None, custom_thresholds=None):  # Fungsi utama membuat keputusan
    thresholds, threshold_source = get_thresholds(  # Mengambil threshold yang akan dipakai
        preset=preset,  # Preset dari request
        custom_thresholds=custom_thresholds  # Custom threshold dari request
    )  # Menutup pemanggilan get_thresholds

    round_decimals = settings["round_decimals"]  # Mengambil jumlah digit pembulatan
    score = round(float(overall_score), round_decimals)  # Membulatkan overall_score
    clip = round_optional_score(clip_score, round_decimals)  # Membulatkan clip_score jika ada
    cnn = round_optional_score(cnn_score, round_decimals)  # Membulatkan cnn_score jika ada
    score_rules = build_custom_score_rules(thresholds) if threshold_source == "custom" else get_score_rules(threshold_source)  # Rule CLIP/CNN dari custom atau preset

    high_threshold = thresholds["high"]  # Mengambil threshold high
    medium_threshold = thresholds["medium"]  # Mengambil threshold medium
    low_threshold = thresholds["low"]  # Mengambil threshold low

    if score >= high_threshold:  # Mengecek apakah skor masuk kategori high
        return build_response(  # Mengembalikan keputusan high similarity
            score,  # Overall score
            clip,  # CLIP score
            cnn,  # CNN score
            "high_similarity",  # Status high similarity
            "high",  # Risiko tinggi
            True,  # Perlu review manual
            f"Kandidat dengan skor tertinggi melebihi threshold high {high_threshold} menggunakan mode {threshold_source}"  # Alasan
        )  # Menutup build_response

    if clip is not None and cnn is not None:  # Jika score detail tersedia
        if clip >= score_rules["clip_high"] and cnn >= score_rules["cnn_high"]:  # CLIP dan CNN sama-sama kuat
            return build_response(  # Return high similarity berbasis dua sinyal
                score,  # Overall score
                clip,  # CLIP score
                cnn,  # CNN score
                "high_similarity",  # Status high similarity
                "high",  # Risiko tinggi
                True,  # Perlu review manual
                f"CLIP score {clip} dan CNN score {cnn} melewati batas kuat ({score_rules['clip_high']}/{score_rules['cnn_high']})"  # Alasan
            )  # Menutup build_response

        if score >= score_rules["final_high"] and cnn >= score_rules["cnn_high"]:  # Final kuat dan detail visual cukup
            return build_response(  # Return high similarity berbasis final + CNN
                score,  # Overall score
                clip,  # CLIP score
                cnn,  # CNN score
                "high_similarity",  # Status high similarity
                "high",  # Risiko tinggi
                True,  # Perlu review manual
                f"Overall score {score} dan CNN score {cnn} melewati batas kuat ({score_rules['final_high']}/{score_rules['cnn_high']})"  # Alasan
            )  # Menutup build_response

    if score >= medium_threshold:  # Mengecek apakah skor masuk kategori medium
        return build_response(  # Mengembalikan keputusan medium similarity
            score,  # Overall score
            clip,  # CLIP score
            cnn,  # CNN score
            "medium_similarity",  # Status medium similarity
            "medium",  # Risiko sedang
            True,  # Perlu review manual
            f"Kandidat dengan skor tertinggi melebihi threshold medium {medium_threshold} menggunakan mode {threshold_source}"  # Alasan
        )  # Menutup build_response

    if clip is not None and cnn is not None:  # Jika score detail tersedia
        if score >= score_rules["possible_final"] or clip >= score_rules["possible_clip"] or cnn >= score_rules["possible_cnn"]:  # Sinyal sedang
            return build_response(  # Return possible plagiarism
                score,  # Overall score
                clip,  # CLIP score
                cnn,  # CNN score
                "possible_plagiarism",  # Status possible plagiarism
                "medium",  # Risiko sedang
                True,  # Perlu review manual
                f"Salah satu sinyal melewati batas possible: overall>={score_rules['possible_final']}, CLIP>={score_rules['possible_clip']}, atau CNN>={score_rules['possible_cnn']}"  # Alasan
            )  # Menutup build_response

    if score >= low_threshold:  # Mengecek apakah skor masuk kategori low
        return build_response(  # Mengembalikan keputusan low similarity
            score,  # Overall score
            clip,  # CLIP score
            cnn,  # CNN score
            "low_similarity",  # Status low similarity
            "low",  # Risiko rendah
            False,  # Tidak wajib review manual
            f"Kandidat dengan skor tertinggi melebihi threshold low {low_threshold} menggunakan mode {threshold_source}"  # Alasan
        )  # Menutup build_response

    return build_response(  # Mengembalikan keputusan jika tidak signifikan
        score,  # Overall score
        clip,  # CLIP score
        cnn,  # CNN score
        "no_significant_similarity",  # Status tidak signifikan
        "very_low",  # Risiko sangat rendah
        False,  # Tidak perlu review manual
        f"Kandidat dengan skor tertinggi berada di bawah threshold low {low_threshold} menggunakan mode {threshold_source}"  # Alasan
    )  # Menutup build_response



