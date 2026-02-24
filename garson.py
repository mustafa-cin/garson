#!/usr/bin/env python3
# garson.py - Siparişleri alan ve mutfağa ileten garson

"""
GARSON'UN ROLÜ:
1. Müşteriden sipariş al
2. Siparişi bir kağıda yaz (queue)
3. Aşçılar gelip sıradaki siparişi alsın
4. Sipariş durumunu takip et
"""

from flask import Flask
from flask_restx import Api, Resource, fields, Namespace
from datetime import datetime
import threading

app = Flask(__name__)

# ============================================================================
# SWAGGER / OpenAPI CONFIGURATION
# ============================================================================
api = Api(
    app,
    version='1.0',
    title='Restoran Garson API',
    description='Restoran sipariş yönetim sistemi - Producer/Dispatcher/Worker pattern',
    doc='/docs',  # Swagger UI endpoint'i
    prefix='/api/v1'  # Tüm endpoint'ler /api/v1 prefix'i ile başlayacak
)

# Namespace'ler - API'yi gruplamak için
ns_siparis = Namespace('siparis', description='Sipariş işlemleri')
ns_asci = Namespace('asci', description='Aşçı işlemleri')
ns_sistem = Namespace('sistem', description='Sistem bilgileri')

api.add_namespace(ns_siparis, path='/siparis')
api.add_namespace(ns_asci, path='/asci')
api.add_namespace(ns_sistem, path='/sistem')

# ============================================================================
# SWAGGER MODEL TANIMLARI (Request/Response Şemaları)
# ============================================================================

# Sipariş oluşturma modeli
siparis_input_model = api.model('SiparisInput', {
    'musteri_adi': fields.String(description='Müşteri adı', example='Ahmet Yılmaz'),
    'yemek': fields.String(required=True, description='Yemek adı', example='Pizza'),
    'adet': fields.Integer(description='Adet', default=1, example=2),
    'not': fields.String(description='Özel notlar', example='Az acılı olsun')
})

# Sipariş çıktı modeli
siparis_output_model = api.model('SiparisOutput', {
    'id': fields.String(description='Sipariş ID', example='S001'),
    'musteri_adi': fields.String(description='Müşteri adı'),
    'yemek': fields.String(description='Yemek'),
    'adet': fields.Integer(description='Adet'),
    'not': fields.String(description='Notlar'),
    'durum': fields.String(description='Sipariş durumu', example='Bekliyor'),
    'siparis_zamani': fields.String(description='Sipariş zamanı'),
    'asci_id': fields.String(description='Aşçı ID'),
    'hazirlama_zamani': fields.String(description='Hazırlanma süresi')
})

# Aşçı kayıt modeli
asci_input_model = api.model('AsciInput', {
    'isim': fields.String(required=True, description='Aşçı ismi', example='Mehmet'),
    'uzmanlik': fields.List(fields.String, description='Uzmanlık alanları', example=['Pizza', 'Pasta'])
})

# Aşçı çıktı modeli
asci_output_model = api.model('AsciOutput', {
    'id': fields.String(description='Aşçı ID'),
    'isim': fields.String(description='Aşçı ismi'),
    'uzmanlik': fields.List(fields.String, description='Uzmanlık alanları'),
    'durum': fields.String(description='Aşçı durumu'),
    'kayit_zamani': fields.String(description='Kayıt zamanı'),
    'hazirlanan_siparis': fields.Integer(description='Hazırlanan sipariş sayısı'),
    'son_aktivite': fields.String(description='Son aktivite zamanı')
})

# Sipariş alma modeli (aşçı için)
siparis_al_input = api.model('SiparisAlInput', {
    'asci_id': fields.String(required=True, description='Aşçı ID', example='A01')
})

# Sipariş tamamlama modeli
siparis_tamamla_input = api.model('SiparisTamamlaInput', {
    'asci_id': fields.String(required=True, description='Aşçı ID', example='A01'),
    'siparis_id': fields.String(required=True, description='Sipariş ID', example='S001')
})

# ============================================================================
# IN-MEMORY VERI YAPILARI
# ============================================================================

siparis_kuyrugu = []  # Bekleyen siparişler (FIFO)
tum_siparisler = {}   # Tüm sipariş geçmişi
ascilar = {}          # Kayıtlı aşçılar
kuyruk_lock = threading.Lock()  # Thread safety için
siparis_sayaci = 0

# ============================================================================
# ENDPOINT 1: SİPARİŞ OLUŞTUR
# ============================================================================

