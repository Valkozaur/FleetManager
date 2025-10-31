# Database Migration Service

This service is responsible for running database migrations using Alembic.

## Usage

To run migrations, you can use the following command:

```bash
docker-compose run --rm database-migration upgrade head
```

To generate a new migration:

```bash
docker-compose run --rm database-migration revision --autogenerate -m "Your migration message"
```
