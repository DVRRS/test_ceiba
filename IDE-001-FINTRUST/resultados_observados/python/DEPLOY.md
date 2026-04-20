# Guía de Despliegue a Cloud Run (Sin Pipelines)

## ⚙️ Configuración de Variables

**Antes de empezar**, define estas variables en tu terminal (o actualiza en `deploy.sh`):

```bash
export PROJECT_ID="tu-project-id"              # Tu GCP Project ID
export REGION="tu-region"                      # Región (ej: us-central1, northamerica-northeast1)
export SERVICE_NAME="tu-servicio"              # Nombre del servicio en Cloud Run
export BQ_DATASET_RAW="tu_dataset_raw"         # Dataset raw
export BQ_DATASET_CLEAN="tu_dataset_clean"     # Dataset clean
export BQ_DATASET_REJECTS="tu_dataset_rejects" # Dataset rejects
export BQ_DATASET_DATAMART="tu_dataset_datamart" # Dataset datamart
```

---

## ⚠️ IMPORTANTE: Dónde ejecutar estos comandos

**TODOS los comandos se ejecutan desde TU TERMINAL LOCAL**.

- ✅ Abre Terminal en tu computadora
- ✅ Posiciónate en la carpeta del proyecto
- ✅ Ejecuta los comandos de esta guía
- ✅ Cloud Build hace el trabajo pesado en la nube

**NO necesitas** conectarte a ningún servidor remoto. Todo se maneja desde tu computadora mediante `gcloud` CLI.

---

## Pre-requisitos

1. **Google Cloud SDK** instalado
   
   ```bash
   # Instalar con Homebrew (Mac)
   brew install --cask google-cloud-sdk
   
   # Verificar instalación
   gcloud --version
   ```

2. **Docker** instalado (opcional si usas Cloud Build)
   ```bash
   docker --version
   ```

3. **Autenticación en GCP**
   ```bash
   gcloud auth login
   gcloud config set project $PROJECT_ID
   ```

4. **Habilitar APIs necesarias**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

---

## 🚀 Opción 1: Deploy con Cloud Build (RECOMENDADO)

**IMPORTANTE**: El proceso es **idéntico** para primera vez y actualizaciones.

---

### Paso 1: Editar variables en `deploy.sh`

Abre `deploy.sh` y actualiza:
```bash
PROJECT_ID="tu-project-id"
REGION="tu-region"
SERVICE_NAME="tu-servicio"
```

### Paso 2: Dar permisos de ejecución (solo primera vez)

```bash
cd /path/to/python/
chmod +x deploy.sh
```

### Paso 3: Ejecutar deploy

```bash
./deploy.sh
```

**Esto funciona para**:
- ✅ Primera vez (crea el servicio)
- ✅ Actualizaciones (actualiza el servicio)

**Tiempo**: 3-5 minutos

### Paso 4: Probar el servicio

```bash
# Obtener la URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --format='value(status.url)')

# Probar ruta clean
curl -X POST "$SERVICE_URL/clean/run" \
  -H "Content-Type: application/json" \
  -d '{"run_dq": true}'

# Probar ruta datamart
curl -X POST "$SERVICE_URL/datamart/run" \
  -H "Content-Type: application/json" \
  -d '{"run": true}'
```

---

## 🔧 Opción 2: Deploy Manual Paso a Paso

### Paso 1: Build local de imagen

```bash
cd /path/to/python/

docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
```

### Paso 2: Push a GCR

```bash
# Configurar Docker para GCR
gcloud auth configure-docker

# Push de imagen
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
```

### Paso 3: Deploy a Cloud Run

```bash
gcloud run deploy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region=$REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars "BQ_LOCATION=$REGION" \
  --set-env-vars "BQ_DATASET_RAW=$BQ_DATASET_RAW" \
  --set-env-vars "BQ_DATASET_CLEAN=$BQ_DATASET_CLEAN" \
  --set-env-vars "BQ_DATASET_REJECTS=$BQ_DATASET_REJECTS" \
  --set-env-vars "BQ_DATASET_DATAMART=$BQ_DATASET_DATAMART" \
  --set-env-vars "DEBUG=false"
```

