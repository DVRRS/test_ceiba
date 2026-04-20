# Propuesta: Asistente Conversacional con LLM para Análisis de Cartera

---

## 📋 Resumen Ejecutivo

Propuesta para implementar un **asistente conversacional inteligente** que permita a usuarios del área financiera consultar y analizar datos de cartera mediante **lenguaje natural**, sin necesidad de escribir SQL.

**Valor clave**: Democratizar el acceso a datos complejos, reduciendo el tiempo de análisis de horas a segundos.

---

## 🎯 Problema Actual

### Barreras Técnicas
- **SQL como barrera**: Analistas financieros requieren conocimientos de SQL para consultar el datamart
- **Dependencia de IT**: Solicitudes de reportes personalizados generan cuellos de botella
- **Tiempo perdido**: Análisis ad-hoc pueden tomar horas o días

### Ejemplo Real
```
❌ Usuario piensa: "¿Cuántos créditos del segmento Premium están en mora en [Ciudad X]?"
❌ Realidad actual: Debe pedir a IT que escriba SQL, esperar respuesta, iterar
✅ Con LLM: Pregunta en lenguaje natural, obtiene respuesta inmediata
```

---

## 💡 Solución Propuesta

### Asistente Conversacional con LLM

Un **chatbot financiero especializado** que:
1. **Entiende** preguntas en lenguaje natural
2. **Genera** queries SQL automáticamente
3. **Ejecuta** contra el datamart del proyecto
4. **Presenta** resultados en formato amigable (tablas, gráficos, insights)

---

## 🏗️ Arquitectura Técnica

```
┌─────────────────────────────────────────────────┐
│  Frontend: Interfaz de Chat (tipo ChatGPT)     │
│  - Web UI amigable                              │
│  - Historial de conversaciones                  │
│  - Visualización de resultados                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Backend: Orquestador LLM                       │
│  - FastAPI / Flask                              │
│  - Gestión de contexto del datamart            │
│  - Generación y validación de SQL              │
│  - Ejecución segura de queries                 │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐     ┌───────────────────┐
│  LLM Engine  │     │  BigQuery         │
│  (flexible)  │     │  Datamart         │
│              │     │  - 6 objetos      │
│ • OpenAI     │     │  - 3 tablas       │
│ • Claude     │     │  - 3 vistas       │
│ • Gemini     │     └───────────────────┘
│ • Llama      │
│ • Mistral    │
└──────────────┘
```

---

## 🔧 Componentes Clave

### 1. **Frontend: Interfaz de Chat**

**Tecnología sugerida**: Streamlit, Gradio, o React + ChatUI

**Funcionalidades**:
- 💬 Input de texto natural
- 📊 Visualización de resultados (tablas, gráficos)
- 📜 Historial de conversaciones
- 🔄 Refinamiento iterativo de preguntas
- 📥 Exportar resultados (CSV, Excel, PDF)

**Ejemplo UI**:
```
Usuario: "Dame los top 5 créditos con mayor mora en [Ciudad X]"

[Procesando...]

Asistente: Encontré 5 créditos:
┌──────────┬─────────────┬──────────┬─────────────┐
│ Loan ID  │ Cliente     │ Mora     │ Saldo       │
├──────────┼─────────────┼──────────┼─────────────┤
│ L***01   │ Cliente A   │ 45 días  │ $XX,XXX,XXX │
│ L***02   │ Cliente B   │ 38 días  │ $XX,XXX,XXX │
│ L***03   │ Cliente C   │ 32 días  │ $XX,XXX,XXX │
...
└──────────┴─────────────┴──────────┴─────────────┘

💡 Insight: El 80% de estos clientes tienen >30 días de mora
```

---

### 2. **Backend: Orquestador LLM**

**Responsabilidades**:

