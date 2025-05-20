Twitter-clone-v2/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entrypoint with cache, batcher, logging
│   ├── database.py              # SQLAlchemy engine & session
│   ├── models.py                # ORM models
│   ├── cache.py                 # Redis cache init, get/set helpers
│   ├── like_batcher.py          # Batcher class for aggregating likes
│   ├── logging_config.py        # StructLog/JSON log setup
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── accounts.py          # /accounts endpoints
│   │   └── tweets.py            # /tweets endpoints (with cache & batcher calls)
│   └── utils/                   # shared helpers
│       ├── auth.py
│       └── settings.py          # Pydantic settings (e.g. Redis URL, DB URL)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures (test DB, test cache)
│   ├── test_accounts.py
│   └── test_tweets.py
│
├── load_tests/
│   ├── locustfile.py            # Load-testing scenarios for posting, searching, liking
│   └── README.md
│
├── docker/
│   ├── Dockerfile.api           # Container for FastAPI app
│   ├── Dockerfile.redis         # Redis (if custom config)
│   ├── docker-compose.yml       # Orchestrate API, Postgres, Redis
│   └── nginx/
│       ├── Dockerfile           # Nginx as load-balancer/reverse proxy
│       └── nginx.conf
│
├── scripts/
│   ├── run_db_migrations.sh     # e.g. Alembic migrations
│   └── flush_cache.sh
│
├── logging/                      # (Optional) centralized logging config for ELK/EFK
│   └── filebeat.yml
│
├── report/
│   ├── performance_report.md    # Results of load-testing & caching benchmarks
│   └── architecture.md          # Diagram + explanations of your A2 design
│
├── .gitignore
├── README.md                     # Updated with A2 instructions
└── requirements.txt              # pinned dependencies (FastAPI, Redis, locust, pytest…)
