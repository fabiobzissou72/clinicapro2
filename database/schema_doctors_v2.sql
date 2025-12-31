-- ============================================
-- SCHEMA PARA TABELA DOCTORS (Supabase)
-- Sistema de autenticação de médicos
-- Versão 2: Script mais robusto com verificações
-- ============================================

-- ============================================
-- PASSO 1: CRIAR TABELA DOCTORS (se não existir)
-- ============================================

CREATE TABLE IF NOT EXISTS doctors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    crm TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    specialty TEXT DEFAULT 'Cardiologia',
    phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- PASSO 2: ADICIONAR COLUNAS (se não existirem)
-- ============================================

-- Adiciona is_active se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'doctors'
          AND column_name = 'is_active'
    ) THEN
        ALTER TABLE doctors ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
END $$;

-- Adiciona updated_at se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'doctors'
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE doctors ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- ============================================
-- PASSO 3: CRIAR ÍNDICES (se não existirem)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_doctors_email ON doctors(email);
CREATE INDEX IF NOT EXISTS idx_doctors_crm ON doctors(crm);
CREATE INDEX IF NOT EXISTS idx_doctors_active ON doctors(is_active);

-- ============================================
-- PASSO 4: ADICIONAR COMENTÁRIOS
-- ============================================

COMMENT ON TABLE doctors IS 'Tabela de médicos cadastrados no sistema';
COMMENT ON COLUMN doctors.id IS 'ID único do médico (UUID)';
COMMENT ON COLUMN doctors.crm IS 'CRM do médico (formato: 12345-UF)';
COMMENT ON COLUMN doctors.email IS 'Email único para login';
COMMENT ON COLUMN doctors.password_hash IS 'Hash bcrypt da senha';
COMMENT ON COLUMN doctors.specialty IS 'Especialidade médica';
COMMENT ON COLUMN doctors.is_active IS 'Status ativo/inativo';

-- ============================================
-- PASSO 5: ATUALIZAR TABELA CASE_ANALYSES
-- Adicionar referência ao médico
-- ============================================

-- Adicionar coluna doctor_id se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'case_analyses'
          AND column_name = 'doctor_id'
    ) THEN
        ALTER TABLE case_analyses ADD COLUMN doctor_id UUID;
        -- Adiciona FK depois de criar a coluna
        ALTER TABLE case_analyses ADD CONSTRAINT fk_doctor
            FOREIGN KEY (doctor_id) REFERENCES doctors(id);
        CREATE INDEX idx_case_analyses_doctor ON case_analyses(doctor_id);
    END IF;
END $$;

-- ============================================
-- PASSO 6: FUNÇÕES AUXILIARES
-- ============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar updated_at
DROP TRIGGER IF EXISTS update_doctors_updated_at ON doctors;
CREATE TRIGGER update_doctors_updated_at
    BEFORE UPDATE ON doctors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- PASSO 7: ROW LEVEL SECURITY (RLS) - COMENTADO
-- Descomente se quiser ativar RLS
-- ============================================

-- IMPORTANTE: RLS precisa ser configurado com cuidado
-- Descomente apenas se tiver certeza da configuração de auth

-- ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;

-- Policy: Médicos podem ver apenas seu próprio perfil
-- CREATE POLICY doctors_select_own
--     ON doctors
--     FOR SELECT
--     USING (auth.uid()::text = id::text);

-- Policy: Serviço pode fazer tudo (para autenticação)
-- CREATE POLICY doctors_service_all
--     ON doctors
--     FOR ALL
--     USING (auth.role() = 'service_role');

-- ============================================
-- MENSAGEM DE SUCESSO
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Schema doctors criado/atualizado com sucesso!';
    RAISE NOTICE '📋 Tabela: doctors';
    RAISE NOTICE '📊 Colunas: id, name, crm, email, password_hash, specialty, phone, is_active, created_at, updated_at';
    RAISE NOTICE '🔐 Índices criados para email, crm e is_active';
    RAISE NOTICE '⚠️  RLS está DESABILITADO. Para habilitar, descomente o PASSO 7';
END $$;
