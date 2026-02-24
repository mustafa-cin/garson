# 🚀 Garson Projesi - Minikube'e Deploy Rehberi (A'dan Z'ye)

Bu döküman, `garson` projesini (Docker Compose ile çalışan restoran mikroservisleri) **Minikube** üzerinde Kubernetes'e deploy etmeyi adım adım anlatır.

---

## 📖 KAVRAMLAR - Önce Bunları Anla

### Docker Compose vs Kubernetes Karşılaştırması

| Docker Compose        | Kubernetes               | Ne İşe Yarar?                        |
|-----------------------|--------------------------|---------------------------------------|
| `docker-compose.yml`  | Deployment + Service YAML| Servislerin tanımı                    |
| `services:`           | `Deployment`             | Container'ları çalıştırır            |
| `ports:`              | `Service`                | Ağ erişimi sağlar                    |
| `networks:`           | `Namespace` + Service DNS| Servisler arası iletişim             |
| `depends_on:`         | `readinessProbe`         | Sıralı başlatma / hazır olma        |
| `restart: unless-stopped` | Deployment (varsayılan) | Çökerse otomatik yeniden başlat  |
| `restart: "no"`       | `Job`                    | Bir kez çalış bitir                  |
| `environment:`        | `env:` (Deployment içinde)| Ortam değişkenleri                  |

### Neden Minikube?
- **Minikube** = Bilgisayarında çalışan tek node'lu mini Kubernetes cluster'ı
- Gerçek Kubernetes'i öğrenmek için ideal
- Docker Desktop'a benzer ama K8s odaklı

---

## 📋 ÖN GEREKSİNİMLER

Aşağıdakilerin kurulu olması gerekiyor:

### 1. Docker Desktop
```
Kontrol: docker --version
İndirme: https://www.docker.com/products/docker-desktop/
```

### 2. Minikube
```powershell
# Windows'ta PowerShell (Yönetici) ile:
winget install Kubernetes.minikube

# Kontrol:
minikube version
```

### 3. kubectl (Kubernetes CLI)
```powershell
# Windows'ta:
winget install Kubernetes.kubectl

# Kontrol:
kubectl version --client
```

---

## 🔧 ADIM ADIM DEPLOY SÜRECİ

### ADIM 1: Minikube'ü Başlat

```powershell
# Minikube cluster'ını başlat (ilk seferde biraz sürer)
minikube start --driver=docker
```

**Ne oldu?**
- Minikube, Docker içinde bir sanal makine (container) oluşturdu
- Bu container içinde tam bir Kubernetes cluster'ı çalışıyor
- `kubectl` artık bu cluster'a bağlı

**Kontrol:**
```powershell
# Cluster durumunu kontrol et
minikube status

# Çıktı böyle olmalı:
# minikube
# type: Control Plane
# host: Running
# kubelet: Running
# apiserver: Running
# kubeconfig: Configured
```

---

### ADIM 2: Docker Image'ları Minikube İçinde Build Et

**NEDEN?**
Docker Desktop ve Minikube **farklı Docker daemon'ları** kullanır.
Senin bilgisayarındaki Docker'da build ettiğin image, Minikube'ün içinde yoktur.

**İki seçenek var:**
1. ✅ Minikube'ün Docker'ını kullan (basit) ← **Bunu yapacağız**
2. Image'ı bir registry'ye push et (gerçek ortamda yapılır)

```powershell
# Terminal'i Minikube'ün Docker daemon'ına bağla
# Bu komut SADECE bu terminal penceresi için geçerli!
# Her yeni terminal açtığında tekrar çalıştırman gerekir.

# PowerShell için:
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# CMD için:
# @FOR /f "tokens=*" %i IN ('minikube -p minikube docker-env --shell cmd') DO @%i
```

**Kontrol:**
```powershell
docker images
# Minikube'ün image'larını görmelisin (k8s.gcr.io/... gibi)
```

---

### ADIM 3: Image'ları Build Et

