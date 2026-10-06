CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    razao_social TEXT NOT NULL,
    data_inicio_atividade DATE,
    cep VARCHAR(8),
    uf VARCHAR(2),
    municipio TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quarantine (
    id BIGSERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    row_number INTEGER,
    raw_line JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION upsert_empresas(p_rows JSONB)
RETURNS TABLE(inserted_count INTEGER, updated_count INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    row_data JSONB;
    was_existing BOOLEAN;
BEGIN
    inserted_count := 0;
    updated_count := 0;

    FOR row_data IN SELECT value FROM jsonb_array_elements(p_rows)
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM empresas
            WHERE cnpj = row_data->>'cnpj'
        ) INTO was_existing;

        INSERT INTO empresas (
            cnpj, razao_social, data_inicio_atividade, cep, uf, municipio
        )
        VALUES (
            row_data->>'cnpj',
            row_data->>'razao_social',
            NULLIF(row_data->>'data_inicio_atividade', '')::DATE,
            row_data->>'cep',
            row_data->>'uf',
            row_data->>'municipio'
        )
        ON CONFLICT (cnpj)
        DO UPDATE SET
            razao_social = EXCLUDED.razao_social,
            data_inicio_atividade = EXCLUDED.data_inicio_atividade,
            cep = EXCLUDED.cep,
            uf = EXCLUDED.uf,
            municipio = EXCLUDED.municipio,
            updated_at = NOW();

        IF was_existing THEN
            updated_count := updated_count + 1;
        ELSE
            inserted_count := inserted_count + 1;
        END IF;
    END LOOP;

    RETURN NEXT;
END;
$$;
