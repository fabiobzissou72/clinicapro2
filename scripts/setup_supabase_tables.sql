-- ============================================
-- CLINICAPRO CARDIO - SUPABASE TABLES
-- ============================================
-- Execute este SQL no Supabase SQL Editor
-- ============================================

-- ===== TABELA: case_analyses =====
-- Armazena análises de casos clínicos
CREATE TABLE IF NOT EXISTS case_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    doctor_crm VARCHAR(50),
    patient_id VARCHAR(255),
    transcription TEXT NOT NULL,
    analysis_result TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_case_analyses_case_id ON case_analyses(case_id);
CREATE INDEX IF NOT EXISTS idx_case_analyses_doctor_crm ON case_analyses(doctor_crm);
CREATE INDEX IF NOT EXISTS idx_case_analyses_created_at ON case_analyses(created_at DESC);

-- ===== TABELA: doctors =====
-- Cadastro de médicos
CREATE TABLE IF NOT EXISTS doctors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    crm VARCHAR(50) UNIQUE NOT NULL,
    specialty VARCHAR(100) DEFAULT 'Cardiologia',
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doctors_crm ON doctors(crm);

-- ===== TABELA: patients =====
-- Cadastro completo de pacientes
CREATE TABLE IF NOT EXISTS patients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Dados pessoais
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    birth_date DATE,
    age INTEGER,
    gender VARCHAR(20) CHECK (gender IN ('M', 'F', 'Outro', NULL)),
    blood_type VARCHAR(5) CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', NULL)),

    -- Endereço
    address_street VARCHAR(255),
    address_number VARCHAR(20),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zipcode VARCHAR(10),

    -- Contato de emergência
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),

    -- Convênio
    health_insurance VARCHAR(100),
    insurance_number VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patients_cpf ON patients(cpf);
CREATE INDEX IF NOT EXISTS idx_patients_full_name ON patients(full_name);

-- ===== TABELA: patient_history =====
-- Histórico médico dos pacientes
CREATE TABLE IF NOT EXISTS patient_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,

    -- Comorbidades e alergias (JSON arrays)
    comorbidities JSONB DEFAULT '[]',  -- ["HAS", "DM", "Dislipidemia"]
    allergies JSONB DEFAULT '[]',      -- ["Penicilina", "AAS"]
    current_medications JSONB DEFAULT '[]',  -- [{"name": "Losartana", "dose": "50mg"}]

    -- História familiar
    family_history TEXT,

    -- Hábitos
    smoker BOOLEAN DEFAULT false,
    smoking_pack_years INTEGER,
    alcohol_use VARCHAR(50) CHECK (alcohol_use IN ('Nunca', 'Social', 'Diário', NULL)),
    physical_activity VARCHAR(100),

    -- Dados cardiológicos (JSON arrays)
    previous_cardiac_events JSONB DEFAULT '[]',  -- ["IAM 2020", "AVC 2018"]
    cardiac_risk_factors JSONB DEFAULT '[]',     -- ["HAS", "DM tipo 2", "Tabagismo"]

    -- Cirurgias prévias (JSON array)
    previous_surgeries JSONB DEFAULT '[]',  -- [{"surgery": "Apendicectomia", "year": 2015}]

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_history_patient_id ON patient_history(patient_id);

-- ===== ROW LEVEL SECURITY (RLS) =====
-- Habilita RLS para segurança

ALTER TABLE case_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Policies (ajuste conforme necessidade)

-- Permite leitura para usuários autenticados
CREATE POLICY "Enable read for authenticated users" ON case_analyses
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Permite insert para service_role (backend)
CREATE POLICY "Enable insert for service_role" ON case_analyses
    FOR INSERT
    WITH CHECK (true);

-- ===== FUNÇÕES ÚTEIS =====

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para case_analyses
CREATE TRIGGER update_case_analyses_updated_at
    BEFORE UPDATE ON case_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para doctors
CREATE TRIGGER update_doctors_updated_at
    BEFORE UPDATE ON doctors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===== VIEWS ÚTEIS =====

-- View: Estatísticas por médico
CREATE OR REPLACE VIEW doctor_stats AS
SELECT
    doctor_crm,
    doctor_name,
    COUNT(*) as total_cases,
    COUNT(DISTINCT patient_id) as unique_patients,
    MAX(created_at) as last_case_date
FROM case_analyses
WHERE doctor_crm IS NOT NULL
GROUP BY doctor_crm, doctor_name;

-- ===== COMENTÁRIOS =====

COMMENT ON TABLE case_analyses IS 'Armazena análises de casos clínicos realizadas pelo sistema';
COMMENT ON TABLE doctors IS 'Cadastro de médicos usuários do sistema';
COMMENT ON TABLE patients IS 'Dados anonimizados de pacientes';

-- ============================================
-- FIM DO SCRIPT
-- ============================================
-- Após executar, verifique em Supabase:
-- 1. Table Editor > Confirme que as 3 tabelas foram criadas
-- 2. Database > Functions > Confirme trigger function
-- 3. Database > Views > Confirme doctor_stats
-- ============================================