```powershell
# garson klasörüne git
cd c:\Users\mcin\Desktop\test\garson

# Garson image'ını build et
docker build -t restoran/garson:latest -f Dockerfile.garson .

# Aşçı image'ını build et
docker build -t restoran/asci:latest -f Dockerfile.asci .

# Müşteri image'ını build et
docker build -t restoran/musteri:latest -f Dockerfile.musteri .
```

**Ne oldu?**
- 3 adet Docker image build ettik
- `imagePullPolicy: Never` sayesinde Kubernetes bu image'ları internetten çekmeye çalışmayacak
- Direkt Minikube'ün local Docker'ındaki image'ları kullanacak

**Kontrol:**
```powershell
docker images | findstr restoran
# restoran/garson    latest   ...
# restoran/asci      latest   ...
# restoran/musteri   latest   ...
```

---

### ADIM 4: Namespace Oluştur

```powershell
kubectl apply -f k8s/namespace.yaml
```

**Ne oldu?**
- `restoran` adında bir namespace oluştu
- Tüm kaynaklarımız bu namespace içinde yaşayacak
- Namespace = Projenin kendi odası, diğer projelerle karışmaz

**Kontrol:**
```powershell
kubectl get namespaces
# restoran namespace'ini görmelisin
```

---

### ADIM 5: Garson'u Deploy Et (Önce Garson, Çünkü Herkes Ona Bağımlı)

```powershell
# Garson Deployment'ını oluştur
kubectl apply -f k8s/garson-deployment.yaml

# Garson Service'ini oluştur
kubectl apply -f k8s/garson-service.yaml
```

**Ne oldu?**
- Kubernetes bir `garson` pod'u oluşturdu (içinde garson container'ı çalışıyor)
- `garson` isimli bir Service oluştu (DNS adı: `garson`, port: `5000`)
- NodePort 30500 ile dışarıdan da erişilebilir

