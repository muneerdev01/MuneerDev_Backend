import fs from 'fs';
import path from 'path';
import { IStorageProvider, StorageUploadOptions, StorageUploadResult, StorageSignedUrlOptions } from './storage.interface';

/**
 * Local Disk Storage Provider.
 * Safely writes files to the local container/server filesystem and serves them via static route.
 * Perfect for development, offline testing, or containerized self-hosting.
 */
export class LocalStorageProvider implements IStorageProvider {
  public readonly name = 'local' as const;
  private readonly baseDir: string;
  private readonly publicPathPrefix: string;

  constructor(options?: { baseDir?: string; publicPathPrefix?: string }) {
    this.baseDir = options?.baseDir || path.join(process.cwd(), 'uploads');
    this.publicPathPrefix = options?.publicPathPrefix || '/uploads';

    if (!fs.existsSync(this.baseDir)) {
      fs.mkdirSync(this.baseDir, { recursive: true });
    }
  }

  private sanitizePath(relPath: string): string {
    // Prevent path traversal
    const normalized = path.normalize(relPath).replace(/^(\.\.[\/\\])+/, '');
    return normalized.replace(/\\/g, '/');
  }

  private resolveFullPath(storagePath: string): string {
    const clean = this.sanitizePath(storagePath);
    return path.join(this.baseDir, clean);
  }

  public async upload(
    fileBuffer: Buffer,
    filename: string,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    const entityType = options?.entityType || 'general';
    const subfolder = options?.entityId ? `${entityType}/${options.entityId}` : entityType;
    const targetDir = path.join(this.baseDir, subfolder);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const ext = path.extname(filename);
    const base = path.basename(filename, ext).toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    const safeFilename = `${base}-${Date.now()}${ext}`;
    const relativePath = `${subfolder}/${safeFilename}`;
    const destinationPath = path.join(this.baseDir, relativePath);

    await fs.promises.writeFile(destinationPath, fileBuffer);

    const publicUrl = this.getPublicUrl(relativePath);

    return {
      path: relativePath,
      url: publicUrl,
      provider: 'local',
      filename: safeFilename,
      contentType: options?.contentType || 'application/octet-stream',
      size: fileBuffer.length,
      bucket: options?.bucket || 'local'
    };
  }

  public async delete(storagePath: string): Promise<boolean> {
    try {
      // Support path whether it starts with /uploads/ or direct relative path
      const cleanPath = storagePath.replace(/^\/?uploads\//, '');
      const fullPath = this.resolveFullPath(cleanPath);

      if (fs.existsSync(fullPath)) {
        await fs.promises.unlink(fullPath);
        return true;
      }
      return false;
    } catch (err) {
      console.error('[LocalStorageProvider] Delete error:', err);
      return false;
    }
  }

  public getPublicUrl(storagePath: string): string {
    const cleanPath = this.sanitizePath(storagePath.replace(/^\/?uploads\//, ''));
    return `${this.publicPathPrefix}/${cleanPath}`;
  }

  public async getSignedUrl(
    storagePath: string,
    _options?: StorageSignedUrlOptions
  ): Promise<string> {
    // For local storage, the public static URL serves as the URL
    return this.getPublicUrl(storagePath);
  }

  public async replace(
    storagePath: string,
    fileBuffer: Buffer,
    options?: StorageUploadOptions
  ): Promise<StorageUploadResult> {
    const cleanPath = this.sanitizePath(storagePath.replace(/^\/?uploads\//, ''));
    const fullPath = this.resolveFullPath(cleanPath);
    const dir = path.dirname(fullPath);

    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    await fs.promises.writeFile(fullPath, fileBuffer);

    return {
      path: cleanPath,
      url: this.getPublicUrl(cleanPath),
      provider: 'local',
      filename: path.basename(cleanPath),
      contentType: options?.contentType || 'application/octet-stream',
      size: fileBuffer.length,
      bucket: options?.bucket || 'local'
    };
  }

  public async exists(storagePath: string): Promise<boolean> {
    const cleanPath = storagePath.replace(/^\/?uploads\//, '');
    return fs.existsSync(this.resolveFullPath(cleanPath));
  }
}
