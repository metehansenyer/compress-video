# Video Sıkıştırma

Python tabanlı video sıkıştırma uygulaması. FFmpeg kullanarak H.265 codec ile videolarınızı optimize eder.

## Kurulum

### Gereksinimler
- Python 3.12+
- FFmpeg

### FFmpeg Kurulumu

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt install ffmpeg
```

#### Windows
```bash
winget install --id=Gyan.FFmpeg  -e
```

### Kodları İndirme
```bash
git clone https://github.com/metehansenyer/compress-video.git
cd compress-video
```

## Kullanım

1. Videolarınızı `input/` klasörüne koyun
2. Çalıştırın: `python main.py`
3. Sıkıştırılmış videolar `output/` klasöründe oluşur

## Yapılandırma

`main.py` dosyasının üst kısmındaki ayarları düzenleyin:

```python
PRESET = "medium"  # slow, medium, fast, faster 
CRF = "28"        # 24-28 arası (24: kaliteli, 28: sıkıştırılmış)
```

## Test Sonuçları

**Test Cihazı**: MacBook M1 Air 8GB

### 720p Video (337.95 MB)
| Preset | Süre | Sonuç | Tasarruf |
|--------|------|--------|----------|
| veryslow | 2sa 30dk | 108.13 MB | 68% |
| slow | 22 dk | 108.34 MB | 68% |
| medium | 8 dk | 103.28 MB | 69% |
| faster | 5 dk | 99.43 MB | 71% |

### 1080p Video (636.5 MB)
| Preset | Süre | Sonuç | Tasarruf |
|--------|------|--------|----------|
| medium | 15 dk | 131 MB | 79% |

### 12 Video Toplamı (4480 MB)
- **Süre**: 1sa 38dk
- **Sonuç**: 1380 MB
- **Tasarruf**: 69%