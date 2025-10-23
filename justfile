start:
  docker compose up -d
  @echo ""
  @echo "Docker services started!"
  @echo ""
  @echo "Starting main program..."
  docker compose run --rm app
  # python3 -m src.main
  @echo ""

mongo:
  docker exec -it mongodb mongosh -u admin -p password123

redis:
  docker exec -it redis redis-cli -a redis_pass_123

psql:
  docker compose exec -it langfuse-db psql -U langfuse -d langfuse

stop:
  @echo "Stopping the program. Taking down the docker containers."
  docker compose down
