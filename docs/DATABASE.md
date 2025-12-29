# 🗄️ Estrutura do Banco de Dados - ClinicaPro Cardio

## Visão Geral

O ClinicaPro Cardio utiliza **Supabase** (PostgreSQL) para armazenar dados de pacientes, médicos e análises clínicas.

## 📊 Tabelas

### 1. **patients** - Cadastro de Pacientes

Armazena dados pessoais completos dos pacientes.

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,

    -- Dados Pessoais
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    birth_date DATE,
    age INTEGER,
    gender VARCHAR(20),  -- M, F, Outro
    blood_type VARCHAR(5),  -- A+, B+, AB+, O+, A-, B-, AB-, O-

    -- Endereço
    address_street VARCHAR(255),
    address_number VARCHAR(20),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zipcode VARCHAR(10),

    -- Emergência
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),

    -- Convênio
    health_insurance VARCHAR(100),
    insurance_number VARCHAR(100),

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Índices:**
- `idx_patients_cpf` - Busca rápida por CPF
- `idx_patients_full_name` - Busca por nome

**Exemplo de Registro:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "João da Silva Santos",
  "cpf": "12345678900",
  "phone": "(11) 98765-4321",
  "email": "joao@email.com",
  "birth_date": "1965-05-15",
  "age": 58,
  "gender": "M",
  "blood_type": "O+",
  "address_city": "São Paulo",
  "address_state": "SP",
  "emergency_contact_name": "Maria Santos",
  "health_insurance": "Unimed"
}
```

---

### 2. **patient_history** - Histórico Médico

Armazena histórico clínico detalhado do paciente.

```sql
CREATE TABLE patient_history (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),

    -- Arrays JSON para flexibilidade
    comorbidities JSONB DEFAULT '[]',
    allergies JSONB DEFAULT '[]',
    current_medications JSONB DEFAULT '[]',

    family_history TEXT,

    -- Hábitos
    smoker BOOLEAN,
    smoking_pack_years INTEGER,
    alcohol_use VARCHAR(50),
    physical_activity VARCHAR(100),

    -- Dados Cardiológicos
    previous_cardiac_events JSONB DEFAULT '[]',
    cardiac_risk_factors JSONB DEFAULT '[]',
    previous_surgeries JSONB DEFAULT '[]',

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Relacionamento:** `patient_id` → `patients.id` (CASCADE DELETE)

