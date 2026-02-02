-- Supabase seed (sesuai project pds) - SKEMA + POLICY SAJA
--
-- Tujuan file ini adalah memastikan Supabase punya tabel dengan nama & kolom yang dipakai kode:
--   - src/supabase_client.py (default table: inflasi, bi_7day_rr)
--   - src/utils.py / src/bi_data.py (membaca data untuk UI)
--
-- Penting:
-- - File ini TIDAK mengisi data, supaya tidak ada angka berdasarkan asumsi.
-- - Untuk data aktual, isi tabel via import CSV/Excel (atau gunakan generator seed_actual.sql dari data/).

begin;

-- =========================
-- 1) TABEL INFLASI
-- =========================
create table if not exists public.inflasi (
  provinsi text not null,
  tahun int not null,
  bulan int not null check (bulan between 1 and 12),
  inflasi numeric not null,
  constraint inflasi_unique unique (provinsi, tahun, bulan)
);

create index if not exists inflasi_tahun_bulan_idx on public.inflasi (tahun, bulan);
create index if not exists inflasi_provinsi_idx on public.inflasi (provinsi);

alter table public.inflasi enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'inflasi'
      and policyname = 'Public read inflasi'
  ) then
    create policy "Public read inflasi"
      on public.inflasi
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;


-- =========================
-- 2) TABEL BI-7DAY-RR
-- =========================
create table if not exists public.bi_7day_rr (
  tanggal date not null,
  bi_7day_rr numeric not null,
  constraint bi_7day_rr_unique unique (tanggal)
);

create index if not exists bi_7day_rr_tanggal_idx on public.bi_7day_rr (tanggal);

alter table public.bi_7day_rr enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'bi_7day_rr'
      and policyname = 'Public read BI-7Day-RR'
  ) then
    create policy "Public read BI-7Day-RR"
      on public.bi_7day_rr
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;


-- =========================
-- 3) TABEL KURS JISDOR
-- =========================
create table if not exists public.kurs_jisdor (
  tanggal date not null,
  kurs numeric not null,
  constraint kurs_jisdor_unique unique (tanggal)
);

create index if not exists kurs_jisdor_tanggal_idx on public.kurs_jisdor (tanggal);

alter table public.kurs_jisdor enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'kurs_jisdor'
      and policyname = 'Public read kurs_jisdor'
  ) then
    create policy "Public read kurs_jisdor"
      on public.kurs_jisdor
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

commit;