#### A. Gestión de Contexto del Datamart
```python
# Inyectar esquema del datamart al LLM
DATAMART_CONTEXT = """
Tienes acceso a estas tablas en BigQuery:

1. table_installments_master:
   - Granularidad: Por cuota
   - Campos: loan_id, customer_name, city, segment, 
             outstanding_balance, days_past_due, is_overdue
   
2. table_loans_summary:
   - Granularidad: Por crédito
   - Campos: loan_id, total_outstanding, overdue_balance, 
             risk_category

3. table_payments_detail:
   - Granularidad: Por pago
   - Campos: payment_id, payment_date, payment_amount, 
             payment_to_overdue, payment_on_time

Reglas de negocio:
- mora_bucket: "Al día", "Mora 1-30 días", "Mora 31-60 días", etc.
- cohort: Mes de desembolso (YYYY-MM)
- is_overdue: TRUE si outstanding_balance > 0 y due_date < hoy
"""
```

#### B. Generación de SQL
```python
def generate_sql(user_question: str, llm_provider: str) -> str:
    """
    Convierte pregunta natural → SQL
    """
    prompt = f"""
    {DATAMART_CONTEXT}
    
    Pregunta del usuario: {user_question}
    
    Genera una query SQL válida para BigQuery.
    Solo usa las tablas disponibles en el datamart.
    """
    
    sql = llm_client.generate(prompt)
    return validate_sql(sql)  # Validación de seguridad
```

#### C. Validación de Seguridad
```python
def validate_sql(sql: str) -> str:
    """
    Asegura que SQL sea seguro (no DROP, DELETE, etc.)
    """
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]
    sql_upper = sql.upper()
    
    for keyword in forbidden:
        if keyword in sql_upper:
            raise ValueError(f"SQL no permitido: contiene {keyword}")
    
    # Solo permite SELECT
    if not sql_upper.strip().startswith("SELECT"):
        raise ValueError("Solo se permiten queries SELECT")
    
    return sql
```

#### D. Ejecución de Query
```python
def execute_query(sql: str) -> pd.DataFrame:
    """
    Ejecuta SQL contra BigQuery y devuelve resultados
    """
    client = bigquery.Client(project=PROJECT_ID)
    df = client.query(sql).to_dataframe()
    return df
```

---

### 3. **LLM Engine: Parametrizable**

**Flexibilidad**: Soportar múltiples proveedores mediante adaptadores

```python
# config.yaml
llm:
  provider: "openai"  # openai, claude, gemini, llama, mistral
  model: "gpt-4"
  temperature: 0.0
  max_tokens: 1500
```

**Proveedores Soportados**:

| Proveedor | Modelo Sugerido | Costo | Ventaja |
|-----------|----------------|-------|---------|
| **OpenAI** | GPT-4o | $$ | Mejor precisión en SQL |
| **Anthropic** | Claude 3.5 Sonnet | $$ | Excelente razonamiento |
| **Google** | Gemini 1.5 Pro | $ | Integración nativa con BigQuery |
| **Meta** | Llama 3.1 70B | Gratis | Open source, self-hosted |
| **Mistral** | Mixtral 8x7B | Gratis | Open source, rápido |

**Implementación**:
```python
class LLMAdapter:
    @staticmethod
    def get_client(provider: str):
        if provider == "openai":
            return OpenAIClient()
        elif provider == "claude":
            return ClaudeClient()
        elif provider == "gemini":
            return GeminiClient()
        # ... más proveedores
```

---

### 4. **Base de Datos: Datamart como Contexto**

**Dataset**: `project_datamart` (ya existente)

**Configuración**:
```python
# datamart_config.yaml
datamart:
  project_id: "tu-project-id"
  dataset: "project_datamart"
  
  tables:
    - name: "table_installments_master"
      description: "Detalle por cuota con métricas de mora"
      primary_key: "installment_id"
      
    - name: "table_loans_summary"
      description: "Resumen por crédito con riesgo agregado"
      primary_key: "loan_id"
      
    - name: "table_payments_detail"
      description: "Detalle de pagos con flags de mora"
      primary_key: "payment_id"
```