@ns_siparis.route('')
class SiparisOlustur(Resource):
    @ns_siparis.doc('siparis_olustur')
    @ns_siparis.expect(siparis_input_model)
    @ns_siparis.response(201, 'Sipariş başarıyla oluşturuldu')
    @ns_siparis.response(400, 'Geçersiz istek')
    def post(self):
        """Yeni sipariş oluştur"""
        global siparis_sayaci
        
        data = api.payload
        
        if not data or 'yemek' not in data:
            api.abort(400, 'Yemek belirtmelisiniz!')
        
        siparis_sayaci += 1
        siparis_id = f"S{siparis_sayaci:03d}"
        
        siparis = {
            'id': siparis_id,
            'musteri_adi': data.get('musteri_adi', 'Anonim'),
            'yemek': data['yemek'],
            'adet': data.get('adet', 1),
            'not': data.get('not', ''),
            'durum': 'Bekliyor',
            'siparis_zamani': datetime.now().strftime('%H:%M:%S'),
            'asci_id': None,
            'hazirlama_zamani': None
        }
        
        tum_siparisler[siparis_id] = siparis
        
        with kuyruk_lock:
            siparis_kuyrugu.append(siparis.copy())
        
        print(f"\n{'='*60}")
        print(f"🆕 YENİ SİPARİŞ!")
        print(f"{'='*60}")
        print(f"📋 ID: {siparis_id}")
        print(f"👤 Müşteri: {siparis['musteri_adi']}")
        print(f"🍕 Yemek: {siparis['yemek']} x {siparis['adet']}")
        if siparis['not']:
            print(f"📝 Not: {siparis['not']}")
        print(f"⏰ Zaman: {siparis['siparis_zamani']}")
        print(f"📊 Kuyrukta bekleyen: {len(siparis_kuyrugu)} sipariş")
        print(f"{'='*60}\n")
        
        return {
            'siparis_id': siparis_id,
            'durum': 'Mutfağa gönderildi',
            'mesaj': f"Siparişiniz alındı, {siparis['musteri_adi']}! 🙏",
            'kuyrukta': len(siparis_kuyrugu)
        }, 201

# ============================================================================
# ENDPOINT 2: SİPARİŞ DURUMU SORGULA
# ============================================================================

@ns_siparis.route('/<string:siparis_id>')
@ns_siparis.param('siparis_id', 'Sipariş ID')
class SiparisSorgula(Resource):
    @ns_siparis.doc('siparis_sorgula')
    @ns_siparis.response(200, 'Başarılı', siparis_output_model)
    @ns_siparis.response(404, 'Sipariş bulunamadı')
    def get(self, siparis_id):
        """Belirli bir siparişin durumunu sorgula"""
        siparis = tum_siparisler.get(siparis_id)
        
        if not siparis:
            api.abort(404, f'Sipariş bulunamadı: {siparis_id}')
        
        return siparis, 200

# ============================================================================
# ENDPOINT 3: TÜM SİPARİŞLERİ LİSTELE
# ============================================================================

@ns_siparis.route('ler')
class SiparislerListele(Resource):
    @ns_siparis.doc('siparisler_listele')
    @ns_siparis.response(200, 'Başarılı')
    def get(self):
        """Tüm siparişleri listele ve istatistikleri göster"""
        bekleyen = len(siparis_kuyrugu)
        hazirlaniyor = len([s for s in tum_siparisler.values() if s['durum'] == 'Hazırlanıyor'])
        hazir = len([s for s in tum_siparisler.values() if s['durum'] == 'Hazır'])
        
        return {
            'toplam_siparis': len(tum_siparisler),
            'bekleyen': bekleyen,
            'hazirlaniyor': hazirlaniyor,
            'hazir': hazir,
            'siparisler': list(tum_siparisler.values())
        }, 200

# ============================================================================
# ENDPOINT 4: AŞÇI KAYIT
# ============================================================================

@ns_asci.route('/kayit')
class AsciKayit(Resource):
    @ns_asci.doc('asci_kayit')
    @ns_asci.expect(asci_input_model)
    @ns_asci.response(201, 'Aşçı başarıyla kaydedildi')
    @ns_asci.response(400, 'Geçersiz istek')
    def post(self):
        """Yeni aşçı kaydı oluştur"""
        data = api.payload
        
        if not data or 'isim' not in data:
            api.abort(400, 'İsim gerekli!')
        
        asci_id = f"A{len(ascilar)+1:02d}"
        
        asci = {
            'id': asci_id,
            'isim': data['isim'],
            'uzmanlik': data.get('uzmanlik', []),
            'durum': 'Boşta',
            'kayit_zamani': datetime.now().strftime('%H:%M:%S'),
            'hazirlanan_siparis': 0,
            'son_aktivite': datetime.now().strftime('%H:%M:%S')
        }
        
        ascilar[asci_id] = asci
        
        print(f"\n👨‍🍳 YENİ AŞÇI KAYIT OLDU: {asci['isim']} ({asci_id})")
        print(f"   Uzmanlık: {', '.join(asci['uzmanlik']) if asci['uzmanlik'] else 'Genel'}")
        print(f"   Toplam aşçı sayısı: {len(ascilar)}\n")
        
        return {
            'asci_id': asci_id,
            'mesaj': f"Hoş geldin, {asci['isim']}! 👋"
        }, 201

# ============================================================================
# ENDPOINT 5: SİPARİŞ AL
# ============================================================================

