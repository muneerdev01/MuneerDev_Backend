# MuneerDev Blog API 🚀

An asynchronous, high-performance RESTful API built with **FastAPI**, **SQLAlchemy (AsyncIO)**, and **PostgreSQL** for managing blog articles, categories, tags, media assets, and healthcare content safeguards.

---

## 🛠 Tech Stack

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Database ORM:** [SQLAlchemy 2.0 (Async)](https://www.sqlalchemy.org/) with `asyncpg`
* **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
* **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)
* **Storage / Cloud:** [Supabase](https://supabase.com/)
* **Server:** [Uvicorn](https://www.uvicorn.org/)

---

## 📁 Project Structure

```text
.
├── config/             # Settings and configuration
├── database/           # Async database connection and session management
├── models/             # SQLAlchemy ORM models (Articles, Categories, Tags, etc.)
├── routers/            # FastAPI route handlers (Public, Admin, Auth, Media)
├── utils/              # Helper utilities (Slug generator, TOC extractor, Safeguards)
├── test_db.py          # Database setup and connection test script
├── test_services.py    # Service utilities test script
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation