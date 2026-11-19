# srt-fit-id

CLI dan library lokal untuk merapikan subtitle SRT, termasuk subtitle hasil Whisper atau tool transkripsi AI. Teks cue dibungkus di batas kata sesuai batas panjang baris, sementara nomor cue dan timestamp dipertahankan apa adanya. Bila satu cue tidak muat dalam batas baris yang diminta, tool berhenti dengan error alih-alih mengubah timing atau diam-diam membuat banyak baris.

## CLI

```sh
cat video.srt | srt-fit-id --max-chars 42 --max-lines 2 > video-rapi.srt
```

Default-nya maksimum 42 karakter per baris dan dua baris per cue. Cue yang terlalu panjang menghasilkan error berisi nomor cue, bukan menampilkan ulang teks subtitle.

## Sebagai library

```python
from srt_fit_id import reflow_srt

hasil = reflow_srt(teks_srt, max_chars=42, max_lines=2)
```

Python 3.9+. Instalasi: `python -m pip install .`

## Batasan dan privasi

Tool menangani SRT bernomor dengan timestamp standar dan teks biasa; ia tidak membuat caption, mengubah timing, atau menilai sinkronisasi audio. Perhitungan panjang memakai jumlah karakter Python, bukan lebar visual font. Teks diproses lokal tanpa API, penyimpanan, atau telemetri.

Tes: `python -m unittest discover -s tests -v`

## Lisensi

MIT. Lihat [LICENSE](LICENSE).