---

## 🔐 Autenticación con BigQuery

Cloud Run automáticamente usa la **service account del runtime** para autenticarse.

### Opción A: Service account por defecto (más simple)

Por defecto, Cloud Run usa:
```
{project-number}-compute@developer.gserviceaccount.com
```

**Otorgar permisos de BigQuery**:
```bash
# BigQuery Data Editor
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:{project-number}-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# BigQuery Job User
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:{project-number}-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### Opción B: Service account dedicada (mejor práctica)

```bash
# 1. Crear service account
gcloud iam service-accounts create ${SERVICE_NAME}-sa \
  --project=$PROJECT_ID \
  --display-name="${SERVICE_NAME} Service Account"

# 2. Dar permisos de BigQuery
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# 3. Actualizar Cloud Run
gcloud run services update $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --service-account=${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

**Nota**: En Cloud Run **NO necesitas** `GOOGLE_APPLICATION_CREDENTIALS`.

---

## 🔄 Actualizar el Servicio (Re-deploy)

Cuando hagas cambios en el código:

```bash
# Opción fácil: usar deploy.sh
./deploy.sh

# O manualmente
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region=$REGION
```

**No necesitas** especificar env vars de nuevo (se mantienen).

---

## 🛡️ Seguridad (Opcional)

Si **NO quieres** que la API sea pública:

```bash
# Deploy con autenticación requerida
gcloud run deploy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region=$REGION \
  --no-allow-unauthenticated

# Dar acceso a usuarios específicos
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --member="user:tu-email@example.com" \
  --role="roles/run.invoker"
```

Para llamar a la API autenticada:
```bash
# Obtener token
TOKEN=$(gcloud auth print-identity-token)

# Llamar a la API
curl -X POST "$SERVICE_URL/clean/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"run_dq": true}'
```

---

## 📊 Ver Logs

```bash
# Logs en tiempo real
gcloud run services logs read $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --tail

# O usar Cloud Console
# https://console.cloud.google.com/run?project=$PROJECT_ID
```

---

## 💰 Costos Estimados

Cloud Run cobra por:
- **CPU/Memoria**: Solo cuando hay requests
- **Requests**: Primeros 2M gratis/mes

Estimado para uso moderado: **$5-10/mes**

---

## ⚠️ Troubleshooting

### Error: "Permission denied" al acceder a BigQuery
→ Verifica que la service account tenga roles `bigquery.dataEditor` y `bigquery.jobUser`

### Error: "Container failed to start"
→ Revisa logs con `gcloud run services logs read ...`

### Error: Timeout (504)
→ Aumenta timeout en el deploy:
```bash
--timeout 600  # 10 minutos
```

### Build falla por dependencias
→ Verifica que `requirements.txt` esté limpio (sin caracteres raros UTF-16)

---

## 🎯 Resumen: Pasos Rápidos

**Abre tu Terminal y ejecuta**:

```bash
# 1. Configurar variables (actualiza con tus valores)
export PROJECT_ID="tu-project-id"
export REGION="tu-region"
export SERVICE_NAME="tu-servicio"
export BQ_DATASET_RAW="tu_dataset_raw"
export BQ_DATASET_CLEAN="tu_dataset_clean"
export BQ_DATASET_REJECTS="tu_dataset_rejects"
export BQ_DATASET_DATAMART="tu_dataset_datamart"

# 2. Posicionarte en el proyecto
cd /path/to/python/

# 3. Autenticarte en GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# 4. Habilitar APIs (solo primera vez)
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# 5. Dar permisos al script (solo primera vez)
chmod +x deploy.sh

# 6. Editar deploy.sh con tus variables y desplegar
./deploy.sh
```

**Tiempo**: 3-5 minutos

### Después del deploy

```bash
# Ver la URL del servicio
gcloud run services describe $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --format='value(status.url)'

# Probar la API
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --project=$PROJECT_ID --region=$REGION --format='value(status.url)')
curl -X POST "$SERVICE_URL/clean/run" \
  -H "Content-Type: application/json" \
  -d '{"run_dq": true}'
```
