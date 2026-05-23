"""
leaderboard.py — Top-5 High Score Leaderboard

Menyimpan dan memuat 5 skor tertinggi beserta nama pemain (3 huruf)
dari file `scores.json`.
"""
import json
import os
from typing import TypedDict

SCORES_FILE = "scores.json"
MAX_ENTRIES = 5


class ScoreEntry(TypedDict):
    name: str
    score: int


def load_leaderboard() -> list[ScoreEntry]:
    """
    Muat leaderboard dari file. Kembalikan list kosong jika gagal.
    """
    try:
        if not os.path.exists(SCORES_FILE):
            return []
        with open(SCORES_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        valid: list[ScoreEntry] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if "name" not in entry or "score" not in entry:
                continue
            try:
                valid.append({
                    "name":  str(entry["name"])[:3].upper(),
                    "score": int(entry["score"]),
                })
            except (ValueError, TypeError):
                pass
        return valid[:MAX_ENTRIES]
    except Exception as e:
        print(f"Warning: Gagal memuat leaderboard: {e}")
        return []


def save_leaderboard(entries: list[ScoreEntry]) -> bool:
    """
    Simpan leaderboard ke file. Kembalikan True jika berhasil.
    """
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(entries[:MAX_ENTRIES], f, indent=2)
        return True
    except Exception as e:
        print(f"Error: Gagal menyimpan leaderboard: {e}")
        return False


def qualifies_for_leaderboard(score: int, entries: list[ScoreEntry]) -> bool:
    """
    Cek apakah score masuk ke Top-5. Score 0 tidak dihitung.
    """
    try:
        score = int(score)
        if score <= 0:
            return False
        if len(entries) < MAX_ENTRIES:
            return True
        return score > min(e["score"] for e in entries)
    except Exception:
        return False


def insert_score(name: str, score: int, entries: list[ScoreEntry]) -> list[ScoreEntry]:
    """
    Sisipkan skor baru, urutkan descending, pangkas ke MAX_ENTRIES.
    Nama otomatis dipadding/dipotong ke 3 karakter.
    """
    try:
        clean_name  = str(name).strip().upper()[:3].ljust(3, "_")
        clean_score = int(score)
        updated     = list(entries) + [{"name": clean_name, "score": clean_score}]
        updated.sort(key=lambda e: e.get("score", 0), reverse=True)
        return updated[:MAX_ENTRIES]
    except Exception as e:
        print(f"Error inserting score: {e}")
        return list(entries)
