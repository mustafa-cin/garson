#!/usr/bin/env python3
# musteri.py - Sipariş veren müşteri servisi

"""
MÜŞTERİ'NİN ROLÜ:
1. Menüden yemek seç
2. Garsona sipariş ver (HTTP POST)
3. Sipariş durumunu takip et
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
MUSTERI_ADI = os.getenv('MUSTERI_ADI', "Müşteri")
SENARYO = os.getenv('SENARYO', '1')

# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def siparis_ver(musteri_adi, yemek_bilgi, adet=1, not_ekle=""):
    """Garsona sipariş ver"""
    
    payload = {
        'musteri_adi': musteri_adi,
        'yemek': yemek_bilgi['yemek'],
        'adet': adet,
        'not': not_ekle
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"📞 GARSON ÇAĞRILIYOR...")
        print(f"{'='*60}")
        print(f"👤 Müşteri: {musteri_adi}")
        print(f"🍕 Sipariş: {yemek_bilgi['yemek']} x {adet}")
        if not_ekle:
            print(f"📝 Not: {not_ekle}")
        print(f"⏰ Zaman: {datetime.now().strftime('%H:%M:%S')}")
        
        response = requests.post(
            f"{GARSON_URL}/api/v1/siparis",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            siparis_id = data['siparis_id']
            
            print(f"\n✅ SİPARİŞ ALINDI!")
            print(f"📋 Sipariş No: {siparis_id}")
            print(f"💬 Garson: {data['mesaj']}")
            print(f"📊 Kuyrukta bekleyen: {data['kuyrukta']} sipariş")
            print(f"{'='*60}\n")
            
            return siparis_id
        else:
            print(f"\n❌ SİPARİŞ VERİLEMEDİ! Status: {response.status_code}")
            return None
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ HATA: Garson bulunamıyor! URL: {GARSON_URL}")
        return None
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        return None

def siparis_durumu_sorgula(siparis_id):
    """Sipariş durumunu öğren"""
    try:
        response = requests.get(f"{GARSON_URL}/api/v1/siparis/{siparis_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def siparis_takip_et(siparis_id, timeout=120):
    """Sipariş hazır olana kadar bekle"""
    
    print(f"\n🔍 Sipariş takip başladı: {siparis_id}")
    print(f"⏰ Maksimum bekleme: {timeout} saniye\n")
    
    baslangic = time.time()
    kontrol_sayisi = 0
    
    while True:
        gecen_sure = time.time() - baslangic
        if gecen_sure > timeout:
            print(f"\n⏱️  TIMEOUT: {timeout} saniye aşıldı!")
            return False
        
        kontrol_sayisi += 1
        siparis = siparis_durumu_sorgula(siparis_id)
        
        if not siparis:
            print(f"⚠️  Sorgu hatası, 5 saniye sonra tekrar...")
            time.sleep(5)
            continue
        
        durum = siparis['durum']
        print(f"[{kontrol_sayisi}] 🔍 Durum: {durum}", end="")
        
        if siparis.get('asci_id'):
            print(f" | 👨‍🍳 Aşçı: {siparis['asci_id']}", end="")
        
        print(f" | ⏱️  Geçen: {int(gecen_sure)}s")
        
        if durum == 'Hazır':
            print(f"\n{'='*60}")
            print(f"🎉 SİPARİŞ HAZIR!")
            print(f"{'='*60}")
            print(f"📋 Sipariş: {siparis_id}")
            print(f"🍕 Yemek: {siparis['yemek']}")
            print(f"⏰ Hazırlanma süresi: {int(gecen_sure)} saniye")
            print(f"🙏 Afiyet olsun!")
            print(f"{'='*60}\n")
            return True
        
        time.sleep(5)

# ============================================================================
# SENARYO FONKSİYONLARI
# ============================================================================

def tek_siparis_senaryosu():
    """Tek sipariş ver ve takip et"""
    print("\n" + "🎬 "*20)
    print("SENARYO: TEK SİPARİŞ")
    print("🎬 "*20 + "\n")
    
    yemek = random.choice(MENU)
    adet = random.randint(1, 3)
    
    notlar = ["", "Az acılı olsun", "Çok acılı olsun", "Soslu olsun", "Ekstra peynir"]
    not_ekle = random.choice(notlar)
    
    siparis_id = siparis_ver(MUSTERI_ADI, yemek, adet, not_ekle)
    
    if siparis_id:
        siparis_takip_et(siparis_id)

def coklu_siparis_senaryosu(siparis_sayisi=3):
    """Birden fazla sipariş ver"""
    print("\n" + "🎬 "*20)
    print(f"SENARYO: {siparis_sayisi} FARKLI SİPARİŞ")
    print("🎬 "*20 + "\n")
    
    siparis_idleri = []
    
    for i in range(siparis_sayisi):
        yemek = random.choice(MENU)
        adet = random.randint(1, 2)
        
        print(f"\n📌 SİPARİŞ {i+1}/{siparis_sayisi}")
        siparis_id = siparis_ver(MUSTERI_ADI, yemek, adet)
        
        if siparis_id:
            siparis_idleri.append(siparis_id)
        
        if i < siparis_sayisi - 1:
            bekleme = random.randint(1, 3)
            print(f"💭 Menüye tekrar bakıyor... ({bekleme}s)")
            time.sleep(bekleme)
    
    if siparis_idleri:
        print(f"\n🔍 İlk sipariş takip ediliyor: {siparis_idleri[0]}")
        siparis_takip_et(siparis_idleri[0])

def surekli_siparis_senaryosu():
    """Sürekli sipariş ver (Load test)"""
    print("\n" + "🎬 "*20)
    print("SENARYO: SÜREKLİ SİPARİŞ (CTRL+C ile dur)")
    print("🎬 "*20 + "\n")
    
    siparis_no = 0
    
    try:
        while True:
            siparis_no += 1
            yemek = random.choice(MENU)
            adet = random.randint(1, 2)
            
            print(f"\n🔄 Döngü #{siparis_no}")
            siparis_ver(MUSTERI_ADI, yemek, adet)
            
            bekleme = random.randint(10, 30)
            print(f"\n💤 {bekleme} saniye bekleniyor...")
            time.sleep(bekleme)
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Durduruldu! Toplam {siparis_no} sipariş verildi.")
        print("👋 Görüşürüz!\n")

# ============================================================================
# ANA PROGRAM
# ============================================================================

def main():
    print("\n" + "="*60)
    print("🍽️  RESTORAN MÜŞTERİ SİMÜLASYONU")
    print("="*60)
    print(f"👤 Müşteri: {MUSTERI_ADI}")
    print(f"🏢 Garson URL: {GARSON_URL}")
    print(f"📋 Menü: {len(MENU)} çeşit yemek")
    print("="*60 + "\n")
    
    # Garson kontrolü
    print("🔍 Garson servisini kontrol ediliyor...")
    try:
        response = requests.get(f"{GARSON_URL}/api/v1/sistem/health", timeout=5)
        if response.status_code == 200:
            print("✅ Garson hazır!\n")
        else:
            print("⚠️  Garson yanıt veriyor ama sorun var\n")
    except:
        print("❌ Garson servisine ulaşılamıyor!")
        print("💡 Önce garson servisini başlat\n")
        return
    
    print(f"🎬 Senaryo: {SENARYO}")
    
    if SENARYO == '1':
        tek_siparis_senaryosu()
    elif SENARYO == '2':
        coklu_siparis_senaryosu(3)
    elif SENARYO == '3':
        surekli_siparis_senaryosu()
    else:
        tek_siparis_senaryosu()

if __name__ == '__main__':
    print("⏳ 3 saniye bekleniyor (servisler başlasın)...")
    time.sleep(3)
    main()