---

## 📊 Beneficios Esperados

### Cuantitativos
- ⏱️ **Reducción 90%** en tiempo de análisis (de horas a segundos)
- 📉 **Reducción 70%** en solicitudes a IT para reportes ad-hoc
- 💰 **ROI positivo** en 3-6 meses (ahorro en tiempo vs costo de implementación)

### Cualitativos
- 🎯 **Democratización**: Analistas sin SQL pueden hacer análisis complejos
- 🚀 **Agilidad**: Decisiones basadas en datos en tiempo real
- 💡 **Insights**: LLM puede sugerir análisis adicionales
- 📈 **Adopción**: Interfaz amigable aumenta uso del datamart

---

## 🛠️ Implementación Sugerida

### Fase 1: MVP (4-6 semanas)
- ✅ Backend básico con FastAPI
- ✅ Integración con 1 LLM (ej: OpenAI GPT-4)
- ✅ Contexto del datamart parametrizado
- ✅ Generación y ejecución de SQL
- ✅ Frontend simple con Streamlit
- ✅ 10 preguntas predefinidas como ejemplos

### Fase 2: Mejoras (4-6 semanas)
- ✅ Soporte multi-LLM (añadir Claude, Gemini, Llama)
- ✅ Historial de conversaciones
- ✅ Visualizaciones (gráficos)
- ✅ Exportación de resultados
- ✅ Validaciones de seguridad avanzadas

### Fase 3: Producción (4-6 semanas)
- ✅ Autenticación de usuarios
- ✅ Rate limiting
- ✅ Logging y monitoreo
- ✅ Caché de queries frecuentes
- ✅ Deploy a Cloud Run
- ✅ Documentación y capacitación

---

## 💰 Estimación de Costos

### Costos de Infraestructura

| Componente | Costo Mensual |
|------------|---------------|
| **Cloud Run** (backend) | $5-10 |
| **BigQuery** (queries adicionales) | $10-20 |
| **LLM API Calls** | $50-200* |
| **Frontend Hosting** | $5-10 |
| **Total** | **$70-240/mes** |

\* Depende del proveedor y volumen de uso

### Costos por Proveedor LLM (por 1M tokens)

| Proveedor | Input | Output | Costo por pregunta (estimado) |
|-----------|-------|--------|--------------------------------|
| OpenAI GPT-4o | $2.50 | $10 | $0.02-0.05 |
| Claude 3.5 Sonnet | $3 | $15 | $0.03-0.06 |
| Gemini 1.5 Pro | $1.25 | $5 | $0.01-0.03 |
| Llama 3.1 (self-hosted) | Gratis | Gratis | $0 (costo de compute) |

**Estimado**: 1,000 preguntas/mes = $20-60 en costos de LLM

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: LLM genera SQL incorrecto
**Probabilidad**: Media  
**Impacto**: Medio  

**Mitigación**:
- ✅ Validación sintáctica del SQL generado
- ✅ Ejecución con timeout (evitar queries costosas)
- ✅ Dry-run antes de ejecutar (validar con EXPLAIN)
- ✅ Feedback loop: usuario puede reportar errores

### Riesgo 2: Costos de LLM se disparan
**Probabilidad**: Media  
**Impacto**: Medio  

**Mitigación**:
- ✅ Caché de queries frecuentes
- ✅ Rate limiting por usuario
- ✅ Alertas de presupuesto en GCP
- ✅ Opción de usar modelos open source (Llama, Mistral)

### Riesgo 3: Exposición de datos sensibles
**Probabilidad**: Baja  
**Impacto**: Alto  

**Mitigación**:
- ✅ Solo lectura (SELECT), no escritura
- ✅ Validación estricta de SQL (blacklist de comandos)
- ✅ Row-level security en BigQuery
- ✅ Logs de auditoría de todas las queries

### Riesgo 4: Dependencia de API externa (OpenAI, Claude)
**Probabilidad**: Baja  
**Impacto**: Medio  

