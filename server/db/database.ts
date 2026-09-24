import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { 
  Article, 
  Category, 
  Tag, 
  MediaItem, 
  BlogStats, 
  SlugRedirect, 
  AuditLogEntry, 
  BlogType,
  ContentFormat,
  ArticleStatus
} from '../../src/types/blog';
import { 
  ContentRelationshipRow, 
  MediaReferenceRow, 
  EntityType, 
  RelationshipType 
} from '../../src/types/database';
import { MUNEERDEV_PROJECTS, MUNEERDEV_SERVICES } from '../../src/data/muneerdev-portfolio';
import { storageService } from '../storage/storage.service';

// Utility: Slugify
export function slugify(text: string): string {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/[\s\W-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Utility: Normalize Status to 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export function normalizeStatus(status?: string | null): ArticleStatus {
  if (!status) return 'DRAFT';
  const s = status.toUpperCase().trim();
  if (s === 'PUBLISHED') return 'PUBLISHED';
  if (s === 'ARCHIVED') return 'ARCHIVED';
  return 'DRAFT';
}

// Utility: Normalize Blog Type to 'TECH' | 'HEALTHCARE'
export function normalizeBlogType(type?: string | null): BlogType {
  if (!type) return 'TECH';
  const t = type.toUpperCase().trim();
  if (t === 'HEALTHCARE' || t === 'HEALTHCARE_MEDICINE') return 'HEALTHCARE';
  return 'TECH';
}

// Utility: Normalize Content Format to 'markdown' | 'html' | 'rich_text'
export function normalizeContentFormat(format?: string | null): ContentFormat {
  if (!format) return 'markdown';
  const f = format.toLowerCase().trim();
  if (f === 'html' || f === 'rich_text') return f as ContentFormat;
  return 'markdown';
}

// Utility: Calculate reading time
export function calculateReadingTime(content: string): number {
  if (!content) return 1;
  const wordsPerMinute = 200;
  const wordCount = content.trim().split(/\s+/).length;
  return Math.max(1, Math.ceil(wordCount / wordsPerMinute));
}

// Utility: Extract table of contents from markdown headings
export function extractTableOfContents(content: string): Array<{ id: string; text: string; level: number }> {
  if (!content) return [];
  const headingRegex = /^(#{2,4})\s+(.+)$/gm;
  const toc: Array<{ id: string; text: string; level: number }> = [];
  let match;

  while ((match = headingRegex.exec(content)) !== null) {
    const level = match[1].length;
    const rawText = match[2].trim();
    const cleanText = rawText.replace(/\*\*|\*|`|\[.*?\]\(.*?\)/g, '').trim();
    const id = slugify(cleanText);
    toc.push({ id, text: cleanText, level });
  }

  return toc;
}

// Default Categories for taxonomy - dynamic database-driven taxonomy
const DEFAULT_CATEGORIES: Category[] = [
  // Initial Tech Categories
  { id: 'cat-nextjs', name: 'Next.js', slug: 'nextjs', blog_type: 'TECH', description: 'Server components, App Router, SSR/SSG, and Next.js optimization' },
  { id: 'cat-react', name: 'React', slug: 'react', blog_type: 'TECH', description: 'React 18+, modern hooks, concurrent features, and state architecture' },
  { id: 'cat-typescript', name: 'TypeScript', slug: 'typescript', blog_type: 'TECH', description: 'Strict typing, advanced generics, and compiler performance' },
  { id: 'cat-javascript', name: 'JavaScript', slug: 'javascript', blog_type: 'TECH', description: 'Modern ECMAScript standards, asynchronous runtimes, and engine internals' },
  { id: 'cat-python', name: 'Python', slug: 'python', blog_type: 'TECH', description: 'Python architecture, type hints, async IO, and scientific libraries' },
  { id: 'cat-fastapi', name: 'FastAPI', slug: 'fastapi', blog_type: 'TECH', description: 'High-performance async Python APIs, Pydantic validation, and OpenAPI' },
  { id: 'cat-ai', name: 'AI', slug: 'ai', blog_type: 'TECH', description: 'Artificial intelligence foundations, models, algorithms, and applications' },
  { id: 'cat-generative-ai', name: 'Generative AI', slug: 'generative-ai', blog_type: 'TECH', description: 'Multimodal generation, prompt pipelines, and foundational models' },
  { id: 'cat-llm', name: 'LLM', slug: 'llm', blog_type: 'TECH', description: 'Large Language Model architectures, fine-tuning, embeddings, and context windows' },
  { id: 'cat-ai-agents', name: 'AI Agents', slug: 'ai-agents', blog_type: 'TECH', description: 'Autonomous agentic loops, tool execution, memory, and orchestration' },
  { id: 'cat-rag', name: 'RAG', slug: 'rag', blog_type: 'TECH', description: 'Retrieval-augmented generation, vector search, chunking, and re-ranking' },
  { id: 'cat-apis', name: 'APIs', slug: 'apis', blog_type: 'TECH', description: 'RESTful systems, GraphQL, gRPC, and API governance' },
  { id: 'cat-saas', name: 'SaaS', slug: 'saas', blog_type: 'TECH', description: 'Software-as-a-service architecture, multi-tenancy, and subscription platforms' },
  { id: 'cat-databases', name: 'Databases', slug: 'databases', blog_type: 'TECH', description: 'PostgreSQL, relational schemas, indexing, and distributed data systems' },
  { id: 'cat-supabase', name: 'Supabase', slug: 'supabase', blog_type: 'TECH', description: 'Supabase PostgreSQL, row-level security (RLS), Edge Functions, and realtime' },
  { id: 'cat-web-development', name: 'Web Development', slug: 'web-development', blog_type: 'TECH', description: 'Full-stack web architecture, standards, responsive UX, and modern web platforms' },
  { id: 'cat-backend', name: 'Backend', slug: 'backend', blog_type: 'TECH', description: 'Distributed servers, microservices, queue systems, and background workers' },
  { id: 'cat-frontend', name: 'Frontend', slug: 'frontend', blog_type: 'TECH', description: 'User interfaces, design systems, client performance, and accessibility' },
  { id: 'cat-deployment', name: 'Deployment', slug: 'deployment', blog_type: 'TECH', description: 'CI/CD pipelines, Docker containers, Cloud Run, and production operations' },
  { id: 'cat-performance', name: 'Performance', slug: 'performance', blog_type: 'TECH', description: 'Latency optimization, bundle analysis, profiling, and caching layers' },
  { id: 'cat-security', name: 'Security', slug: 'security', blog_type: 'TECH', description: 'App security, authentication, OWASP prevention, and cryptography' },

  // Initial Healthcare & Medicine Categories
  { id: 'cat-medicines', name: 'Medicines', slug: 'medicines', blog_type: 'HEALTHCARE', description: 'Clinical therapeutic agents, dosage forms, indications, and formulations' },
  { id: 'cat-pharmacology', name: 'Pharmacology', slug: 'pharmacology', blog_type: 'HEALTHCARE', description: 'Pharmacokinetics, pharmacodynamics, receptor binding, and mechanism of action' },
  { id: 'cat-drug-information', name: 'Drug Information', slug: 'drug-information', blog_type: 'HEALTHCARE', description: 'Comprehensive pharmaceutical monographs, FDA/EMA updates, and clinical guidelines' },
  { id: 'cat-drug-interactions', name: 'Drug Interactions', slug: 'drug-interactions', blog_type: 'HEALTHCARE', description: 'CYP450 metabolism, pharmacokinetic & pharmacodynamic clinical interactions' },
  { id: 'cat-lab-tests', name: 'Lab Tests', slug: 'lab-tests', blog_type: 'HEALTHCARE', description: 'Diagnostic pathology, reference ranges, biomarker interpretation, and hematology' },
  { id: 'cat-diseases-conditions', name: 'Diseases & Conditions', slug: 'diseases-conditions', blog_type: 'HEALTHCARE', description: 'Clinical pathophysiology, diagnosis, staging, and therapeutic management' },
  { id: 'cat-healthcare-technology', name: 'Healthcare Technology', slug: 'healthcare-technology', blog_type: 'HEALTHCARE', description: 'Medical device systems, hospital IT infrastructure, and clinical hardware' },
  { id: 'cat-digital-health', name: 'Digital Health', slug: 'digital-health', blog_type: 'HEALTHCARE', description: 'Telemedicine, EHR/EMR platforms, remote patient monitoring, and FHIR APIs' },
  { id: 'cat-ai-in-healthcare', name: 'AI in Healthcare', slug: 'ai-in-healthcare', blog_type: 'HEALTHCARE', description: 'Clinical decision support systems, diagnostic AI models, and medical NLP' },
  { id: 'cat-pharmaceutical-technology', name: 'Pharmaceutical Technology', slug: 'pharmaceutical-technology', blog_type: 'HEALTHCARE', description: 'Drug delivery mechanisms, nanomedicine, bioequivalence, and manufacturing' },
  { id: 'cat-pakistan-healthcare-context', name: 'Pakistan Healthcare Context', slug: 'pakistan-healthcare-context', blog_type: 'HEALTHCARE', description: 'DRAP regulations, local pharmaceutical market, national disease burden, and health reforms' }
];

// Foundational authentic seed articles (Zero local JSON dependency)
const SEED_ARTICLES: Article[] = [
  {
    id: 'art-tech-node-streams',
    title: 'Architecting High-Throughput Event Streams in Node.js & TypeScript',
    slug: 'architecting-high-throughput-event-streams-nodejs-typescript',
    excerpt: 'A deep dive into backpressure management, memory-efficient buffer chunking, and Server-Sent Events (SSE) for production data streaming.',
    content: `## Introduction to High-Concurrency Streaming

When building real-time data pipelines or high-volume APIs in Node.js, standard buffering can quickly exhaust container memory. Under high concurrency, allocating complete response payloads in V8 heap memory leads to garbage collection stalls and eventual process termination (OOM).

Stream-oriented programming decouples data production from consumption by processing chunks as they arrive.

\`\`\`typescript
import { Transform, TransformCallback } from 'stream';

export class ChunkTransformStream extends Transform {
  private count = 0;

  constructor(options = {}) {
    super({ ...options, objectMode: true });
  }

  _transform(chunk: Buffer, encoding: string, callback: TransformCallback): void {
    this.count++;
    // Process chunk without holding reference to whole dataset
    const processed = Buffer.from(chunk.toString().trim() + '\\n');
    this.push(processed);
    callback();
  }
}
\`\`\`

## Managing Stream Backpressure

Backpressure is the signal a consumer gives to a producer when it cannot keep up with the rate of incoming data. In Node.js, backpressure occurs when the internal buffer reaches its \`highWaterMark\`.

### Key Rules for Backpressure Safety

1. **Check the return value of \`stream.write(chunk)\`**: If it returns \`false\`, pause the upstream source immediately.
2. **Wait for the \`drain\` event**: Only resume writing after the readable side has emptied its buffer.
3. **Prefer \`pipeline()\`**: Always use the native \`stream.promises.pipeline()\` utility over manual event wiring to avoid memory leaks on unexpected stream closure.

\`\`\`typescript
import { pipeline } from 'stream/promises';
import { createReadStream, createWriteStream } from 'fs';

async function copyFileSafely(src: string, dest: string): Promise<void> {
  await pipeline(
    createReadStream(src, { highWaterMark: 64 * 1024 }),
    new ChunkTransformStream(),
    createWriteStream(dest)
  );
}
\`\`\`

## Server-Sent Events (SSE) vs WebSockets

For unidirectional live updates (such as financial tickers, LLM token streaming, or IoT sensor telemetry), Server-Sent Events offer a lightweight HTTP-compliant alternative to WebSockets:

| Characteristic | Server-Sent Events (SSE) | WebSockets |
| :--- | :--- | :--- |
| **Protocol** | Standard HTTP/1.1 or HTTP/2 | ws:// / wss:// upgrade |
| **Reconnection** | Native browser retry handling | Manual reconnection logic required |
| **Proxy Compatibility** | Works seamlessly behind standard CDNs | Often requires sticky sessions & special proxy rules |
| **Direction** | Server-to-Client only | Bi-directional full duplex |

## Conclusion and Recommendations

By respecting Node.js backpressure dynamics and leveraging pipeline abstractions, you can maintain sub-50ms streaming latency without spiking memory utilization even under heavy production load.`,
    content_format: 'markdown',
    blog_type: 'TECH',
    category_id: 'cat-react-ts',
    category: 'React & TypeScript',
    subcategory: 'Backend Architecture',
    tags: ['Node.js', 'TypeScript', 'Streaming', 'Performance', 'Architecture'],
    tag_ids: ['tag-nodejs', 'tag-typescript', 'tag-streaming', 'tag-performance', 'tag-architecture'],
    author: {
      name: 'Muneer',
      title: 'Principal Systems Architect',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
    },
    featured_image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&auto=format&fit=crop&q=80',
    image_alt_text: 'Server racks representing high throughput network event streaming',
    reading_time: 4,
    status: 'PUBLISHED',
    featured: true,
    published_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    seo_title: 'High-Throughput Event Streams in Node.js & TypeScript | MuneerDev',
    seo_description: 'Master backpressure management, memory-safe stream pipelines, and Server-Sent Events (SSE) in Node.js and TypeScript.',
    canonical_url: 'https://muneerdev.com/blog/architecting-high-throughput-event-streams-nodejs-typescript',
    og_image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&auto=format&fit=crop&q=80',
    table_of_contents: [
      { id: 'introduction-to-high-concurrency-streaming', text: 'Introduction to High-Concurrency Streaming', level: 2 },
      { id: 'managing-stream-backpressure', text: 'Managing Stream Backpressure', level: 2 },
      { id: 'server-sent-events-sse-vs-websockets', text: 'Server-Sent Events (SSE) vs WebSockets', level: 2 },
      { id: 'conclusion-and-recommendations', text: 'Conclusion and Recommendations', level: 2 }
    ],
    references: [
      { id: 'ref-1', title: 'Node.js Official Stream Documentation', url: 'https://nodejs.org/api/stream.html', source: 'Node.js Foundation', year: '2024' },
      { id: 'ref-2', title: 'High Performance Browser Networking: Server-Sent Events', url: 'https://hpbn.co/server-sent-events-sse/', source: 'Ilya Grigorik', year: '2023' }
    ],
    created_by: 'muneer',
    updated_by: 'muneer',
    related_articles: [],
    related_projects: [MUNEERDEV_PROJECTS[2]],
    related_services: [MUNEERDEV_SERVICES[0], MUNEERDEV_SERVICES[3]]
  },
  {
    id: 'art-health-pharmacokinetics',
    title: 'Clinical Pharmacokinetics: Bioavailability, Clearance, and Half-Life Principles',
    slug: 'clinical-pharmacokinetics-bioavailability-clearance-half-life',
    excerpt: 'An educational breakdown of how pharmaceuticals are absorbed, distributed, metabolized, and eliminated (ADME) in the human body.',
    content: `## Fundamentals of Pharmacokinetics (ADME)

Pharmacokinetics is quantitatively described as what the body does to a drug, contrasting with pharmacodynamics, which describes what the drug does to the body. Understanding these quantitative principles is vital for clinicians, medical software designers, and clinical informatics engineers building dosage decision-support engines.

The primary framework comprises four distinct phases:
1. **Absorption**: The rate and extent at which the active drug molecule enters systemic circulation.
2. **Distribution**: The reversible transfer of drug between blood plasma and extravascular tissues.
3. **Metabolism**: The enzymatic biotransformation of the parent molecule into active or inactive metabolites (primarily hepatic).
4. **Elimination / Excretion**: The irreversible removal of drug compounds from the organism (primarily renal and biliary).

## Understanding Bioavailability ($F$)

Bioavailability ($F$) represents the fraction of an administered dose that reaches the systemic circulation in unchanged form:

- **Intravenous (IV) administration**: By definition, $F = 1.0$ (100%), because the full dose bypasses gastrointestinal absorption barriers and first-pass hepatic metabolism.
- **Oral (PO) administration**: $F$ is typically $< 1.0$ due to incomplete intestinal absorption, drug degradation in gastric acid, and extensive first-pass metabolism by CYP450 enzymes in the liver.

\`\`\`text
Bioavailability (F) = (AUC_oral / Dose_oral) / (AUC_iv / Dose_iv)
\`\`\`

## Elimination Half-Life ($t_{1/2}$) and Steady-State Kinetics

The elimination half-life ($t_{1/2}$) is the duration required for the plasma concentration of a drug to decrease by 50% during the elimination phase.

### Key Clinical Rules of Thumb
- **Steady State ($C_{ss}$)**: In repeated continuous or intermittent dosing regimens, a therapeutic steady state is achieved after approximately **4 to 5 half-lives**.
- **Washout Period**: Similarly, after discontinuation of a drug, approximately 94% to 97% of the substance is cleared from the systemic circulation after 4 to 5 half-lives.

| Elapsed Half-Lives | Fraction of Steady State Achieved | Fraction of Drug Remaining After Cessation |
| :--- | :--- | :--- |
| **1 half-life** | 50.0% | 50.0% |
| **2 half-lives** | 75.0% | 25.0% |
| **3 half-lives** | 87.5% | 12.5% |
| **4 half-lives** | 93.75% | 6.25% |
| **5 half-lives** | 96.88% | 3.12% |

## Relevance in Digital Health and Clinical Informatics

In modern Electronic Health Records (EHR) and computerized physician order entry (CPOE) platforms, pharmacokinetic algorithms flag critical therapeutic risks, such as:
- Glomerular Filtration Rate (eGFR) dose adjustments for renal-cleared medications.
- Cytochrome P450 competitive enzyme inhibition and induction interactions.
- Narrow therapeutic index (NTI) drug monitoring warnings (e.g., digoxin, lithium, aminoglycosides).

## References and Authoritative Sources

The concepts detailed in this overview reflect standard clinical pharmacology consensus curricula and regulatory drug development guidance documents.`,
    content_format: 'markdown',
    blog_type: 'HEALTHCARE',
    category_id: 'cat-clinical-pharm',
    category: 'Medicines & Pharmacology',
    subcategory: 'Clinical Pharmacology',
    tags: ['Pharmacokinetics', 'Pharmacology', 'Bioavailability', 'Digital Health', 'Clinical Informatics'],
    tag_ids: ['tag-pharmacokinetics', 'tag-pharmacology', 'tag-bioavailability', 'tag-digitalhealth', 'tag-clinicalinformatics'],
    author: {
      name: 'Muneer',
      title: 'Principal Systems Architect',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
    },
    featured_image: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=1200&auto=format&fit=crop&q=80',
    image_alt_text: 'Clinical medication capsules and laboratory vials illustrating pharmacokinetics',
    reading_time: 5,
    status: 'PUBLISHED',
    featured: true,
    published_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    seo_title: 'Clinical Pharmacokinetics: Bioavailability & Half-Life | MuneerDev',
    seo_description: 'Educational guide to clinical pharmacokinetics: ADME pathways, bioavailability (F), clearance calculation, and steady-state kinetics.',
    canonical_url: 'https://muneerdev.com/blog/clinical-pharmacokinetics-bioavailability-clearance-half-life',
    og_image: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=1200&auto=format&fit=crop&q=80',
    table_of_contents: [
      { id: 'fundamentals-of-pharmacokinetics-adme', text: 'Fundamentals of Pharmacokinetics (ADME)', level: 2 },
      { id: 'understanding-bioavailability-f', text: 'Understanding Bioavailability (F)', level: 2 },
      { id: 'elimination-half-life-t_1-2-and-steady-state-kinetics', text: 'Elimination Half-Life and Steady-State Kinetics', level: 2 },
      { id: 'relevance-in-digital-health-and-clinical-informatics', text: 'Relevance in Digital Health and Clinical Informatics', level: 2 },
      { id: 'references-and-authoritative-sources', text: 'References and Authoritative Sources', level: 2 }
    ],
    references: [
      { id: 'ref-1', title: 'Goodman & Gilman\'s: The Pharmacological Basis of Therapeutics (14th Ed)', source: 'McGraw Hill Medical', year: '2023' },
      { id: 'ref-2', title: 'FDA Guidance for Industry: Bioavailability and Bioequivalence Studies', url: 'https://www.fda.gov/regulatory-information/search-fda-guidance-documents', source: 'US Food and Drug Administration', year: '2022' }
    ],
    created_by: 'muneer',
    updated_by: 'muneer',
    related_articles: [],
    related_projects: [MUNEERDEV_PROJECTS[0], MUNEERDEV_PROJECTS[3]],
    related_services: [MUNEERDEV_SERVICES[1]]
  },
  {
    id: 'art-draft-ai-agents',
    title: 'Implementing Strict JSON Schemas for Production AI Agents',
    slug: 'implementing-strict-json-schemas-production-ai-agents',
    excerpt: 'Techniques for enforcing deterministic, type-safe outputs when executing tool calls with Large Language Models.',
    content: `## The Determinism Challenge in LLM Tool Execution

Production AI workflows cannot rely on fuzzy string parsing. When calling internal APIs, writing database records, or initiating financial transactions, agents require strict schema adherence.

\`\`\`typescript
import { z } from 'zod';

export const ToolCallSchema = z.object({
  action: z.enum(['query_patient_record', 'schedule_appointment', 'flag_adverse_reaction']),
  payload: z.record(z.unknown()),
  confidence_score: z.number().min(0).max(1)
});
\`\`\`

## Constrained Decoding vs Prompt Engineering

While system prompts guide model behavior, compiler-level constrained decoding forces the model token sampler to only emit valid transitions matching the context-free grammar (CFG) or JSON schema.

*(Draft article under active authoring)*`,
    content_format: 'markdown',
    blog_type: 'TECH',
    category_id: 'cat-ai-rag',
    category: 'AI & RAG Systems',
    subcategory: 'Tool Calling',
    tags: ['AI Agents', 'JSON Schema', 'TypeScript', 'LLM'],
    tag_ids: ['tag-aiagents', 'tag-jsonschema', 'tag-typescript', 'tag-llm'],
    author: {
      name: 'Muneer',
      title: 'Principal Systems Architect',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
    },
    featured_image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80',
    image_alt_text: 'Abstract neural network graph visualizing structured agent decisions',
    reading_time: 3,
    status: 'DRAFT',
    featured: false,
    published_at: null,
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    updated_at: new Date().toISOString(),
    seo_title: 'Strict JSON Schemas for Production AI Agents | MuneerDev',
    seo_description: 'Enforce deterministic, type-safe outputs for AI agent tool calls with structured JSON schemas and constrained sampling.',
    canonical_url: 'https://muneerdev.com/blog/implementing-strict-json-schemas-production-ai-agents',
    og_image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80',
    table_of_contents: [
      { id: 'the-determinism-challenge-in-llm-tool-execution', text: 'The Determinism Challenge in LLM Tool Execution', level: 2 },
      { id: 'constrained-decoding-vs-prompt-engineering', text: 'Constrained Decoding vs Prompt Engineering', level: 2 }
    ],
    references: [],
    created_by: 'muneer',
    updated_by: 'muneer',
    related_articles: [],
    related_projects: [MUNEERDEV_PROJECTS[1]],
    related_services: [MUNEERDEV_SERVICES[2]]
  }
];

/**
 * Enterprise Database Service with Supabase PostgreSQL integration foundation.
 * 
 * Features:
 * - NO dependence on local JSON files (/data/articles.json, /data/audit.json)
 * - Directly connects to Supabase PostgreSQL when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are configured
 * - Polymorphic content relationships between articles, projects, services, resources, and products
 * - Media assets registry and references
 * - Audit logging and slug redirects
 */
export class DatabaseService {
  private supabase: SupabaseClient | null = null;
  private isSupabaseConfigured = false;

  // In-memory data store for standalone/preview readiness without local JSON files
  private inMemoryArticles: Article[] = [...SEED_ARTICLES];
  private inMemoryCategories: Category[] = [...DEFAULT_CATEGORIES];
  private inMemoryTags: Tag[] = [];
  private inMemoryMedia: MediaItem[] = [];
  private inMemoryRedirects: SlugRedirect[] = [];
  private inMemoryAuditLogs: AuditLogEntry[] = [];
  private inMemoryRelationships: ContentRelationshipRow[] = [];
  private inMemoryMediaReferences: MediaReferenceRow[] = [];

  constructor() {
    this.initSupabase();
    this.inMemoryTags = this.generateTagsFromArticles(this.inMemoryArticles);
  }

  private initSupabase() {
    const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (url && key) {
      try {
        this.supabase = createClient(url, key, {
          auth: { persistSession: false }
        });
        this.isSupabaseConfigured = true;
        console.log(`[Database] Supabase PostgreSQL Client connected: ${url}`);
        storageService.initialize(this.supabase, 'media');
      } catch (err) {
        console.error('[Database] Failed to initialize Supabase client:', err);
        storageService.initialize(null);
      }
    } else {
      console.log('[Database] Supabase PostgreSQL foundation initialized in Standby mode. Connect anytime by declaring SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.');
      storageService.initialize(null);
    }
  }

  public getSupabaseClient(): SupabaseClient | null {
    return this.supabase;
  }

  public isConfigured(): boolean {
    return this.isSupabaseConfigured;
  }

  private generateTagsFromArticles(articles: Article[]): Tag[] {
    const tagCountMap = new Map<string, number>();
    articles.forEach(art => {
      art.tags.forEach(tag => {
        tagCountMap.set(tag, (tagCountMap.get(tag) || 0) + 1);
      });
    });

    return Array.from(tagCountMap.entries()).map(([name, count]) => ({
      id: `tag-${slugify(name)}`,
      name,
      slug: slugify(name),
      count
    }));
  }

  private async logAudit(action: string, entityId?: string, entityTitle?: string, user = 'admin', details?: string) {
    const entry: AuditLogEntry = {
      id: `audit-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      action,
      article_id: entityId,
      article_title: entityTitle,
      timestamp: new Date().toISOString(),
      user,
      details
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('audit_logs').insert([{
          action,
          entity_type: 'article',
          entity_id: entityId,
          user_email: user,
          details: details || `${action} performed on ${entityTitle || entityId}`
        }]);
      } catch (e) {
        console.error('[Database] Supabase audit insert error:', e);
      }
    }

    this.inMemoryAuditLogs.unshift(entry);
    if (this.inMemoryAuditLogs.length > 200) {
      this.inMemoryAuditLogs = this.inMemoryAuditLogs.slice(0, 200);
    }
  }

  // --- Public Blog API ---
  public getPublishedArticles(params: {
    blog_type?: string;
    category?: string;
    tag?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) {
    // Strictly filter published articles - Do not publish DRAFT articles!
    let result = this.inMemoryArticles.filter(a => normalizeStatus(a.status) === 'PUBLISHED');

    if (params.blog_type && params.blog_type !== 'ALL') {
      const targetType = normalizeBlogType(params.blog_type);
      result = result.filter(a => normalizeBlogType(a.blog_type) === targetType);
    }

    if (params.category && params.category !== 'ALL') {
      result = result.filter(a => 
        (a.category_id && a.category_id === params.category) ||
        (a.category && a.category.toLowerCase() === params.category!.toLowerCase()) ||
        (a.category && slugify(a.category) === params.category)
      );
    }

    if (params.tag) {
      result = result.filter(a => 
        a.tags.some(t => t.toLowerCase() === params.tag!.toLowerCase() || slugify(t) === params.tag)
      );
    }

    if (params.search) {
      const q = params.search.toLowerCase().trim();
      result = result.filter(a => 
        a.title.toLowerCase().includes(q) ||
        a.excerpt.toLowerCase().includes(q) ||
        a.tags.some(t => t.toLowerCase().includes(q)) ||
        (a.category && a.category.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => {
      const timeA = a.published_at ? new Date(a.published_at).getTime() : 0;
      const timeB = b.published_at ? new Date(b.published_at).getTime() : 0;
      return timeB - timeA;
    });

    const page = Math.max(1, params.page || 1);
    const limit = Math.max(1, Math.min(50, params.limit || 12));
    const total = result.length;
    const paginated = result.slice((page - 1) * limit, page * limit);

    return {
      articles: paginated,
      pagination: {
        page,
        limit,
        total,
        total_pages: Math.ceil(total / limit)
      }
    };
  }

  public getPublishedArticleBySlug(slug: string): { article: Article | null; redirect?: string; related_articles?: Article[] } {
    const cleanSlug = slug.toLowerCase().trim();
    
    // Check if redirect exists
    const redirect = this.inMemoryRedirects.find(r => r.from_slug.toLowerCase() === cleanSlug);
    if (redirect) {
      return { article: null, redirect: redirect.to_slug };
    }

    // Strictly ensure DRAFT articles are never returned via public slug lookup
    const article = this.inMemoryArticles.find(a => 
      a.slug.toLowerCase() === cleanSlug && normalizeStatus(a.status) === 'PUBLISHED'
    );

    if (!article) {
      return { article: null };
    }

    // Compute related published articles (same category or shared tags, excluding self)
    const related = this.inMemoryArticles.filter(a => 
      a.id !== article.id &&
      normalizeStatus(a.status) === 'PUBLISHED' &&
      (
        (article.category && a.category && a.category.toLowerCase() === article.category.toLowerCase()) ||
        a.tags.some(t => article.tags.includes(t)) ||
        a.blog_type === article.blog_type
      )
    ).slice(0, 3);

    return { article, related_articles: related };
  }

  // --- Admin Blog API ---
  public getAdminArticles(params: {
    status?: string;
    blog_type?: string;
    category?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) {
    let result = [...this.inMemoryArticles];

    if (params.status && params.status !== 'ALL') {
      const targetStatus = normalizeStatus(params.status);
      result = result.filter(a => normalizeStatus(a.status) === targetStatus);
    }

    if (params.blog_type && params.blog_type !== 'ALL') {
      const targetType = normalizeBlogType(params.blog_type);
      result = result.filter(a => normalizeBlogType(a.blog_type) === targetType);
    }

    if (params.category && params.category !== 'ALL') {
      result = result.filter(a => 
        (a.category_id && a.category_id === params.category) ||
        (a.category && a.category.toLowerCase() === params.category!.toLowerCase()) ||
        (a.category && slugify(a.category) === params.category)
      );
    }

    if (params.search) {
      const q = params.search.toLowerCase().trim();
      result = result.filter(a => 
        a.title.toLowerCase().includes(q) ||
        a.slug.toLowerCase().includes(q) ||
        (a.category && a.category.toLowerCase().includes(q)) ||
        a.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

    const page = Math.max(1, params.page || 1);
    const limit = Math.max(1, Math.min(100, params.limit || 20));
    const total = result.length;
    const paginated = result.slice((page - 1) * limit, page * limit);

    return {
      articles: paginated,
      pagination: {
        page,
        limit,
        total,
        total_pages: Math.ceil(total / limit)
      }
    };
  }

  public getArticleById(id: string): Article | null {
    return this.inMemoryArticles.find(a => a.id === id) || null;
  }

  public isSlugAvailable(slug: string, excludeId?: string): boolean {
    const clean = slugify(slug);
    return !this.inMemoryArticles.some(a => a.slug.toLowerCase() === clean && a.id !== excludeId);
  }

  public async createArticle(data: Partial<Article>, user = 'admin'): Promise<Article> {
    const title = (data.title || 'Untitled Article').trim();
    let slug = slugify(data.slug || title);

    if (!this.isSlugAvailable(slug)) {
      let counter = 2;
      while (!this.isSlugAvailable(`${slug}-${counter}`)) {
        counter++;
      }
      slug = `${slug}-${counter}`;
    }

    const content = data.content || '';
    const now = new Date().toISOString();
    const readingTime = data.reading_time || calculateReadingTime(content);
    const toc = extractTableOfContents(content);
    const content_format = normalizeContentFormat(data.content_format);
    const blog_type = normalizeBlogType(data.blog_type);
    const status = normalizeStatus(data.status);

    // Strict Rule: Do not publish DRAFT articles!
    const published_at = status === 'PUBLISHED' ? (data.published_at || now) : null;

    // Relational Category Resolution
    let category_id = data.category_id;
    let categoryName = data.category?.trim();
    let categoryObj = this.inMemoryCategories.find(c => 
      (category_id && c.id === category_id) || 
      (categoryName && (c.name.toLowerCase() === categoryName.toLowerCase() || c.slug === slugify(categoryName)))
    );

    if (!categoryObj) {
      categoryObj = this.inMemoryCategories.find(c => normalizeBlogType(c.blog_type) === blog_type);
      if (!categoryObj) {
        categoryObj = {
          id: `cat-${slugify(categoryName || (blog_type === 'HEALTHCARE' ? 'healthcare' : 'technology'))}`,
          name: categoryName || (blog_type === 'HEALTHCARE' ? 'Medicines & Pharmacology' : 'React & TypeScript'),
          slug: slugify(categoryName || (blog_type === 'HEALTHCARE' ? 'healthcare' : 'technology')),
          blog_type,
          description: 'General category'
        };
        this.inMemoryCategories.push(categoryObj);
      }
    }
    category_id = categoryObj.id;
    categoryName = categoryObj.name;

    // Relational Tag synchronization
    const rawTags = Array.isArray(data.tags) ? data.tags.map(t => t.trim()).filter(Boolean) : [];
    const tag_ids: string[] = [];
    for (const tagName of rawTags) {
      const tagSlug = slugify(tagName);
      let tagObj = this.inMemoryTags.find(t => t.slug === tagSlug);
      if (!tagObj) {
        tagObj = { id: `tag-${tagSlug}`, name: tagName, slug: tagSlug, count: 1 };
        this.inMemoryTags.push(tagObj);
      }
      tag_ids.push(tagObj.id);
    }

    const newArticle: Article = {
      id: `art-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      title,
      slug,
      excerpt: data.excerpt?.trim() || title,
      content,
      content_format,
      blog_type,
      category_id,
      category: categoryName,
      subcategory: data.subcategory?.trim(),
      tags: rawTags,
      tag_ids,
      author: data.author || {
        name: 'Muneer',
        title: 'Principal Systems Architect'
      },
      featured_image: data.featured_image?.trim() || (blog_type === 'HEALTHCARE' 
        ? 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=1200&auto=format&fit=crop&q=80'
        : 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&auto=format&fit=crop&q=80'),
      image_alt_text: data.image_alt_text?.trim() || title,
      reading_time: readingTime,
      status,
      featured: Boolean(data.featured),
      published_at,
      created_at: now,
      updated_at: now,
      seo_title: data.seo_title?.trim() || `${title} | MuneerDev`,
      seo_description: data.seo_description?.trim() || (data.excerpt?.trim() || title),
      canonical_url: data.canonical_url?.trim() || `https://muneerdev.com/blog/${slug}`,
      og_image: data.og_image?.trim() || data.featured_image?.trim() || '',
      table_of_contents: toc,
      references: Array.isArray(data.references) ? data.references : [],
      created_by: data.created_by || user || 'admin',
      updated_by: user || 'admin',
      related_articles: Array.isArray(data.related_articles) ? data.related_articles : [],
      related_projects: Array.isArray(data.related_projects) ? data.related_projects : [],
      related_services: Array.isArray(data.related_services) ? data.related_services : []
    };

    // Supabase PostgreSQL sync
    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('articles').insert([{
          id: newArticle.id,
          slug: newArticle.slug,
          title: newArticle.title,
          excerpt: newArticle.excerpt,
          content: newArticle.content,
          content_format: newArticle.content_format,
          blog_type: newArticle.blog_type,
          category_id: newArticle.category_id,
          status: newArticle.status,
          reading_time: newArticle.reading_time,
          featured: newArticle.featured,
          seo_title: newArticle.seo_title,
          seo_description: newArticle.seo_description,
          canonical_url: newArticle.canonical_url,
          og_image: newArticle.og_image,
          author: newArticle.author,
          table_of_contents: newArticle.table_of_contents,
          references: newArticle.references,
          published_at: newArticle.published_at,
          created_by: newArticle.created_by,
          updated_by: newArticle.updated_by
        }]);
      } catch (e) {
        console.error('[Database] Supabase article insert error:', e);
      }
    }

    this.inMemoryArticles.unshift(newArticle);
    this.inMemoryTags = this.generateTagsFromArticles(this.inMemoryArticles);
    await this.logAudit('CREATE_ARTICLE', newArticle.id, newArticle.title, user, `Status: ${newArticle.status}`);

    return newArticle;
  }

  public async updateArticle(id: string, updates: Partial<Article>, user = 'admin'): Promise<Article> {
    const index = this.inMemoryArticles.findIndex(a => a.id === id);
    if (index === -1) {
      throw new Error(`Article with id ${id} not found`);
    }

    const current = this.inMemoryArticles[index];
    const now = new Date().toISOString();

    let newSlug = current.slug;
    if (updates.slug && updates.slug.trim()) {
      const candidateSlug = slugify(updates.slug);
      if (candidateSlug !== current.slug) {
        if (!this.isSlugAvailable(candidateSlug, id)) {
          throw new Error(`Slug "${candidateSlug}" is already taken by another article`);
        }
        newSlug = candidateSlug;

        if (current.status === 'PUBLISHED' || updates.status === 'PUBLISHED') {
          this.inMemoryRedirects.push({
            from_slug: current.slug,
            to_slug: newSlug,
            created_at: now
          });
          await this.logAudit('CREATE_REDIRECT', current.id, current.title, user, `${current.slug} -> ${newSlug}`);
        }
      }
    }

    const content = updates.content !== undefined ? updates.content : current.content;
    const toc = extractTableOfContents(content);
    const readingTime = updates.reading_time || calculateReadingTime(content);
    const content_format = updates.content_format ? normalizeContentFormat(updates.content_format) : current.content_format;
    const blog_type = updates.blog_type ? normalizeBlogType(updates.blog_type) : current.blog_type;
    const status = updates.status ? normalizeStatus(updates.status) : current.status;

    // Strict Rule: Do not publish DRAFT articles!
    let published_at = current.published_at;
    if (status === 'DRAFT') {
      published_at = null;
    } else if (status === 'PUBLISHED') {
      published_at = updates.published_at || current.published_at || now;
    }

    // Category resolution
    let category_id = updates.category_id || current.category_id;
    let categoryName = updates.category !== undefined ? updates.category.trim() : current.category;
    if (updates.category_id && updates.category_id !== current.category_id) {
      const foundCat = this.inMemoryCategories.find(c => c.id === updates.category_id);
      if (foundCat) {
        categoryName = foundCat.name;
      }
    } else if (updates.category && updates.category !== current.category) {
      const foundCat = this.inMemoryCategories.find(c => c.name.toLowerCase() === updates.category!.toLowerCase());
      if (foundCat) {
        category_id = foundCat.id;
      }
    }

    // Tag resolution
    const tags = updates.tags !== undefined ? updates.tags : current.tags;
    const tag_ids = updates.tag_ids || current.tag_ids || [];

    const updated: Article = {
      ...current,
      ...updates,
      id: current.id,
      slug: newSlug,
      content,
      content_format,
      blog_type,
      category_id,
      category: categoryName,
      tags,
      tag_ids,
      status,
      table_of_contents: toc,
      reading_time: readingTime,
      published_at,
      updated_by: user || 'admin',
      updated_at: now
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('articles').update({
          slug: updated.slug,
          title: updated.title,
          excerpt: updated.excerpt,
          content: updated.content,
          content_format: updated.content_format,
          blog_type: updated.blog_type,
          category_id: updated.category_id,
          status: updated.status,
          reading_time: updated.reading_time,
          featured: updated.featured,
          seo_title: updated.seo_title,
          seo_description: updated.seo_description,
          canonical_url: updated.canonical_url,
          og_image: updated.og_image,
          author: updated.author,
          table_of_contents: updated.table_of_contents,
          references: updated.references,
          published_at: updated.published_at,
          updated_by: updated.updated_by,
          updated_at: updated.updated_at
        }).eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase article update error:', e);
      }
    }

    this.inMemoryArticles[index] = updated;
    this.inMemoryTags = this.generateTagsFromArticles(this.inMemoryArticles);
    await this.logAudit('UPDATE_ARTICLE', updated.id, updated.title, user, `Status: ${updated.status}`);

    return updated;
  }

  public async setArticleStatus(id: string, actionOrStatus: string, user = 'admin'): Promise<Article> {
    const article = this.getArticleById(id);
    if (!article) {
      throw new Error(`Article not found`);
    }

    const clean = actionOrStatus.toLowerCase();
    let nextStatus: ArticleStatus = 'DRAFT';
    let published_at: string | null = null;
    const now = new Date().toISOString();

    if (clean === 'publish' || clean === 'published') {
      nextStatus = 'PUBLISHED';
      published_at = article.published_at || now;
    } else if (clean === 'unpublish' || clean === 'draft' || clean === 'restore') {
      nextStatus = 'DRAFT';
      published_at = null; // Strictly: Do not publish DRAFT articles!
    } else if (clean === 'archive' || clean === 'archived') {
      nextStatus = 'ARCHIVED';
      published_at = article.published_at || null;
    }

    return this.updateArticle(id, {
      status: nextStatus,
      published_at,
      updated_at: now
    }, user);
  }

  public async deleteArticle(id: string, user = 'admin'): Promise<boolean> {
    const article = this.getArticleById(id);
    if (!article) {
      return false;
    }

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('articles').delete().eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase article delete error:', e);
      }
    }

    this.inMemoryArticles = this.inMemoryArticles.filter(a => a.id !== id);
    this.inMemoryTags = this.generateTagsFromArticles(this.inMemoryArticles);
    await this.logAudit('DELETE_ARTICLE', article.id, article.title, user);
    return true;
  }

  // --- Taxonomy: Categories & Tags (Database-Driven Management) ---
  public getCategories(blogType?: string): Category[] {
    let list = this.inMemoryCategories;
    if (blogType && blogType !== 'ALL') {
      const normType = normalizeBlogType(blogType);
      list = list.filter(c => normalizeBlogType(c.blog_type) === normType);
    }
    return list.map(c => ({
      ...c,
      article_count: this.inMemoryArticles.filter(a => 
        (a.category_id === c.id || a.category?.toLowerCase() === c.name.toLowerCase() || slugify(a.category || '') === c.slug) && 
        normalizeStatus(a.status) === 'PUBLISHED'
      ).length
    }));
  }

  public getCategoryById(id: string): Category | null {
    return this.inMemoryCategories.find(c => c.id === id || c.slug === id) || null;
  }

  public async addCategory(data: { name: string; blog_type: 'TECH' | 'HEALTHCARE' | 'HEALTHCARE_MEDICINE'; description?: string }, user = 'admin'): Promise<Category> {
    const normType = normalizeBlogType(data.blog_type);
    const slug = slugify(data.name);
    const existing = this.inMemoryCategories.find(c => c.slug === slug && normalizeBlogType(c.blog_type) === normType);
    if (existing) {
      return existing;
    }

    const newCat: Category = {
      id: `cat-${Date.now()}-${slug}`,
      name: data.name.trim(),
      slug,
      blog_type: normType,
      description: data.description?.trim() || ''
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('categories').insert([{
          id: newCat.id,
          slug: newCat.slug,
          name: newCat.name,
          description: newCat.description,
          blog_type: newCat.blog_type,
          entity_type: 'article'
        }]);
      } catch (e) {
        console.error('[Database] Supabase category insert error:', e);
      }
    }

    this.inMemoryCategories.push(newCat);
    await this.logAudit('CREATE_CATEGORY', newCat.id, newCat.name, user);
    return newCat;
  }

  public async updateCategory(id: string, data: { name?: string; description?: string; blog_type?: 'TECH' | 'HEALTHCARE' | 'HEALTHCARE_MEDICINE' }, user = 'admin'): Promise<Category> {
    const idx = this.inMemoryCategories.findIndex(c => c.id === id);
    if (idx === -1) {
      throw new Error(`Category with ID ${id} not found`);
    }

    const current = this.inMemoryCategories[idx];
    const oldName = current.name;
    const newName = data.name ? data.name.trim() : current.name;
    const newSlug = data.name ? slugify(data.name) : current.slug;
    const newType = data.blog_type ? normalizeBlogType(data.blog_type) : current.blog_type;
    const newDesc = data.description !== undefined ? data.description.trim() : current.description;

    const updated: Category = {
      ...current,
      name: newName,
      slug: newSlug,
      blog_type: newType,
      description: newDesc
    };

    this.inMemoryCategories[idx] = updated;

    // Cascade update category name on existing in-memory articles if name changed
    if (oldName !== newName) {
      this.inMemoryArticles.forEach(a => {
        if (a.category_id === id || a.category === oldName) {
          a.category = newName;
          a.category_id = id;
        }
      });
    }

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('categories').update({
          name: updated.name,
          slug: updated.slug,
          description: updated.description,
          blog_type: updated.blog_type,
          updated_at: new Date().toISOString()
        }).eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase category update error:', e);
      }
    }

    await this.logAudit('UPDATE_CATEGORY', updated.id, updated.name, user);
    return updated;
  }

  public async deleteCategory(id: string, user = 'admin'): Promise<boolean> {
    const cat = this.inMemoryCategories.find(c => c.id === id);
    if (!cat) {
      return false;
    }

    // Unassign category from existing articles to prevent dangling pointers
    this.inMemoryArticles.forEach(a => {
      if (a.category_id === id || a.category === cat.name) {
        a.category = 'General';
        a.category_id = 'cat-general';
      }
    });

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('categories').delete().eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase category delete error:', e);
      }
    }

    this.inMemoryCategories = this.inMemoryCategories.filter(c => c.id !== id);
    await this.logAudit('DELETE_CATEGORY', cat.id, cat.name, user);
    return true;
  }

  // --- Dynamic Manageable Tags ---
  public getTags(): Tag[] {
    // Merge dynamically added tags and article-derived tags
    const tagCountMap = new Map<string, number>();
    
    // Count from articles
    this.inMemoryArticles.forEach(art => {
      art.tags.forEach(tag => {
        const clean = tag.trim();
        if (clean) {
          tagCountMap.set(clean, (tagCountMap.get(clean) || 0) + 1);
        }
      });
    });

    // Ensure all stored tags exist in output
    this.inMemoryTags.forEach(t => {
      if (!tagCountMap.has(t.name)) {
        tagCountMap.set(t.name, t.count || 0);
      }
    });

    return Array.from(tagCountMap.entries()).map(([name, count]) => {
      const existing = this.inMemoryTags.find(t => t.name.toLowerCase() === name.toLowerCase());
      return {
        id: existing?.id || `tag-${slugify(name)}`,
        name,
        slug: slugify(name),
        count
      };
    });
  }

  public async addTag(name: string, user = 'admin'): Promise<Tag> {
    const cleanName = name.trim();
    if (!cleanName) throw new Error('Tag name cannot be blank');
    const slug = slugify(cleanName);

    const existing = this.inMemoryTags.find(t => t.slug === slug);
    if (existing) return existing;

    const newTag: Tag = {
      id: `tag-${Date.now()}-${slug}`,
      name: cleanName,
      slug,
      count: 0
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('tags').insert([{
          id: newTag.id,
          name: newTag.name,
          slug: newTag.slug
        }]);
      } catch (e) {
        console.error('[Database] Supabase tag insert error:', e);
      }
    }

    this.inMemoryTags.push(newTag);
    await this.logAudit('CREATE_TAG', newTag.id, newTag.name, user);
    return newTag;
  }

  public async updateTag(oldName: string, newName: string, user = 'admin'): Promise<Tag> {
    const cleanOld = oldName.trim();
    const cleanNew = newName.trim();
    if (!cleanNew) throw new Error('New tag name cannot be blank');
    const newSlug = slugify(cleanNew);

    // Update in stored tags
    const existing = this.inMemoryTags.find(t => t.name.toLowerCase() === cleanOld.toLowerCase() || t.slug === slugify(cleanOld));
    let tagId = existing ? existing.id : `tag-${Date.now()}-${newSlug}`;

    if (existing) {
      existing.name = cleanNew;
      existing.slug = newSlug;
    } else {
      this.inMemoryTags.push({ id: tagId, name: cleanNew, slug: newSlug, count: 0 });
    }

    // Cascade rename tag in articles
    this.inMemoryArticles.forEach(art => {
      const tagIndex = art.tags.findIndex(t => t.toLowerCase() === cleanOld.toLowerCase());
      if (tagIndex !== -1) {
        art.tags[tagIndex] = cleanNew;
      }
    });

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('tags').update({ name: cleanNew, slug: newSlug }).eq('id', tagId);
      } catch (e) {
        console.error('[Database] Supabase tag update error:', e);
      }
    }

    await this.logAudit('UPDATE_TAG', tagId, `${cleanOld} -> ${cleanNew}`, user);
    return { id: tagId, name: cleanNew, slug: newSlug };
  }

  public async deleteTag(name: string, user = 'admin'): Promise<boolean> {
    const clean = name.trim();
    const slug = slugify(clean);

    // Remove from in-memory articles
    this.inMemoryArticles.forEach(art => {
      art.tags = art.tags.filter(t => t.toLowerCase() !== clean.toLowerCase() && slugify(t) !== slug);
    });

    // Remove from in-memory tags list
    this.inMemoryTags = this.inMemoryTags.filter(t => t.name.toLowerCase() !== clean.toLowerCase() && t.slug !== slug);

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('tags').delete().or(`name.eq.${clean},slug.eq.${slug}`);
      } catch (e) {
        console.error('[Database] Supabase tag delete error:', e);
      }
    }

    await this.logAudit('DELETE_TAG', slug, clean, user);
    return true;
  }

  // --- Polymorphic Content Relationships ---
  public getContentRelationships(sourceType: EntityType, sourceId: string): ContentRelationshipRow[] {
    return this.inMemoryRelationships.filter(r => r.source_type === sourceType && r.source_id === sourceId);
  }

  public async addContentRelationship(rel: Omit<ContentRelationshipRow, 'id' | 'created_at'>, user = 'admin'): Promise<ContentRelationshipRow> {
    const newRel: ContentRelationshipRow = {
      id: `rel-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      ...rel,
      created_at: new Date().toISOString()
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('content_relationships').insert([newRel]);
      } catch (e) {
        console.error('[Database] Supabase content_relationships insert error:', e);
      }
    }

    this.inMemoryRelationships.push(newRel);
    await this.logAudit('CREATE_RELATIONSHIP', newRel.id, `${newRel.source_type} -> ${newRel.target_type}`, user);
    return newRel;
  }

  public async deleteContentRelationship(id: string, user = 'admin'): Promise<boolean> {
    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('content_relationships').delete().eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase relationship delete error:', e);
      }
    }
    this.inMemoryRelationships = this.inMemoryRelationships.filter(r => r.id !== id);
    await this.logAudit('DELETE_RELATIONSHIP', id, 'ContentRelationship', user);
    return true;
  }

  // --- Media Library & References ---
  public getMedia(): MediaItem[] {
    return this.inMemoryMedia;
  }

  public async addMedia(item: Omit<MediaItem, 'id' | 'created_at'>, user = 'admin'): Promise<MediaItem> {
    const mediaItem: MediaItem = {
      id: `media-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      ...item,
      created_at: new Date().toISOString()
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('media_assets').insert([{
          id: mediaItem.id,
          file_name: mediaItem.filename,
          original_name: mediaItem.original_name,
          url: mediaItem.url,
          mime_type: mediaItem.mime_type,
          size_bytes: mediaItem.size,
          alt_text: mediaItem.alt_text,
          caption: mediaItem.caption,
          storage_provider: mediaItem.storage_provider || 'local',
          storage_path: mediaItem.storage_path || mediaItem.filename,
          entity_type: mediaItem.entity_type || 'blogs'
        }]);
      } catch (e) {
        console.error('[Database] Supabase media insert error:', e);
      }
    }

    this.inMemoryMedia.unshift(mediaItem);
    await this.logAudit('UPLOAD_MEDIA', mediaItem.id, mediaItem.filename, user);
    return mediaItem;
  }

  public async deleteMedia(id: string, user = 'admin'): Promise<boolean> {
    const item = this.inMemoryMedia.find(m => m.id === id);
    if (!item) return false;

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('media_assets').delete().eq('id', id);
      } catch (e) {
        console.error('[Database] Supabase media delete error:', e);
      }
    }

    this.inMemoryMedia = this.inMemoryMedia.filter(m => m.id !== id);
    await this.logAudit('DELETE_MEDIA', item.id, item.filename, user);
    return true;
  }

  public getMediaReferences(mediaId: string): MediaReferenceRow[] {
    return this.inMemoryMediaReferences.filter(r => r.media_id === mediaId);
  }

  public async addMediaReference(ref: Omit<MediaReferenceRow, 'id' | 'created_at'>): Promise<MediaReferenceRow> {
    const newRef: MediaReferenceRow = {
      id: `mref-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      ...ref,
      created_at: new Date().toISOString()
    };

    if (this.isSupabaseConfigured && this.supabase) {
      try {
        await this.supabase.from('media_references').insert([newRef]);
      } catch (e) {
        console.error('[Database] Supabase media reference insert error:', e);
      }
    }

    this.inMemoryMediaReferences.push(newRef);
    return newRef;
  }

  // --- Redirects & Audits ---
  public getRedirects(): SlugRedirect[] {
    return this.inMemoryRedirects;
  }

  public getAuditLogs(): AuditLogEntry[] {
    return this.inMemoryAuditLogs;
  }

  // --- Dashboard Stats ---
  public getStats(): BlogStats {
    const published = this.inMemoryArticles.filter(a => a.status === 'published');
    const drafts = this.inMemoryArticles.filter(a => a.status === 'draft');
    const archived = this.inMemoryArticles.filter(a => a.status === 'archived');
    const tech = this.inMemoryArticles.filter(a => a.blog_type === 'TECH');
    const healthcare = this.inMemoryArticles.filter(a => a.blog_type === 'HEALTHCARE_MEDICINE');

    return {
      total_articles: this.inMemoryArticles.length,
      published_count: published.length,
      draft_count: drafts.length,
      archived_count: archived.length,
      tech_count: tech.length,
      healthcare_count: healthcare.length,
      total_views: 1240
    };
  }

  // --- Sitemap Data Generator ---
  public getAllPublishedForSitemap() {
    return this.inMemoryArticles
      .filter(a => normalizeStatus(a.status) === 'PUBLISHED')
      .map(a => ({
        slug: a.slug,
        title: a.title,
        updated_at: a.updated_at || a.published_at || a.created_at || new Date().toISOString(),
        published_at: a.published_at || a.created_at,
        featured: Boolean(a.featured),
        featured_image: a.featured_image || null,
        image_alt_text: a.image_alt_text || a.title
      }));
  }
}

export const db = new DatabaseService();
