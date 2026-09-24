import { SupabaseClient } from '@supabase/supabase-js';
import {
  IStorageProvider,
  StorageUploadOptions,
  StorageUploadResult,
  StorageSignedUrlOptions,
  StorageEntityType
} from './storage.interface';
import { LocalStorageProvider } from './local.provider';
import { SupabaseStorageProvider } from './supabase.provider';

/**
 * Unified Storage Service.
 * Single entry point for all media and asset persistence in MuneerDev Platform.
 * 
 * Future systems (Projects, Blogs, Services, Resources, Products) consume this service
 * without knowing or caring whether the backend is Supabase Storage, Local Filesystem, AWS S3, or R2.
 */
export class StorageService {
  private static instance: StorageService;
  private provider: IStorageProvider;
  private localFallbackProvider: LocalStorageProvider;
  private defaultBucket = 'media';

  private constructor() {
    this.localFallbackProvider = new LocalStorageProvider();
    this.provider = this.localFallbackProvider;
  }

  public static getInstance(): StorageService {
    if (!StorageService.instance) {
      StorageService.instance = new StorageService();
    }
    return StorageService.instance;
  }

  /**
   * Initializes or upgrades the storage provider based on runtime environment.
   * If Supabase client is available, activates Supabase Storage.
   * Otherwise smoothly uses local disk storage.
   */
  public initialize(supabaseClient?: SupabaseClient | null, bucketName = 'media') {
    this.defaultBucket = bucketName;

    if (supabaseClient) {
      console.log(`[StorageService] Activating Supabase Storage Provider (Bucket: "${bucketName}")`);
      this.provider = new SupabaseStorageProvider(supabaseClient, bucketName);
    } else {
      console.log('[StorageService] Supabase not configured. Using LocalStorageProvider.');
      this.provider = this.localFallbackProvider;
    }
  }

  /**
   * Set custom provider at runtime (e.g. S3, Cloudflare R2).
   */
  public setProvider(customProvider: IStorageProvider) {
    console.log(`[StorageService] Provider switched to: ${customProvider.name}`);
    this.provider = customProvider;
  }

  /**
   * Returns current active provider info.
   */
  public getActiveProviderName(): string {
    return this.provider.name;
  }

  /**
   * Upload an asset for any domain entity (blogs, projects, services, resources, products).
   */
  public async upload(
    fileBuffer: Buffer,
    filename: string,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    try {
      return await this.provider.upload(fileBuffer, filename, {
        bucket: this.defaultBucket,
        ...options
      });
    } catch (err) {
      // If remote provider fails and it wasn't already local, fallback to local disk
      if (this.provider.name !== 'local') {
        console.warn(`[StorageService] ${this.provider.name} upload failed. Falling back to local disk storage...`, err);
        return await this.localFallbackProvider.upload(fileBuffer, filename, {
          bucket: 'local',
          ...options
        });
      }
      throw err;
    }
  }

  /**
   * Delete an asset by its storage path or filename.
   */
  public async delete(storagePath: string, bucket?: string): Promise<boolean> {
    const targetBucket = bucket || this.defaultBucket;
    const deleted = await this.provider.delete(storagePath, targetBucket);

    // Also clean up local file if it was ever copied there
    if (this.provider.name !== 'local') {
      await this.localFallbackProvider.delete(storagePath).catch(() => {});
    }

    return deleted;
  }

  /**
   * Returns public URL for a given storage path.
   */
  public getPublicUrl(storagePath: string, bucket?: string): string {
    const targetBucket = bucket || this.defaultBucket;
    return this.provider.getPublicUrl(storagePath, targetBucket);
  }

  /**
   * Returns signed URL with expiration for protected or private downloads.
   */
  public async getSignedUrl(
    storagePath: string,
    options?: StorageSignedUrlOptions,
    bucket?: string
  ): Promise<string> {
    const targetBucket = bucket || this.defaultBucket;
    return await this.provider.getSignedUrl(storagePath, options, targetBucket);
  }

  /**
   * Replaces an existing media asset.
   */
  public async replace(
    storagePath: string,
    fileBuffer: Buffer,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    try {
      return await this.provider.replace(storagePath, fileBuffer, {
        bucket: this.defaultBucket,
        ...options
      });
    } catch (err) {
      if (this.provider.name !== 'local') {
        console.warn(`[StorageService] Remote replace failed, trying local fallback...`, err);
        return await this.localFallbackProvider.replace(storagePath, fileBuffer, options);
      }
      throw err;
    }
  }

  // --- Domain-Specific Convenience Methods ---

  /**
   * Upload blog article asset (featured image, inline figure)
   */
  public async uploadBlogMedia(
    fileBuffer: Buffer,
    filename: string,
    articleId?: string,
    contentType?: string
  ) {
    return this.upload(fileBuffer, filename, {
      entityType: 'blogs',
      entityId: articleId,
      contentType
    });
  }

  /**
   * Upload project media (architecture diagram, mockup)
   */
  public async uploadProjectMedia(
    fileBuffer: Buffer,
    filename: string,
    projectId?: string,
    contentType?: string
  ) {
    return this.upload(fileBuffer, filename, {
      entityType: 'projects',
      entityId: projectId,
      contentType
    });
  }

  /**
   * Upload service media (infographic, workflow chart)
   */
  public async uploadServiceMedia(
    fileBuffer: Buffer,
    filename: string,
    serviceId?: string,
    contentType?: string
  ) {
    return this.upload(fileBuffer, filename, {
      entityType: 'services',
      entityId: serviceId,
      contentType
    });
  }

  /**
   * Upload resource media (PDF whitepapers, technical specifications)
   */
  public async uploadResourceMedia(
    fileBuffer: Buffer,
    filename: string,
    resourceId?: string,
    contentType?: string
  ) {
    return this.upload(fileBuffer, filename, {
      entityType: 'resources',
      entityId: resourceId,
      contentType
    });
  }

  /**
   * Upload product media (UI snapshots, schematics)
   */
  public async uploadProductMedia(
    fileBuffer: Buffer,
    filename: string,
    productId?: string,
    contentType?: string
  ) {
    return this.upload(fileBuffer, filename, {
      entityType: 'products',
      entityId: productId,
      contentType
    });
  }
}

export const storageService = StorageService.getInstance();
