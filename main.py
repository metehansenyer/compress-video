import os
import sys
import shutil
import subprocess
from pathlib import Path

# =============================
#  CONFIG
# =============================
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
SUPPORTED_FORMATS = [".mp4", ".mov"]


# =============================
#  HELPER FUNCTIONS
# =============================

def check_dependencies():
    """FFmpeg kurulu mu kontrol et."""
    if shutil.which("ffmpeg") is None:
        print("❌ FFmpeg bulunamadı. Lütfen kurun ve PATH'e ekleyin.")
        sys.exit(1)
    else:
        print("✅ FFmpeg bulundu.")


def get_video_files():
    """Input klasöründeki tüm mp4/mov dosyalarını bulur."""
    video_files = []
    for ext in SUPPORTED_FORMATS:
        video_files.extend(INPUT_DIR.rglob(f"*{ext}"))
    return video_files


def ensure_output_path(input_path: Path):
    """Input dosyasına göre output klasör yolunu hazırla."""
    relative = input_path.relative_to(INPUT_DIR)
    output_path = OUTPUT_DIR / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def optimize_video(input_path: Path, output_path: Path):
    """Videoyu ffmpeg ile H.265 kullanarak optimize et."""
    print(f"⚙️ İşleniyor: {input_path} → {output_path}")

    # Orijinal dosya boyutu
    before_size = input_path.stat().st_size

    # FFmpeg komutu (H.265 libx265, CRF kalite ayarı)
    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-c:v", "libx265",
        "-tag:v", "hvc1",
        "-preset", "faster",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "128k",
        "-y",
        str(output_path)
    ]

    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process.returncode != 0:
        print(f"❌ Hata oluştu: {input_path}\n{process.stderr}")
        return None, None

    after_size = output_path.stat().st_size

    print(f"✅ Tamamlandı: {output_path}")
    return before_size, after_size


def human_size(size_bytes):
    """Byte değerini okunabilir formatta döndür."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


# =============================
#  MAIN
# =============================
def main():
    print("🎬 H.265 Video Optimize Aracına Hoşgeldiniz")
    check_dependencies()

    video_files = get_video_files()
    if not video_files:
        print("⚠️ Hiç video bulunamadı.")
        return

    print(f"📂 {len(video_files)} adet video bulundu.\n")

    total_before, total_after = 0, 0

    for i, video in enumerate(video_files, 1):
        print(f"[{i}/{len(video_files)}] İşlem başlatılıyor: {video}")

        output_path = ensure_output_path(video)
        before, after = optimize_video(video, output_path)

        if before and after:
            total_before += before
            total_after += after

    # =============================
    #  SON RAPOR
    # =============================
    print("\n📊 İŞLEM RAPORU")
    print("-----------------------------")
    print(f"Toplam Dosya: {len(video_files)}")
    print(f"Orijinal Boyut: {human_size(total_before)}")
    print(f"Optimize Boyut: {human_size(total_after)}")

    if total_before > 0:
        ratio = (1 - (total_after / total_before)) * 100
        print(f"💾 Tasarruf: %{ratio:.2f}")


if __name__ == "__main__":
    main()
