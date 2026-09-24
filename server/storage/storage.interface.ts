/**
 * Storage Service Abstraction for MuneerDev Platform.
 * 
 * Reusable across:
 * - Blogs (Article hero banners, inline markdown figures, author avatars)
 * - Projects (Architecture diagrams, screenshots, case study thumbnails)
 * - Services (Service capability diagrams, deck previews)
 * - Resources (Whitepapers, clinical guides, technical schematics)
 * - Products (System snapshots, blueprints)
 * 
 * Provides a provider-agnostic interface supporting:
 * - Local filesystem storage (with configurable upload directory)
 * - Supabase Cloud Storage (auto-activated when Supabase credentials exist)
 * - Future providers (AWS S3, Cloudflare R2, Google Cloud Storage)
 */

export type StorageEntityType = 'blogs' | 'projects' | 'services' | 'resources' | 'products' | 'general';

export interface StorageUploadOptions {
  /** Sub-folder or domain context: 'blogs' | 'projects' | 'services' | etc. */
  entityType?: StorageEntityType;
  /** Custom entity ID for grouped organization (e.g. articleId, projectId) */
  entityId?: string;
  /** Custom destination path or filename prefix */
  filename?: string;
  /** MIME type of file */
  contentType?: string;
  /** Storage bucket name (defaults to 'muneerdev-media' or provider default) */
  bucket?: string;
  /** Optional metadata tags */
  metadata?: Record<string, string>;
  /** Whether the file is publicly readable (default: true) */
  isPublic?: boolean;
}

export interface StorageUploadResult {
  /** Unique storage reference path / key (e.g. 'blogs/art-123/banner.webp') */
  path: string;
  /** Accessible public URL */
  url: string;
  /** Active storage provider identifier */
  provider: 'supabase' | 'local' | 's3' | 'r2';
  /** Original or cleaned filename */
  filename: string;
  /** MIME type */
  contentType: string;
  /** Size in bytes */
  size: number;
  /** Bucket name where stored */
  bucket: string;
}

export interface StorageSignedUrlOptions {
  /** Expiration time in seconds (default: 3600 = 1 hour) */
  expiresIn?: number;
  /** Force browser download with given filename */
  download?: boolean | string;
}

export interface IStorageProvider {
  readonly name: 'supabase' | 'local' | 's3' | 'r2';

  /**
   * Uploads a file buffer or stream.
   */
  upload(
    fileBuffer: Buffer,
    filename: string,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult>;

  /**
   * Deletes a file by its storage path or filename.
   */
  delete(path: string, bucket?: string): Promise<boolean>;

  /**
   * Resolves the public URL for a storage path.
   */
  getPublicUrl(path: string, bucket?: string): string;

  /**
   * Generates a temporary signed URL for private assets.
   */
  getSignedUrl(
    path: string,
    options?: StorageSignedUrlOptions,
    bucket?: string
  ): Promise<string>;

  /**
   * Replaces an existing file at path with new content.
   */
  replace(
    path: string,
    fileBuffer: Buffer,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult>;

  /**
   * Checks if a file exists.
   */
  exists?(path: string, bucket?: string): Promise<boolean>;
}
