-- Apply once to databases created from the earlier schema.sql policy set.
-- All writes and sensitive reads go through the backend's server-side service
-- role. Normal Supabase-authenticated users must not inherit admin access.
begin;

drop policy if exists "Admin full access articles" on public.articles;
create policy "Admin full access articles" on public.articles
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access categories" on public.categories;
create policy "Admin full access categories" on public.categories
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access tags" on public.tags;
create policy "Admin full access tags" on public.tags
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access relationships" on public.content_relationships;
create policy "Admin full access relationships" on public.content_relationships
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access media assets" on public.media_assets;
create policy "Admin full access media assets" on public.media_assets
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access media references" on public.media_references;
create policy "Admin full access media references" on public.media_references
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access projects" on public.projects;
create policy "Admin full access projects" on public.projects
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access services" on public.services;
create policy "Admin full access services" on public.services
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access products" on public.products;
create policy "Admin full access products" on public.products
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access customers" on public.customers;
create policy "Admin full access customers" on public.customers
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access leads" on public.leads;
create policy "Admin full access leads" on public.leads
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access orders" on public.orders;
create policy "Admin full access orders" on public.orders
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access subscriptions" on public.subscriptions;
create policy "Admin full access subscriptions" on public.subscriptions
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access licenses" on public.licenses;
create policy "Admin full access licenses" on public.licenses
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access audit logs" on public.audit_logs;
create policy "Admin full access audit logs" on public.audit_logs
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Admin full access slug redirects" on public.slug_redirects;
create policy "Admin full access slug redirects" on public.slug_redirects
  for all using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

commit;
