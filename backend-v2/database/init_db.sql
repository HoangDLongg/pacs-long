-- Bật extension vector (cho tìm kiếm AI)
CREATE EXTENSION IF NOT EXISTS vector;

-- ========== BẢNG 1: patients (bệnh nhân) ==========
CREATE TABLE IF NOT EXISTS patients (
    id              SERIAL PRIMARY KEY,
    patient_id      VARCHAR(50) UNIQUE NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    birth_date      DATE,
    gender          CHAR(1) CHECK (gender IN ('M', 'F')),
    phone           VARCHAR(20),
    address         TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ========== BẢNG 2: users (tài khoản) ==========
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    username            VARCHAR(50) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(100),
    role                VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'doctor', 'technician', 'patient')),
    is_active           BOOLEAN DEFAULT TRUE,
    linked_patient_id   INT REFERENCES patients(id),
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ========== BẢNG 3: studies (ca chụp) ==========
CREATE TABLE IF NOT EXISTS studies (
    id              SERIAL PRIMARY KEY,
    study_uid       VARCHAR(200) UNIQUE NOT NULL,
    patient_id      INT REFERENCES patients(id),
    study_date      DATE NOT NULL,
    modality        VARCHAR(10) CHECK (modality IN ('CR', 'CT', 'MR', 'US', 'DX', 'MG')),
    body_part       VARCHAR(50),
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'REPORTED', 'VERIFIED')),
    technician_id   INT REFERENCES users(id),
    orthanc_id      VARCHAR(200),
    num_instances   INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ========== BẢNG 4: diagnostic_reports (báo cáo chẩn đoán) ==========
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id              SERIAL PRIMARY KEY,
    study_id        INT REFERENCES studies(id) UNIQUE,
    doctor_id       INT REFERENCES users(id),
    findings        TEXT NOT NULL,
    conclusion      TEXT NOT NULL,
    recommendation  TEXT,
    report_date     TIMESTAMP DEFAULT NOW(),
    embedding       vector(1024),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ========== BẢNG 5: refresh_tokens (JWT rotation) ==========
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ========== INDEXES ==========
CREATE INDEX IF NOT EXISTS idx_studies_patient       ON studies(patient_id);
CREATE INDEX IF NOT EXISTS idx_studies_date          ON studies(study_date);
CREATE INDEX IF NOT EXISTS idx_studies_status        ON studies(status);
CREATE INDEX IF NOT EXISTS idx_users_linked_patient  ON users(linked_patient_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user   ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- pgvector: IVFFlat index cho tìm kiếm vector nhanh (ANN)
-- lists = 10 phù hợp cho <1000 documents, tăng lên khi data lớn hơn
-- Cần ít nhất 10 rows đã có embedding trước khi index hoạt động hiệu quả
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_reports_embedding') THEN
        -- Chỉ tạo index khi đã có đủ data (tránh lỗi khi bảng rỗng)
        IF (SELECT COUNT(*) FROM diagnostic_reports WHERE embedding IS NOT NULL) >= 10 THEN
            CREATE INDEX idx_reports_embedding
                ON diagnostic_reports USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 10);
            RAISE NOTICE 'Created IVFFlat index on diagnostic_reports.embedding';
        ELSE
            RAISE NOTICE 'Skipped IVFFlat index: need >= 10 rows with embedding';
        END IF;
    END IF;
END $$;