**Exemplo de Registro:**
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "comorbidities": ["HAS", "DM tipo 2", "Dislipidemia"],
  "allergies": ["Penicilina", "Dipirona"],
  "current_medications": [
    {
      "name": "Losartana",
      "dose": "50mg",
      "frequency": "12/12h"
    },
    {
      "name": "Metformina",
      "dose": "850mg",
      "frequency": "12/12h"
    }
  ],
  "smoker": false,
  "smoking_pack_years": 20,
  "alcohol_use": "Social",
  "previous_cardiac_events": ["IAM 2020"],
  "cardiac_risk_factors": ["HAS", "DM", "Ex-tabagista"],
  "previous_surgeries": [
    {
      "surgery": "Angioplastia",
      "year": 2020
    }
  ]
}
```

---

### 3. **doctors** - Cadastro de Médicos

```sql
CREATE TABLE doctors (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    crm VARCHAR(50) UNIQUE NOT NULL,
    specialty VARCHAR(100) DEFAULT 'Cardiologia',
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Índices:**
- `idx_doctors_crm` - Busca por CRM

---

### 4. **case_analyses** - Análises de Casos Clínicos

Armazena todas as análises feitas pelo sistema CrewAI.

```sql
CREATE TABLE case_analyses (
    id UUID PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE NOT NULL,

    doctor_name VARCHAR(255) NOT NULL,
    doctor_crm VARCHAR(50),
    patient_id VARCHAR(255),

    transcription TEXT NOT NULL,
    analysis_result TEXT NOT NULL,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Índices:**
- `idx_case_analyses_case_id` - Busca por ID do caso
- `idx_case_analyses_doctor_crm` - Casos por médico
- `idx_case_analyses_created_at` - Ordenação temporal

**Exemplo:**
```json
{
  "case_id": "CASE-20250129-001",
  "doctor_name": "Dr. João Silva",
  "doctor_crm": "12345-SP",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcription": "Paciente com dor torácica...",
  "analysis_result": "📋 RELATÓRIO SOAP..."
}
```

---

## 🔐 Segurança (RLS - Row Level Security)

Todas as tabelas possuem RLS habilitado:

```sql
-- Exemplo de policy
CREATE POLICY "Enable read for authenticated users"
ON case_analyses
FOR SELECT
USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for service_role"
ON case_analyses
FOR INSERT
WITH CHECK (true);
```

---

## 📈 Views Úteis

### `doctor_stats` - Estatísticas por Médico

```sql
CREATE VIEW doctor_stats AS
SELECT
    doctor_crm,
    doctor_name,
    COUNT(*) as total_cases,
    COUNT(DISTINCT patient_id) as unique_patients,
    MAX(created_at) as last_case_date
FROM case_analyses
WHERE doctor_crm IS NOT NULL
GROUP BY doctor_crm, doctor_name;
```

**Uso:**
```sql
SELECT * FROM doctor_stats WHERE doctor_crm = '12345-SP';
```

---

## 🔄 Triggers

### `update_updated_at_column`

Atualiza automaticamente o campo `updated_at` em todas as tabelas:

```sql
CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 📝 Operações Comuns

### Criar Paciente

```python
from app.database.models import create_patient

result = await create_patient({
    "full_name": "João Silva",
    "cpf": "12345678900",
    "phone": "(11) 98765-4321",
    "birth_date": "1965-05-15",
    "gender": "M"
})
```

### Buscar Paciente

```python
from app.database.models import get_patient_by_cpf

patient = await get_patient_by_cpf("123.456.789-00")
```

### Atualizar Histórico

```python
from app.database.models import update_patient_history

await update_patient_history(patient_id, {
    "comorbidities": ["HAS", "DM"],
    "allergies": ["Penicilina"],
    "smoker": False
})
```

### Buscar Perfil Completo

```python
from app.database.models import get_patient_full_profile

profile = await get_patient_full_profile(patient_id)
# Retorna: patient + history + recent_cases
```

---

## 🚀 Setup Inicial

### 1. Execute o script SQL no Supabase

```bash
# Acesse: https://supabase.com
# Vá em: SQL Editor
# Cole e execute: scripts/setup_supabase_tables.sql
```

### 2. Configure .env

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua-service-key
```

### 3. Teste

```bash
python examples/exemplo_cadastro_paciente.py
```

---

## 📊 Diagrama de Relacionamentos

```
┌─────────────┐
│  patients   │
│             │
│ • id (PK)   │
│ • full_name │
│ • cpf       │
│ • ...       │
└──────┬──────┘
       │
       │ 1:1
       │
┌──────▼──────────────┐
│  patient_history    │
│                     │
│ • id (PK)           │
│ • patient_id (FK)   │◄─────┐
│ • comorbidities     │      │
│ • allergies         │      │
│ • medications       │      │
└─────────────────────┘      │
                             │
                             │
┌────────────────────┐       │
│  case_analyses     │       │
│                    │       │
│ • id (PK)          │       │
│ • patient_id       ├───────┘
│ • doctor_crm       │
│ • transcription    │
│ • analysis_result  │
└────────────────────┘
```

---

## 🔍 Queries Úteis

### Casos recentes de um paciente

```sql
SELECT
    ca.case_id,
    ca.doctor_name,
    ca.created_at,
    LEFT(ca.analysis_result, 200) as preview
FROM case_analyses ca
WHERE ca.patient_id = 'uuid-do-paciente'
ORDER BY ca.created_at DESC
LIMIT 10;
```

### Pacientes com mais casos analisados

```sql
SELECT
    p.full_name,
    COUNT(ca.id) as total_analyses
FROM patients p
LEFT JOIN case_analyses ca ON p.id::text = ca.patient_id
GROUP BY p.id, p.full_name
ORDER BY total_analyses DESC
LIMIT 10;
```

### Médicos mais ativos

```sql
SELECT * FROM doctor_stats
ORDER BY total_cases DESC;
```

---

## 📚 Referências

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
