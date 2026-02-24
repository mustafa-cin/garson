#!/usr/bin/env python3
# asci.py - Mutfakta yemek hazırlayan aşçı

"""
AŞÇI'NIN ROLÜ:
1. Garson'a kayıt ol
2. Mutfak sırasından sipariş al
3. Yemeği hazırla
4. Garson'a bildir
5. Tekrarla
"""

import requests
import time
import random
import os
from datetime import datetime
from shared.menu import MENU

# ============================================================================
# KONFİGÜRASYON
# ============================================================================

GARSON_URL = os.getenv('GARSON_URL', "http://garson:5000")
ASCI_ISIM = os.getenv('ASCI_ISIM', f'Aşçı-{random.randint(1,99)}')
UZMANLIK = os.getenv('UZMANLIK', '').split(',') if os.getenv('UZMANLIK') else []
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '5'))
HAZIRLAMA_HIZI = float(os.getenv('HAZIRLAMA_HIZI', '1.0'))

asci_id = None
istatistikler = {
    'toplam_siparis': 0,
    'basarili': 0,
    'basarisiz': 0,
    'toplam_sure': 0.0
}

# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def garson_kayit_ol():
    """Garson'a kayıt ol"""
    global asci_id
    
    print(f"\n{'='*60}")
    print(f"📝 GARSON'A KAYIT OLUNUYOR...")
    print(f"{'='*60}")
    print(f"👤 İsim: {ASCI_ISIM}")
    print(f"🎯 Uzmanlık: {', '.join(UZMANLIK) if UZMANLIK else 'Genel (her şey)'}")
    
    payload = {
        'isim': ASCI_ISIM,
        'uzmanlik': UZMANLIK
    }
    
    try:
        response = requests.post(
            f"{GARSON_URL}/api/v1/asci/kayit",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            asci_id = data['asci_id']
            
            print(f"\n✅ KAYIT BAŞARILI!")
            print(f"🆔 Aşçı ID: {asci_id}")
            print(f"💬 Garson: {data['mesaj']}")
            print(f"{'='*60}\n")
            
            return asci_id
        else:
            print(f"\n❌ KAYIT BAŞARISIZ! Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"\n❌ Kayıt hatası: {e}")
        return None

def siparis_al():
    """Mutfak sırasından sipariş al"""
    try:
        response = requests.post(
            f"{GARSON_URL}/api/v1/asci/siparis-al",
            json={'asci_id': asci_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'siparis' in data:
                return data['siparis']
        return None
    except:
        return None

def yemek_hazirla(siparis):
    """Yemeği hazırla (simülasyon)"""
    
    yemek = siparis['yemek']
    adet = siparis['adet']
    siparis_id = siparis['id']
    
    print(f"\n{'='*60}")
    print(f"👨‍🍳 YEMEK HAZIRLANIYOR")
    print(f"{'='*60}")
    print(f"📋 Sipariş: {siparis_id}")
    print(f"🍕 Yemek: {yemek} x {adet}")
    if siparis.get('not'):
        print(f"📝 Not: {siparis['not']}")
    print(f"⏰ Başlangıç: {datetime.now().strftime('%H:%M:%S')}")
    
    # Hazırlama süresi hesapla
    base_sure = 20
    for item in MENU:
        if item['yemek'] == yemek:
            base_sure = item['sure']
            break
    
    sure = base_sure * adet * 0.75 if adet > 1 else base_sure
    sure = sure * HAZIRLAMA_HIZI
    
    print(f"⏱️  Tahmini süre: {int(sure)} saniye")
    print(f"🔥 Hazırlanıyor...\n")
    
    # İlerleme göstergesi
    adimlar = 5
    adim_suresi = sure / adimlar
    
    adim_mesajlari = [
        "🥄 Malzemeler hazırlanıyor...",
        "🔪 Kesim işlemleri yapılıyor...",
        "🍳 Pişirme başladı...",
        "🧂 Baharatlar ekleniyor...",
        "🍽️  Servis için plaklanıyor..."
    ]
    
    for i, mesaj in enumerate(adim_mesajlari):
        print(f"[{i+1}/{adimlar}] {mesaj}")
        time.sleep(adim_suresi)
    
    print(f"\n✅ YEMEK HAZIR!")
    print(f"⏰ Bitiş: {datetime.now().strftime('%H:%M:%S')}")
    print(f"⏱️  Süre: {int(sure)} saniye")
    print(f"{'='*60}\n")
    
    return sure

def siparis_tamamla(siparis_id, sure):
    """Garson'a bildir: Sipariş hazır!"""
    try:
        response = requests.post(
            f"{GARSON_URL}/api/v1/asci/siparis-tamamla",
            json={
                'asci_id': asci_id,
                'siparis_id': siparis_id
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Garson'a bildirildi: Sipariş hazır!")
            istatistikler['basarili'] += 1
            istatistikler['toplam_sure'] += sure
            return True
        else:
            istatistikler['basarisiz'] += 1
            return False
    except:
        istatistikler['basarisiz'] += 1
        return False

def istatistik_goster():
    """Performans istatistiklerini göster"""
    print(f"\n{'='*60}")
    print(f"📊 AŞÇI İSTATİSTİKLERİ")
    print(f"{'='*60}")
    print(f"👤 Aşçı: {ASCI_ISIM} ({asci_id})")
    print(f"📋 Toplam sipariş: {istatistikler['toplam_siparis']}")
    print(f"✅ Başarılı: {istatistikler['basarili']}")
    print(f"❌ Başarısız: {istatistikler['basarisiz']}")
    
    if istatistikler['basarili'] > 0:
        ortalama = istatistikler['toplam_sure'] / istatistikler['basarili']
        print(f"⏱️  Ortalama süre: {ortalama:.1f} saniye")
    
    print(f"{'='*60}\n")

# ============================================================================
# ANA DÖNGÜ
# ============================================================================

def ana_dongu():
    """Aşçının ana çalışma döngüsü"""
    
    print(f"\n{'🔥'*30}")
    print("AŞÇI ÇALIŞMAYA BAŞLADI!")
    print(f"{'🔥'*30}\n")
    
    calisma_sayaci = 0
    bos_sayaci = 0
    
    try:
        while True:
            calisma_sayaci += 1
            
            print(f"\n[Döngü #{calisma_sayaci}] ⏰ {datetime.now().strftime('%H:%M:%S')}")
            print(f"🔍 Mutfak sırasına bakılıyor...")
            
            siparis = siparis_al()
            
            if siparis:
                bos_sayaci = 0
                istatistikler['toplam_siparis'] += 1
                
                sure = yemek_hazirla(siparis)
                siparis_tamamla(siparis['id'], sure)
                continue
            else:
                bos_sayaci += 1
                print(f"💤 Kuyrukta sipariş yok")
                print(f"📊 Boşta kalma: {bos_sayaci} kez")
                
                if bos_sayaci % 10 == 0:
                    istatistik_goster()
                
                print(f"⏳ {POLLING_INTERVAL} saniye bekleniyor...\n")
                time.sleep(POLLING_INTERVAL)
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  DURDURULDU!")
        istatistik_goster()
        print("👋 İyi günler!\n")

# ============================================================================
# ANA PROGRAM
# ============================================================================

def main():
    print("\n" + "="*60)
    print("👨‍🍳 RESTORAN AŞÇI SİMÜLASYONU")
    print("="*60)
    print(f"👤 Aşçı: {ASCI_ISIM}")
    print(f"🎯 Uzmanlık: {', '.join(UZMANLIK) if UZMANLIK else 'Genel'}")
    print(f"🏢 Garson URL: {GARSON_URL}")
    print(f"⏱️  Polling: {POLLING_INTERVAL}s")
    print(f"🚀 Hız: {HAZIRLAMA_HIZI}x")
    print("="*60 + "\n")
    
    print("⏳ 5 saniye bekleniyor (servisler başlasın)...")
    time.sleep(5)
    
    if not garson_kayit_ol():
        print("❌ Kayıt başarısız, program sonlanıyor...")
        return
    
    ana_dongu()

if __name__ == '__main__':
    main()
