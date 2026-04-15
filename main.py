import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

# =============================
#  CONFIG
# =============================
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
SUPPORTED_FORMATS = [".mp4", ".mov", ".mkv", ".MOV"]
PRESET = "medium"  # slow, medium, fast dışına çıkmamaya çalışın. slow'da ortlama bir bölüm 20dk, fast'te ortalama bir bölüm 6dk sürüyor.
CRF = "28" # 24-28 arasında kalmasına dikkat edin. 24 en kaliteli 28 en kalitesiz izlenebilir durumda ama.

# =============================
#  HARDWARE DETECTION
# =============================
USE_GPU = False  # None: auto-detect, True: force GPU, False: force CPU 

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

def check_gpu_support():
    """NVENC desteğini kontrol et."""
    global USE_GPU

    if USE_GPU is not None:
        return USE_GPU

    try:
        # FFmpeg ile NVENC desteğini kontrol et
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-encoders"
        ], capture_output=True, text=True, timeout=10)

        # HEVC kontrolü
        if "hevc_nvenc" in result.stdout:
            USE_GPU = True
        else:
            USE_GPU = False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        print("⚠️ GPU kontrolü yapılamadı. CPU kodlaması kullanılacak.")
        USE_GPU = False

    return USE_GPU

def get_video_files():
    """Input klasöründeki tüm mp4/mov/mkv dosyalarını bulur."""
    video_files = []
    for ext in SUPPORTED_FORMATS:
        video_files.extend(INPUT_DIR.rglob(f"*{ext}"))
    return video_files

def ensure_output_path(input_path: Path):
    """Input dosyasına göre output klasör yolunu hazırla."""
    relative = input_path.relative_to(INPUT_DIR)
    output_path = OUTPUT_DIR / relative
    output_path = output_path.with_suffix('.mp4')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path

def optimize_video(input_path: Path, output_path: Path):
    """Videoyu ffmpeg ile optimize et."""
    start = time.time()
    print(f"⚙️ İşleniyor: {input_path} → {output_path}")

    before_size = input_path.stat().st_size

    use_gpu = check_gpu_support()

    # HEVC/H.265 işlemi
    if use_gpu:
        # GPU ile HEVC NVENC
        command = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "hevc_nvenc",
            "-tag:v", "hvc1",
            "-preset", PRESET,
            "-cq", CRF,
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path)
        ]
        encoder_type = "GPU (NVENC HEVC)"
    else:
        # CPU ile H.265
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
        encoder_type = "CPU (H.265)"

    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process.returncode != 0:
        print(f"❌ Hata oluştu: {input_path}\n{process.stderr}")
        return None

    after_size = output_path.stat().st_size
    elapsed = time.time() - start

    print(f"✅ Tamamlandı: {output_path} ({elapsed:.1f} sn) - {encoder_type}")
    return before_size, after_size, elapsed

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
    print(f"🎬 Video Optimize Aracına Hoşgeldiniz (preset: {PRESET}, crf: {CRF})")
    check_dependencies()

    # GPU desteğini kontrol et
    use_gpu = check_gpu_support()
    encoder_info = "GPU (NVENC HEVC)" if use_gpu else "CPU (H.265)"
    print(f"🔧 Kullanılacak encoder: {encoder_info}\n")

    video_files = get_video_files()
    if not video_files:
        print("⚠️ Hiç video bulunamadı.")
        return

    print(f"📂 {len(video_files)} adet video bulundu.\n")

    total_before, total_after, total_time = 0, 0, 0
    results = []

    start_all = time.time()

    for i, video in enumerate(video_files, 1):
        print(f"📺 [{i}/{len(video_files)}] İşleniyor: {video.name}")
        try:
            result = optimize_video(video, ensure_output_path(video))
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