**Mitigación**:
- ✅ Arquitectura multi-LLM (fallback a otro proveedor)
- ✅ Opción de self-hosted (Llama, Mistral)
- ✅ Caché de respuestas comunes

---

## 🔐 Consideraciones de Seguridad

### 1. Validación de SQL
```python
# Solo permitir SELECT
# Bloquear: DROP, DELETE, UPDATE, INSERT, TRUNCATE
# Validar tablas permitidas (solo datamart)
```

### 2. Autenticación
```python
# OAuth 2.0 con Google Workspace
# Roles: viewer (solo consulta), admin (configuración)
```

### 3. Auditoría
```python
# Log de todas las preguntas y SQL generados
# Registro de usuario, timestamp, query, resultados
```

---

## 📚 Tecnologías Recomendadas

### Backend
- **Framework**: FastAPI (async, rápido, OpenAPI docs)
- **LLM Orchestration**: LangChain o LlamaIndex
- **Database**: BigQuery (ya existente)

### Frontend
- **Opción 1 (Rápida)**: Streamlit (Python puro, fácil de iterar)
- **Opción 2 (Profesional)**: React + ChatUI component

### LLM
- **Producción**: OpenAI GPT-4o o Claude 3.5 Sonnet
- **Costo-efectivo**: Google Gemini 1.5 Pro
- **Self-hosted**: Llama 3.1 70B (vía Ollama o vLLM)

---

## 🎓 Capacitación y Adopción

### Plan de Capacitación

1. **Sesión 1: Introducción** (1 hora)
   - Demostración de casos de uso
   - Cómo hacer preguntas efectivas
   - Limitaciones del sistema

2. **Sesión 2: Hands-on** (2 horas)
   - Ejercicios prácticos
   - Preguntas comunes
   - Troubleshooting

3. **Documentación**
   - FAQ
   - Ejemplos de preguntas por caso de uso
   - Guía de mejores prácticas

---

## 📈 Métricas de Éxito

### Adopción
- **Target**: 80% de usuarios del área financiera usan la herramienta
- **Métrica**: Preguntas/usuario/semana

### Performance
- **Target**: 95% de queries generadas correctamente
- **Métrica**: Tasa de éxito (queries válidas / total)

### Satisfacción
- **Target**: NPS > 50
- **Métrica**: Encuesta trimestral

### Eficiencia
- **Target**: Reducción 80% en tiempo de análisis
- **Métrica**: Tiempo promedio para obtener respuesta

---

## 🚀 Próximos Pasos

### Inmediatos (Semana 1-2)
1. ✅ Revisar y aprobar propuesta
2. ✅ Definir presupuesto
3. ✅ Seleccionar proveedor LLM inicial
4. ✅ Asignar equipo de desarrollo

### Corto Plazo (Mes 1)
1. ✅ Setup de infraestructura
2. ✅ Desarrollo de MVP
3. ✅ Testing interno con 3-5 usuarios
4. ✅ Iteración basada en feedback

### Mediano Plazo (Mes 2-3)
1. ✅ Rollout a área financiera completa
2. ✅ Capacitación de usuarios
3. ✅ Monitoreo de adopción y performance
4. ✅ Mejoras continuas

---

## 📝 Conclusión

La implementación de un **asistente conversacional con LLM** representa una oportunidad estratégica para:

1. **Democratizar** el acceso a datos complejos
2. **Acelerar** la toma de decisiones financieras
3. **Reducir** la carga en el equipo de IT
4. **Maximizar** el ROI del datamart existente

Con una arquitectura **parametrizable y flexible**, podemos adaptar la solución a diferentes proveedores de LLM (libres o pagos) según evolucionen los costos y capacidades del mercado.

**Inversión estimada**: $70-240/mes  
**Retorno esperado**: Ahorro de 10-20 horas/semana en análisis manual

**Última actualización**: Abril 2026
