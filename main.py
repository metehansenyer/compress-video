import os
import sys
import shutil
import subprocess
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# =============================
#  CONFIG
# =============================
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
SUPPORTED_FORMATS = [".mp4", ".mov"]
PRESET = "medium"  # slow, medium, fast dışına çıkmamaya çalışın. slow'da ortlama bir bölüm 20dk, fast'te ortalama bir bölüm 6dk sürüyor.
CRF = "28" # 24-28 arasında kalmasına dikkat edin. 24 en kaliteli 28 en kalitesiz izlenebilir durumda ama. 

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
    start = time.time()
    print(f"⚙️ İşleniyor: {input_path} → {output_path}")

    before_size = input_path.stat().st_size

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-c:v", "libx265",
        "-tag:v", "hvc1",
        "-preset", PRESET,
        "-crf", CRF,
        "-c:a", "aac",
        "-b:a", "128k",
        "-y",
        str(output_path)
    ]

    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process.returncode != 0:
        print(f"❌ Hata oluştu: {input_path}\n{process.stderr}")
        return None

    after_size = output_path.stat().st_size
    elapsed = time.time() - start

    print(f"✅ Tamamlandı: {output_path} ({elapsed:.1f} sn)")
    return before_size, after_size, elapsed

def human_size(size_bytes):
    """Byte değerini okunabilir formatta döndür."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_optimal_workers(video_count, user_workers=None):
    """İdeal worker sayısını belirle."""
    cpu_count = os.cpu_count() or 4

    if user_workers:  # kullanıcı manuel belirlediyse onu kullan
        return user_workers

    # Eğer video sayısı azsa ona göre ayarla
    if video_count <= 2:
        return 1

    # M1 gibi cihazlarda libx265 CPU-bound olduğu için 2-3 worker genelde en verimli
    if cpu_count <= 8:
        return min(3, video_count)

    # Daha güçlü CPU’larda daha fazla worker kullanılabilir
    return min(cpu_count // 2, video_count)

# =============================
#  MAIN
# =============================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, help="Paralel iş sayısı (varsayılan: otomatik seçim)")
    args = parser.parse_args()

    print(f"🎬 Video Optimize Aracına Hoşgeldiniz (preset: {PRESET}, crf: {CRF})")
    check_dependencies()

    video_files = get_video_files()
    if not video_files:
        print("⚠️ Hiç video bulunamadı.")
        return

    print(f"📂 {len(video_files)} adet video bulundu.\n")

    total_before, total_after, total_time = 0, 0, 0
    results = []

    start_all = time.time()

    max_workers = get_optimal_workers(len(video_files), args.workers)
    print(f"⚡ Kullanılan worker sayısı: {max_workers}\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(optimize_video, video, ensure_output_path(video)): video for video in video_files}

        for i, future in enumerate(as_completed(futures), 1):
            video = futures[future]
            try:
                result = future.result()
                if result:
                    before, after, elapsed = result
                    total_before += before
                    total_after += after
                    total_time += elapsed
                    results.append((video, before, after, elapsed))
            except Exception as e:
                print(f"❌ {video} işlenirken hata: {e}")

    end_all = time.time()
    elapsed_all = end_all - start_all

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

    print(f"⏱️ Toplam Süre: {elapsed_all:.1f} sn")
    if results:
        print(f"⏱️ Ortalama Video Süresi: {total_time/len(results):.1f} sn")

if __name__ == "__main__":
    main()