@ns_asci.route('/siparis-al')
class SiparisAl(Resource):
    @ns_asci.doc('siparis_al')
    @ns_asci.expect(siparis_al_input)
    @ns_asci.response(200, 'Başarılı')
    @ns_asci.response(400, 'Geçersiz aşçı ID')
    def post(self):
        """Aşçı kuyruktan sipariş alır"""
        data = api.payload
        asci_id = data.get('asci_id')
        
        if not asci_id or asci_id not in ascilar:
            api.abort(400, 'Geçersiz aşçı ID!')
        
        asci = ascilar[asci_id]
        
        with kuyruk_lock:
            if not siparis_kuyrugu:
                return {'mesaj': 'Kuyrukta sipariş yok, biraz bekle! 😴'}, 200
            
            siparis = siparis_kuyrugu.pop(0)
        
        siparis['durum'] = 'Hazırlanıyor'
        siparis['asci_id'] = asci_id
        siparis['hazirlama_baslangic'] = datetime.now().strftime('%H:%M:%S')
        
        tum_siparisler[siparis['id']].update(siparis)
        
        asci['durum'] = 'Meşgul'
        asci['son_aktivite'] = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"👨‍🍳 AŞÇI SİPARİŞ ALDI")
        print(f"{'='*60}")
        print(f"👤 Aşçı: {asci['isim']} ({asci_id})")
        print(f"📋 Sipariş: {siparis['id']}")
        print(f"🍕 Yemek: {siparis['yemek']} x {siparis['adet']}")
        print(f"⏰ Hazırlamaya başlıyor...")
        print(f"📊 Kuyrukta kalan: {len(siparis_kuyrugu)} sipariş")
        print(f"{'='*60}\n")
        
        return {
            'siparis': siparis,
            'mesaj': f'{asci["isim"]}, siparişin hazır! 🔥'
        }, 200

# ============================================================================
# ENDPOINT 6: SİPARİŞ TAMAMLA
# ============================================================================

@ns_asci.route('/siparis-tamamla')
class SiparisTamamla(Resource):
    @ns_asci.doc('siparis_tamamla')
    @ns_asci.expect(siparis_tamamla_input)
    @ns_asci.response(200, 'Sipariş tamamlandı')
    @ns_asci.response(400, 'Geçersiz istek')
    def post(self):
        """Aşçı siparişi tamamlar"""
        data = api.payload
        asci_id = data.get('asci_id')
        siparis_id = data.get('siparis_id')
        
        if not asci_id or asci_id not in ascilar:
            api.abort(400, 'Geçersiz aşçı!')
        
        if not siparis_id or siparis_id not in tum_siparisler:
            api.abort(400, 'Geçersiz sipariş!')
        
        siparis = tum_siparisler[siparis_id]
        asci = ascilar[asci_id]
        
        siparis['durum'] = 'Hazır'
        siparis['hazirlama_bitis'] = datetime.now().strftime('%H:%M:%S')
        
        asci['durum'] = 'Boşta'
        asci['hazirlanan_siparis'] += 1
        asci['son_aktivite'] = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"✅ SİPARİŞ HAZIR!")
        print(f"{'='*60}")
        print(f"📋 Sipariş: {siparis_id}")
        print(f"🍕 Yemek: {siparis['yemek']}")
        print(f"👨‍🍳 Aşçı: {asci['isim']}")
        print(f"⏰ Hazırlandı: {siparis['hazirlama_bitis']}")
        print(f"👤 Müşteri: {siparis['musteri_adi']} - Afiyet olsun! 🎉")
        print(f"{'='*60}\n")
        
        return {
            'mesaj': f"Sipariş hazır! {siparis['musteri_adi']} için {siparis['yemek']} 🍕",
            'siparis': siparis
        }, 200

# ============================================================================
# ENDPOINT 7: AŞÇI LİSTESİ
# ============================================================================

@ns_asci.route('lar')
class AscilarListele(Resource):
    @ns_asci.doc('ascilar_listele')
    @ns_asci.response(200, 'Başarılı')
    def get(self):
        """Tüm aşçıları ve istatistiklerini listele"""
        return {
            'toplam_asci': len(ascilar),
            'bosta': len([a for a in ascilar.values() if a['durum'] == 'Boşta']),
            'mesgul': len([a for a in ascilar.values() if a['durum'] == 'Meşgul']),
            'ascilar': list(ascilar.values())
        }, 200

# ============================================================================
# HEALTH CHECK
# ============================================================================

@ns_sistem.route('/health')
class Health(Resource):
    @ns_sistem.doc('health_check')
    @ns_sistem.response(200, 'Servis sağlıklı')
    def get(self):
        """Servis sağlık durumunu kontrol et"""
        return {
            'servis': 'Garson',
            'durum': 'Çalışıyor',
            'zaman': datetime.now().strftime('%H:%M:%S'),
            'kuyruk': len(siparis_kuyrugu),
            'toplam_siparis': len(tum_siparisler),
            'asci_sayisi': len(ascilar)
        }, 200

# ============================================================================
# BAŞLATMA
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏃 GARSON SERVİSİ BAŞLATILIYOR")
    print("="*60)
    print("📡 Port: 5000")
    print("📋 Görevler:")
    print("   - Müşterilerden sipariş al")
    print("   - Siparişleri mutfak sırasına koy")
    print("   - Aşçıları kaydet ve yönet")
    print("   - Sipariş durumlarını takip et")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
