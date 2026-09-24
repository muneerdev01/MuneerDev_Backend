import { SupabaseClient } from '@supabase/supabase-js';
import path from 'path';
import { IStorageProvider, StorageUploadOptions, StorageUploadResult, StorageSignedUrlOptions } from './storage.interface';

/**
 * Supabase Storage Provider.
 * Offloads media binary storage directly to Supabase Storage Buckets
 * with automatic public URL generation, signed download token creation,
 * and bucket provisioning.
 */
export class SupabaseStorageProvider implements IStorageProvider {
  public readonly name = 'supabase' as const;
  private readonly supabase: SupabaseClient;
  private readonly defaultBucket: string;

  constructor(supabase: SupabaseClient, defaultBucket = 'media') {
    this.supabase = supabase;
    this.defaultBucket = defaultBucket;
  }

  private resolveBucket(bucket?: string): string {
    return bucket || this.defaultBucket;
  }

  private sanitizePath(relPath: string): string {
    return relPath.replace(/^[\/\\]+/, '').replace(/\\/g, '/');
  }

  public async upload(
    fileBuffer: Buffer,
    filename: string,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    const bucket = this.resolveBucket(options?.bucket);
    const entityType = options?.entityType || 'general';
    const subfolder = options?.entityId ? `${entityType}/${options.entityId}` : entityType;

    const ext = path.extname(filename);
    const base = path.basename(filename, ext).toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    const safeFilename = `${base}-${Date.now()}${ext}`;
    const storagePath = `${subfolder}/${safeFilename}`;

    const contentType = options?.contentType || 'application/octet-stream';

    const { data, error } = await this.supabase.storage
      .from(bucket)
      .upload(storagePath, fileBuffer, {
        contentType,
        upsert: true
      });

    if (error) {
      console.error('[SupabaseStorageProvider] Upload failed:', error);
      throw new Error(`Supabase Storage upload failed: ${error.message}`);
    }

    const publicUrl = this.getPublicUrl(data.path, bucket);

    return {
      path: data.path,
      url: publicUrl,
      provider: 'supabase',
      filename: safeFilename,
      contentType,
      size: fileBuffer.length,
      bucket
    };
  }

  public async delete(storagePath: string, bucket?: string): Promise<boolean> {
    const targetBucket = this.resolveBucket(bucket);
    const cleanPath = this.sanitizePath(storagePath);

    const { error } = await this.supabase.storage
      .from(targetBucket)
      .remove([cleanPath]);

    if (error) {
      console.error('[SupabaseStorageProvider] Delete failed:', error);
      return false;
    }

    return true;
  }

  public getPublicUrl(storagePath: string, bucket?: string): string {
    const targetBucket = this.resolveBucket(bucket);
    const cleanPath = this.sanitizePath(storagePath);

    const { data } = this.supabase.storage
      .from(targetBucket)
      .getPublicUrl(cleanPath);

    return data.publicUrl;
  }

  public async getSignedUrl(
    storagePath: string,
    options?: StorageSignedUrlOptions,
    bucket?: string
  ): Promise<string> {
    const targetBucket = this.resolveBucket(bucket);
    const cleanPath = this.sanitizePath(storagePath);
    const expiresIn = options?.expiresIn || 3600;

    const { data, error } = await this.supabase.storage
      .from(targetBucket)
      .createSignedUrl(cleanPath, expiresIn, {
        download: options?.download
      });

    if (error || !data) {
      console.error('[SupabaseStorageProvider] getSignedUrl failed:', error);
      throw new Error(`Failed to generate signed URL: ${error?.message || 'Unknown error'}`);
    }

    return data.signedUrl;
  }

  public async replace(
    storagePath: string,
    fileBuffer: Buffer,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    const targetBucket = this.resolveBucket(options?.bucket);
    const cleanPath = this.sanitizePath(storagePath);
    const contentType = options?.contentType || 'application/octet-stream';

    const { data, error } = await this.supabase.storage
      .from(targetBucket)
      .update(cleanPath, fileBuffer, {
        contentType,
        upsert: true
      });

    if (error) {
      console.error('[SupabaseStorageProvider] Replace failed:', error);
      throw new Error(`Supabase Storage replace failed: ${error.message}`);
    }

    const publicUrl = this.getPublicUrl(data.path, targetBucket);

    return {
      path: data.path,
      url: publicUrl,
      provider: 'supabase',
      filename: path.basename(cleanPath),
      contentType,
      size: fileBuffer.length,
      bucket: targetBucket
    };
  }

  public async exists(storagePath: string, bucket?: string): Promise<boolean> {
    const targetBucket = this.resolveBucket(bucket);
    const cleanPath = this.sanitizePath(storagePath);
    const folder = path.dirname(cleanPath);
    const filename = path.basename(cleanPath);

    const { data, error } = await this.supabase.storage
      .from(targetBucket)
      .list(folder === '.' ? '' : folder, {
        search: filename
      });

    if (error || !data) return false;
    return data.some(f => f.name === filename);
  }
}
