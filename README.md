# 🍽️ Restoran Mikroservis Sistemi

Producer-Dispatcher-Worker pattern örneği: Restoran sipariş sistemi

## 📁 Mimari

```
👨‍💼 MÜŞTERILER (Producer)
       ↓
   📝 Sipariş
       ↓
🏃 GARSON (Dispatcher)
       ↓
   🗂️ Kuyruk
       ↓
   ┌────┼────┐
   ↓    ↓    ↓
👨‍🍳 AŞÇI1 AŞÇI2 AŞÇI3 (Workers)
```

## 🚀 Hızlı Başlangıç

### 1. Sistemi Başlat

```bash
docker-compose up --build
```

### 2. Log'ları İzle

```bash
docker-compose logs -f
```

### 3. Test Et

```bash
# Garson health check
curl http://localhost:5000/health

# Manuel sipariş ver
curl -X POST http://localhost:5000/siparis \
  -H "Content-Type: application/json" \
  -d '{
    "musteri_adi": "Test",
    "yemek": "🍕 Pizza Margherita",
    "adet": 1
  }'

# Tüm siparişleri listele
curl http://localhost:5000/siparisler | jq
```

## 📊 Servisler

- **Garson** (Port 5000): Sipariş yönetimi
- **Müşteri**: Sipariş oluşturur
- **Aşçı 1** (Mehmet): Pizza, Pasta uzmanı
- **Aşçı 2** (Ayşe): Burger, Salata uzmanı  
- **Aşçı 3** (Ali): Genel aşçı

## 🛑 Durdurma

```bash
docker-compose down
```

## 📖 Detaylı Döküman

Daha fazla bilgi için session log'larına bakın.
