import feedparser
import re
import cloudscraper
import config
import random
from time import mktime

def is_informative_title(title):
    if '?' in title or '!' in title:
        return False
        
    title_lower = title.lower()
    
    if re.match(r'^\d+\s+(ide|cara|fakta|tips|alasan|potret|langkah|rekomendasi|hal)\b', title_lower):
        return False

    blacklisted_phrases = [
        "jelaskan maksud", "beri penjelasan", "buka suara", 
        "angkat bicara", "hasil pertandingan", "rupiah menguat", "rupiah melemah", 
        "baca selengkapnya", "lihat selengkapnya", "cek disini", "baca juga", 
        "ini dia", "seperti ini", "kaya gini", "bikin geger", "penjelasan resmi",
        "video ungkap", "video:", "foto:", "infografis:", "ini daftar", "perbedaan",
        "babak belur"
    ]
    for phrase in blacklisted_phrases:
        if phrase in title_lower:
            return False

    blacklisted_words = [
        "simak", "intip", "begini", "ternyata", "fakta", "wow", "potret", "detik-detik",
        "berikut", "cara", "tips", "trik", "daftar", "rincian", "jadwal", "link", "unduh",
        "video", "foto", "segini", "sinopsis", "hikmah", "jejak", "profil", "rekomendasi",
        "review", "alasan", "makna", "arti", "deretan", "sejarah", "mengenal", "mitos",
        "kumpulan", "pesona", "gaya", "sosok", "bocoran", "terkuak", "menengok",
        "popularitas", "soroti", "skincare", "penjualan", "promo", "tanggapi",
        "melirik", "menikmati", "heboh", "viral", "geger", "gempar",
        "momen", "vs", "klasemen", "skor", "prediksi", "ihsg", "saham",
        "tantangan", "klarifikasi", "strategi", "penjelasan", "jelaskan", "ungkap",
        "ide", "hampers", "resep", "menu", "inspirasi", "katalog", "diskon", 
        "berkesan", "personal", "curhat",
        "eksplorasi", "ekspresi", "karya", "koleksi", "desainer", "busana", "pameran", "estetika",
        "sah", "tok", "genjot", "meladeni", "ambrol", "ambruk", "terciduk", "kepergok",
        "nyungsep", "nongkrong", "ngeri"
    ]
    
    for word in blacklisted_words:
        if re.search(r'\b' + word + r'\b', title_lower):
            return False

    words = title_lower.split()
    for i, word in enumerate(words):
        word_clean = re.sub(r'[^\w\s]', '', word)
        
        if word_clean in ['ini', 'itu']:
            if i > 0:
                prev_word = re.sub(r'[^\w\s]', '', words[i-1])
                allowed_time = ['hari', 'saat', 'tahun', 'bulan', 'minggu', 'pekan', 'kali', 'pagi', 'siang', 'sore', 'malam', 'waktu', 'detik']
                if prev_word not in allowed_time:
                    return False 
            else:
                return False 
                
    words_count = title.split()
    if len(words_count) < 5:
        return False
        
    return True

def clean_prefix(title):
    text = re.sub(r'\[.*?\]|【.*?】|\(.*\)', '', title)
    text = re.sub(r'^[A-Za-z\s]{2,30}\s*-\s+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def paraphrase_title(title):
    replacements = {
        r'\bkena\b': 'terkena',
        r'\bbodoh\b': 'kurang pandai',
        r'\bbikin\b': 'membuat',
        r'\bcuma\b': 'hanya',
        r'\bnumpuk\b': 'menumpuk',
        r'\bkasih\b': 'memberi'
    }
    
    for pattern, replacement in replacements.items():
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
        
    return title

def get_news_data(source):
    scraper = cloudscraper.create_scraper()
    results = []
    
    if source == "Acak (Campuran)":
        sources_to_fetch = list(config.RSS_DATABASE.keys())
    else:
        sources_to_fetch = [source]
        
    all_entries = []
    
    for src in sources_to_fetch:
        url = config.RSS_DATABASE.get(src)
        if not url: continue
        
        try:
            response = scraper.get(url, timeout=8)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    sort_time = 0
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        sort_time = mktime(entry.published_parsed)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        sort_time = mktime(entry.updated_parsed)
                        
                    all_entries.append((entry, src, sort_time))
        except Exception:
            pass
            
    all_entries.sort(key=lambda x: x[2], reverse=True)
        
    for entry, src, _ in all_entries:
        judul_asli = entry.title
        
        if is_informative_title(judul_asli):
            judul_bersih = clean_prefix(judul_asli)
            judul_bersih = paraphrase_title(judul_bersih)
            
            if judul_bersih:
                judul_bersih = judul_bersih[0].upper() + judul_bersih[1:]
                judul_bersih = judul_bersih.rstrip(".'\"")
            
            waktu_terbit = getattr(entry, 'published', getattr(entry, 'updated', 'Waktu tidak terdeteksi'))
            
            display_title = judul_asli
                    
            results.append({
                "title_display": display_title,
                "title_rtx": judul_bersih,
                "link": getattr(entry, 'link', '#'),
                "published": waktu_terbit
            })
        
        if len(results) == 25:
            break
            
    return results