**Kontrol (garson'un hazır olmasını bekle):**
```powershell
# Pod durumunu izle (STATUS = Running olana kadar bekle)
kubectl get pods -n restoran -w

# Çıktı:
# NAME                      READY   STATUS    RESTARTS   AGE
# garson-xxxxx-yyyyy        1/1     Running   0          30s

# CTRL+C ile izlemeyi durdur

# Service kontrolü
kubectl get svc -n restoran
```

**⏳ ÖNEMLİ:** Garson pod'u `1/1 Running` ve `READY` olana kadar sonraki adıma geçme!

---

### ADIM 6: Aşçıları Deploy Et

```powershell
# 3 aşçıyı birden deploy et
kubectl apply -f k8s/asci1-deployment.yaml
kubectl apply -f k8s/asci2-deployment.yaml
kubectl apply -f k8s/asci3-deployment.yaml
```

**Ne oldu?**
- 3 aşçı pod'u oluştu (Mehmet Usta, Ayşe Hanım, Ali Usta)
- Her biri `http://garson:5000` adresine bağlanarak sipariş bekliyor
- Kubernetes DNS sayesinde `garson` ismi otomatik olarak Garson Service'ine yönleniyor

**Kontrol:**
```powershell
kubectl get pods -n restoran
# 4 pod görmelisin (1 garson + 3 aşçı), hepsi Running
```

---

### ADIM 7: Garson'a Dışarıdan Erişim Testi

```powershell
# Minikube IP adresini al
minikube ip

# Veya doğrudan erişim aç (en kolay yol)
minikube service garson -n restoran --url
```

Bu komut bir URL verecek, örneğin: `http://127.0.0.1:xxxxx`

```powershell
# Health check
curl http://<MINIKUBE_URL>/api/v1/sistem/health

# Swagger UI'ı tarayıcıda aç
# Tarayıcıda şu adrese git: http://<MINIKUBE_URL>/docs
```

---

### ADIM 8: Müşteri Job'ını Çalıştır (Sipariş Gönder)

```powershell
kubectl apply -f k8s/musteri-job.yaml
```

**Ne oldu?**
- Müşteri pod'u oluştu, garson'a sipariş gönderdi
- Siparişler garson tarafından aşçılara dağıtıldı
- İş bitince müşteri pod'u `Completed` durumuna geçti

**Kontrol:**
```powershell
# Müşteri job durumu
kubectl get jobs -n restoran

# Müşteri loglarını gör
kubectl logs -n restoran job/musteri-ahmet

# Garson loglarını gör (siparişlerin geldiğini gör)
kubectl logs -n restoran deployment/garson

# Aşçı loglarını gör
kubectl logs -n restoran deployment/asci1-mehmet
kubectl logs -n restoran deployment/asci2-ayse
kubectl logs -n restoran deployment/asci3-ali
```

---

## 🎯 TEK SATIRDA HEPSİNİ DEPLOY ET

Yukarıdaki adımları anladıysan, her şeyi tek komutla da yapabilirsin:

```powershell
kubectl apply -f k8s/
```

Bu komut `k8s/` klasöründeki tüm `.yaml` dosyalarını otomatik sırayla uygular.

---

## 📊 FAYDALI KOMUTLAR

```powershell
# Tüm kaynakları gör
kubectl get all -n restoran

# Pod loglarını canlı izle
kubectl logs -f -n restoran deployment/garson

# Pod'un içine gir (debug için)
kubectl exec -it -n restoran deployment/garson -- /bin/bash

# Pod detaylarını gör (hata ayıklama için)
kubectl describe pod <POD_ADI> -n restoran

# Müşteri job'ını tekrar çalıştırmak istersen önce eskiyi sil
kubectl delete job musteri-ahmet -n restoran
kubectl apply -f k8s/musteri-job.yaml

# Manuel sipariş gönder (port-forward ile)
kubectl port-forward -n restoran svc/garson 5000:5000
# Başka terminal'de:
curl -X POST http://localhost:5000/api/v1/siparis -H "Content-Type: application/json" -d "{\"musteri_adi\": \"Test\", \"yemek\": \"Pizza\", \"adet\": 1}"
```

---

## 🛑 TEMİZLEME (Her Şeyi Sil)

```powershell
# Tüm kaynakları sil
kubectl delete -f k8s/

# Veya namespace'i sil (içindeki her şeyi temizler)
kubectl delete namespace restoran

# Minikube'ü durdur (cluster'ı kapat)
minikube stop

# Minikube'ü tamamen sil (disk alanı kazanmak için)
minikube delete
```

---

## 🔄 DOCKER COMPOSE vs KUBERNETES AKIŞ KARŞILAŞTIRMASI

```
DOCKER COMPOSE:                          KUBERNETES (Minikube):
──────────────                           ──────────────────────
docker-compose up --build                1. minikube start
                                         2. eval $(minikube docker-env)
        ↓                               3. docker build (3 image)
                                         4. kubectl apply -f k8s/
    Hepsi çalışır ✅                         ↓
                                         Hepsi çalışır ✅

docker-compose down                      kubectl delete -f k8s/
                                         minikube stop
```

---

## ❓ OLASI HATALAR VE ÇÖZÜMLERİ

### "ImagePullBackOff" veya "ErrImageNeverPull" Hatası
**Sebep:** Image Minikube'ün Docker'ında yok.
**Çözüm:** `minikube docker-env` komutunu çalıştırıp, image'ları tekrar build et.

### Pod "CrashLoopBackOff" Durumunda
**Sebep:** Container başlatılamıyor veya hemen çöküyor.
**Çözüm:**
```powershell
kubectl logs -n restoran <POD_ADI>
kubectl describe pod -n restoran <POD_ADI>
```

### Garson'a Erişilemiyor
**Sebep:** Service veya port-forward düzgün çalışmıyor.
**Çözüm:**
```powershell
minikube service garson -n restoran
# veya
kubectl port-forward -n restoran svc/garson 5000:5000
```

### Aşçılar Garson'a Bağlanamıyor
**Sebep:** Garson henüz hazır değil veya Service oluşmamış.
**Çözüm:** Önce garson'un `Running` ve `Ready` olduğundan emin ol.
