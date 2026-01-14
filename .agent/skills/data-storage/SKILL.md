---
name: data-storage
description: Handles data persistence in PostgreSQL (Async SQLAlchemy) and file storage in MinIO (S3).
version: 2.0
---

# 1. Database (PostgreSQL)

- **ORM**: SQLAlchemy 2.0+ (Async).
- **Session**: Use `AsyncSession`.
- **Query Style**: Use modern strict syntax: `await session.execute(select(Model).where(...))`.
- **Relationships**: Be careful with Lazy Loading in async context. Use `options(selectinload(...))` to prevent "Greenlet" errors.

## 2. Object Storage (MinIO)

- **Provider**: Use `StorageProvider` class.
- **Bucket**: `anexos-email-bitrix`.
- **Security**:
  - NEVER store full URLs in the database if they are pre-signed/expiring.
  - STORE the object key (path) e.g., `attachments/file.pdf`.
  - GENERATE the signed URL (`get_presigned_url`) dynamically when serializing the response in Pydantic.

## 3. File Upload Workflow

- **Large Files**: Handle via `UploadFile` (FastAPI).
- **Naming**: Sanitize filenames before upload to prevent path traversal or encoding issues.
