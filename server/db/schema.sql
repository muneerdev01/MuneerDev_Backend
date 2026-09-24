-- ============================================================================
-- MUNEERDEV UNIFIED ENTERPRISE DATABASE SCHEMA (Supabase / PostgreSQL)
-- Architecture: Multi-module content engine, polymorphic relationships,
-- media asset registry, commercialization, and audit governance.
-- ============================================================================

-- Enable required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- Enum Types
do $$ begin
  create type entity_type_enum as enum (
    'article', 'project', 'service', 'resource', 'product', 
    'author', 'customer', 'order', 'lead', 'general'
  );
exception
  when duplicate_object then null;
end $$;

do $$ begin
  create type blog_type_enum as enum ('TECH', 'HEALTHCARE_MEDICINE');
exception
  when duplicate_object then null;
end $$;

do $$ begin
  create type publication_status_enum as enum ('draft', 'published', 'archived');
exception
  when duplicate_object then null;
end $$;

do $$ begin
  create type relationship_type_enum as enum (
    'related', 'showcase', 'prerequisite', 'documentation', 
    'upsell', 'case_study', 'reference'
  );
exception
  when duplicate_object then null;
end $$;

-- ----------------------------------------------------------------------------
-- 1. TAXONOMY: CATEGORIES & TAGS
-- ----------------------------------------------------------------------------
create table if not exists public.categories (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  name text not null,
  description text,
  entity_type text not null default 'article',
  blog_type text check (blog_type in ('TECH', 'HEALTHCARE_MEDICINE')),
  parent_id text references public.categories(id) on delete set null,
  display_order integer default 0,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.tags (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  name text not null,
  entity_type text not null default 'article',
  blog_type text check (blog_type in ('TECH', 'HEALTHCARE_MEDICINE')),
  created_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.entity_tags (
  id text primary key default gen_random_uuid()::text,
  entity_type text not null,
  entity_id text not null,
  tag_id text not null references public.tags(id) on delete cascade,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  unique(entity_type, entity_id, tag_id)
);

-- ----------------------------------------------------------------------------
-- 2. CONTENT ENGINE: ARTICLES & REVISIONS
-- ----------------------------------------------------------------------------
create table if not exists public.articles (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  title text not null,
  excerpt text not null,
  content text not null,
  blog_type text not null default 'TECH' check (blog_type in ('TECH', 'HEALTHCARE_MEDICINE')),
  category_id text references public.categories(id) on delete set null,
  status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
  reading_time integer default 5,
  view_count integer default 0,
  featured boolean default false,
  seo_title text,
  seo_description text,
  canonical_url text,
  og_image text,
  no_index boolean default false,
  author jsonb default '{"name": "Muneer", "title": "Principal Systems Architect", "avatar": ""}'::jsonb,
  table_of_contents jsonb default '[]'::jsonb,
  "references" jsonb default '[]'::jsonb,
  published_at timestamptz,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.article_revisions (
  id text primary key default gen_random_uuid()::text,
  article_id text not null references public.articles(id) on delete cascade,
  title text not null,
  content text not null,
  excerpt text not null,
  created_by text default 'admin',
  created_at timestamptz default timezone('utc'::text, now()) not null
);

-- ----------------------------------------------------------------------------
-- 3. POLYMORPHIC CONTENT RELATIONSHIPS
-- Connects any content entity (article, project, service, resource, product)
-- ----------------------------------------------------------------------------
create table if not exists public.content_relationships (
  id text primary key default gen_random_uuid()::text,
  source_type text not null,
  source_id text not null,
  target_type text not null,
  target_id text not null,
  relationship_type text not null default 'related',
  display_order integer default 0,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  unique(source_type, source_id, target_type, target_id, relationship_type)
);

-- ----------------------------------------------------------------------------
-- 4. MEDIA REGISTRY & USAGE REFERENCES
-- ----------------------------------------------------------------------------
create table if not exists public.media_assets (
  id text primary key default gen_random_uuid()::text,
  file_name text not null,
  original_name text not null,
  url text not null,
  storage_path text,
  bucket_name text,
  mime_type text not null,
  size_bytes integer not null,
  width integer,
  height integer,
  alt_text text default '',
  caption text,
  created_by text default 'admin',
  created_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.media_references (
  id text primary key default gen_random_uuid()::text,
  media_id text not null references public.media_assets(id) on delete cascade,
  entity_type text not null,
  entity_id text not null,
  field_name text not null default 'featured_image',
  display_order integer default 0,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  unique(media_id, entity_type, entity_id, field_name)
);

-- ----------------------------------------------------------------------------
-- 5. FUTURE EXTENSIBLE PLATFORM MODULES
-- ----------------------------------------------------------------------------

-- Projects (Engineering Portfolio & Deployments)
create table if not exists public.projects (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  title text not null,
  subtitle text not null,
  description text not null,
  category_id text references public.categories(id) on delete set null,
  status text not null default 'active' check (status in ('active', 'archived', 'in_development')),
  featured boolean default false,
  tech_stack text[] default '{}',
  live_url text,
  github_url text,
  architecture_diagram_url text,
  metrics jsonb default '[]'::jsonb,
  featured_image text,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Services (Advisory & Consulting Offerings)
create table if not exists public.services (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  title text not null,
  headline text not null,
  description text not null,
  deliverables text[] default '{}',
  category_id text references public.categories(id) on delete set null,
  pricing_model text not null default 'Fixed Scope / Retainer',
  target_audience text[] default '{}',
  status text not null default 'active' check (status in ('active', 'inactive')),
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Resources (Technical Whitepapers, Clinical Guides, Code Blueprints)
create table if not exists public.resources (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  title text not null,
  description text not null,
  resource_type text not null default 'whitepaper',
  download_url text not null,
  access_tier text not null default 'free' check (access_tier in ('free', 'lead_gated', 'customer_only')),
  downloads_count integer default 0,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Products (Digital Products, APIs, Software Licenses)
create table if not exists public.products (
  id text primary key default gen_random_uuid()::text,
  slug text unique not null,
  title text not null,
  description text not null,
  price_cents integer default 0,
  currency text not null default 'USD',
  product_type text not null default 'saas' check (product_type in ('saas', 'api', 'license', 'consultation')),
  status text not null default 'active' check (status in ('active', 'draft', 'archived')),
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Customers & Leads (CRM, Consultations, Enterprise Contacts)
create table if not exists public.customers (
  id text primary key default gen_random_uuid()::text,
  email text unique not null,
  full_name text not null,
  company text,
  role text,
  notes text,
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.leads (
  id text primary key default gen_random_uuid()::text,
  email text not null,
  name text not null,
  company text,
  source text not null default 'website_contact',
  service_interest text,
  message text,
  status text not null default 'new' check (status in ('new', 'contacted', 'qualified', 'converted', 'closed')),
  created_at timestamptz default timezone('utc'::text, now()) not null,
  updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Orders, Subscriptions & Licenses (Commercialization)
create table if not exists public.orders (
  id text primary key default gen_random_uuid()::text,
  customer_id text references public.customers(id) on delete set null,
  order_number text unique not null,
  status text not null default 'pending' check (status in ('pending', 'completed', 'failed', 'refunded')),
  total_amount_cents integer not null,
  currency text not null default 'USD',
  items jsonb default '[]'::jsonb,
  created_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.subscriptions (
  id text primary key default gen_random_uuid()::text,
  customer_id text references public.customers(id) on delete cascade,
  product_id text references public.products(id) on delete set null,
  status text not null default 'active' check (status in ('active', 'past_due', 'canceled', 'trialing')),
  tier text not null default 'standard',
  current_period_end timestamptz not null,
  created_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.licenses (
  id text primary key default gen_random_uuid()::text,
  customer_id text references public.customers(id) on delete cascade,
  product_id text references public.products(id) on delete cascade,
  license_key text unique not null,
  status text not null default 'active' check (status in ('active', 'revoked', 'expired')),
  max_activations integer default 1,
  activations_count integer default 0,
  expires_at timestamptz,
  created_at timestamptz default timezone('utc'::text, now()) not null
);

-- ----------------------------------------------------------------------------
-- 6. GOVERNANCE: AUDIT LOGS & SLUG REDIRECTS
-- ----------------------------------------------------------------------------
create table if not exists public.audit_logs (
  id text primary key default gen_random_uuid()::text,
  timestamp timestamptz default timezone('utc'::text, now()) not null,
  action text not null,
  entity_type text not null default 'article',
  entity_id text,
  user_email text not null default 'admin',
  details text not null,
  ip_address text
);

create table if not exists public.slug_redirects (
  id text primary key default gen_random_uuid()::text,
  source_slug text unique not null,
  target_slug text not null,
  entity_type text not null default 'article',
  http_status integer default 301 check (http_status in (301, 302, 308)),
  hit_count integer default 0,
  created_at timestamptz default timezone('utc'::text, now()) not null
);

-- ----------------------------------------------------------------------------
-- 7. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
create index if not exists idx_articles_status_pub on public.articles(status, published_at desc);
create index if not exists idx_articles_blog_type on public.articles(blog_type);
create index if not exists idx_articles_category on public.articles(category_id);
create index if not exists idx_articles_slug on public.articles(slug);

create index if not exists idx_categories_slug on public.categories(slug);
create index if not exists idx_categories_entity on public.categories(entity_type);

create index if not exists idx_tags_slug on public.tags(slug);

create index if not exists idx_rel_source on public.content_relationships(source_type, source_id);
create index if not exists idx_rel_target on public.content_relationships(target_type, target_id);

create index if not exists idx_media_ref_entity on public.media_references(entity_type, entity_id);
create index if not exists idx_media_ref_media on public.media_references(media_id);

create index if not exists idx_audit_entity on public.audit_logs(entity_type, entity_id);
create index if not exists idx_audit_time on public.audit_logs(timestamp desc);

create index if not exists idx_redirects_source on public.slug_redirects(source_slug);

-- ----------------------------------------------------------------------------
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
alter table public.articles enable row level security;
alter table public.categories enable row level security;
alter table public.tags enable row level security;
alter table public.entity_tags enable row level security;
alter table public.content_relationships enable row level security;
alter table public.media_assets enable row level security;
alter table public.media_references enable row level security;
alter table public.projects enable row level security;
alter table public.services enable row level security;
alter table public.resources enable row level security;
alter table public.products enable row level security;
alter table public.customers enable row level security;
alter table public.leads enable row level security;
alter table public.orders enable row level security;
alter table public.subscriptions enable row level security;
alter table public.licenses enable row level security;
alter table public.audit_logs enable row level security;
alter table public.slug_redirects enable row level security;

-- Public read policies for published content
create policy "Public read published articles" on public.articles
  for select using (status = 'published');

create policy "Public read categories" on public.categories
  for select using (true);

create policy "Public read tags" on public.tags
  for select using (true);

create policy "Public read entity tags" on public.entity_tags
  for select using (true);

create policy "Public read relationships" on public.content_relationships
  for select using (true);

create policy "Public read media assets" on public.media_assets
  for select using (true);

create policy "Public read media references" on public.media_references
  for select using (true);

create policy "Public read active projects" on public.projects
  for select using (status = 'active');

create policy "Public read active services" on public.services
  for select using (status = 'active');

create policy "Public read active products" on public.products
  for select using (status = 'active');

create policy "Public read resources" on public.resources
  for select using (true);

create policy "Public read slug redirects" on public.slug_redirects
  for select using (true);

-- Admin full access policies (Service role bypasses RLS, but explicit for authenticated admin)
create policy "Admin full access articles" on public.articles
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access categories" on public.categories
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access tags" on public.tags
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access relationships" on public.content_relationships
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access media assets" on public.media_assets
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access media references" on public.media_references
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access projects" on public.projects
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access services" on public.services
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access products" on public.products
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access customers" on public.customers
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access leads" on public.leads
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access orders" on public.orders
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access subscriptions" on public.subscriptions
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access licenses" on public.licenses
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access audit logs" on public.audit_logs
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Admin full access slug redirects" on public.slug_redirects
  for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');
