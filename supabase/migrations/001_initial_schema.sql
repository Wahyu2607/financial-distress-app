-- ==============================================================================
-- SUPABASE POSTGRESQL MIGRATION: SISTEM AUTENTIKASI & MANAJEMEN PENGGUNA
-- Project: Financial Distress Prediction System
-- ==============================================================================

-- 1. Pastikan ekstensi UUID tersedia
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. TABEL PROFIL PENGGUNA (public.profiles)
-- Terhubung langsung ke auth.users via foreign key UUID
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    phone_number TEXT DEFAULT '',
    institution TEXT DEFAULT '',
    user_type TEXT DEFAULT 'Pekerja / Profesional',
    position TEXT DEFAULT '',
    city TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    avatar_data TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indeks untuk pencarian dan filter cepat
CREATE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles(username);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_status ON public.profiles(status);

-- ==============================================================================
-- 3. TABEL RIWAYAT PREDIKSI FINANCIAL DISTRESS (public.predictions)
-- Terhubung ke auth.users agar tiap analisis terlacak ke pemiliknya
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.predictions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    username TEXT NOT NULL,
    company TEXT NOT NULL,
    ticker TEXT NOT NULL,
    year INTEGER NOT NULL,
    z_score DOUBLE PRECISION,
    z_cls TEXT,
    mda_score DOUBLE PRECISION,
    mda_cls TEXT,
    xgb_prob DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON public.predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON public.predictions(timestamp DESC);

-- ==============================================================================
-- 4. FUNCTION & TRIGGER: AUTO CREATE PROFILE SAAT REGISTRASI SUPABASE AUTH
-- Menetapkan role 'user' dan status 'active' secara default dari sisi database
-- Mencegah manipulasi role menjadi 'admin' saat registrasi publik
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_full_name TEXT;
    v_username TEXT;
    v_base_username TEXT;
    v_clean_username TEXT;
    v_final_username TEXT;
    v_counter INT := 0;
BEGIN
    -- Ambil metadata dari pendaftaran
    v_full_name := COALESCE(NULLIF(TRIM(NEW.raw_user_meta_data->>'full_name'), ''), 'Pengguna Baru');
    v_base_username := COALESCE(NULLIF(TRIM(NEW.raw_user_meta_data->>'username'), ''), split_part(NEW.email, '@', 1));
    
    -- Bersihkan username (hanya huruf, angka, underscore)
    v_clean_username := lower(regexp_replace(v_base_username, '[^a-zA-Z0-9_]', '', 'g'));
    IF v_clean_username = '' THEN
        v_clean_username := 'user';
    END IF;

    -- Cegah penggunaan kata terlarang sebagai username
    IF v_clean_username IN ('admin', 'administrator', 'root', 'superuser') THEN
        v_clean_username := 'user_' || substr(md5(random()::text), 1, 6);
    END IF;

    -- Jamin keunikan username
    v_final_username := v_clean_username;
    WHILE EXISTS (SELECT 1 FROM public.profiles WHERE username = v_final_username) LOOP
        v_counter := v_counter + 1;
        v_final_username := v_clean_username || '_' || v_counter;
    END LOOP;

    -- Insert ke profiles dengan role 'user' & status 'active' yang MUTLAK
    INSERT INTO public.profiles (
        id,
        full_name,
        username,
        email,
        role,
        status,
        institution,
        created_at,
        updated_at
    ) VALUES (
        NEW.id,
        v_full_name,
        v_final_username,
        LOWER(TRIM(NEW.email)),
        'user', -- SELALU default 'user', abaikan metadata apapun dari client
        'active',
        COALESCE(NEW.raw_user_meta_data->>'institution', ''),
        timezone('utc'::text, now()),
        timezone('utc'::text, now())
    );

    RETURN NEW;
END;
$$;

-- Pasang trigger pada tabel auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- 5. FUNCTION & TRIGGER: AUTO UPDATE TIMESTAMP updated_at
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- ==============================================================================
-- 6. FUNCTION HELPER UNTUK CEK APAKAH USER ADALAH ADMIN AKTIF
-- Digunakan dalam RLS policies dengan SECURITY DEFINER
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.is_admin(user_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles
        WHERE id = user_id
          AND role = 'admin'
          AND status = 'active'
    );
$$;

-- ==============================================================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- Menerapkan prinsip least-privilege secara ketat
-- ==============================================================================

-- Aktifkan RLS pada kedua tabel
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- A. Kebijakan RLS untuk public.profiles
-- ------------------------------------------------------------------------------

-- 1. Pengguna dapat membaca profil mereka sendiri ATAU Admin dapat membaca semua profil
DROP POLICY IF EXISTS "profiles_select_policy" ON public.profiles;
CREATE POLICY "profiles_select_policy" ON public.profiles
    FOR SELECT
    USING (
        auth.uid() = id
        OR public.is_admin(auth.uid())
    );

-- 2. Pengguna HANYA dapat memperbarui profil miliknya sendiri
-- Catatan: Pengguna biasa TIDAK BOLEH mengubah role atau status mereka sendiri
DROP POLICY IF EXISTS "profiles_user_update_policy" ON public.profiles;
CREATE POLICY "profiles_user_update_policy" ON public.profiles
    FOR UPDATE
    USING (
        auth.uid() = id
        OR public.is_admin(auth.uid())
    )
    WITH CHECK (
        -- Jika user biasa, role dan status tidak boleh berbeda dari sebelumnya
        (
            auth.uid() = id
            AND role = (SELECT p.role FROM public.profiles p WHERE p.id = auth.uid())
            AND status = (SELECT p.status FROM public.profiles p WHERE p.id = auth.uid())
        )
        OR public.is_admin(auth.uid())
    );

-- ------------------------------------------------------------------------------
-- B. Kebijakan RLS untuk public.predictions
-- ------------------------------------------------------------------------------

-- 1. Pengguna dapat membaca riwayat prediksi miliknya sendiri ATAU Admin membaca semua
DROP POLICY IF EXISTS "predictions_select_policy" ON public.predictions;
CREATE POLICY "predictions_select_policy" ON public.predictions
    FOR SELECT
    USING (
        auth.uid() = user_id
        OR public.is_admin(auth.uid())
    );

-- 2. Pengguna terautentikasi dapat menyimpan prediksi
DROP POLICY IF EXISTS "predictions_insert_policy" ON public.predictions;
CREATE POLICY "predictions_insert_policy" ON public.predictions
    FOR INSERT
    WITH CHECK (
        auth.uid() IS NOT NULL
        AND (auth.uid() = user_id OR user_id IS NULL)
    );

-- 3. HANYA Admin atau pemilik prediksi yang dapat menghapus riwayat
DROP POLICY IF EXISTS "predictions_delete_policy" ON public.predictions;
CREATE POLICY "predictions_delete_policy" ON public.predictions
    FOR DELETE
    USING (
        auth.uid() = user_id
        OR public.is_admin(auth.uid())
    );
