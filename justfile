start:
  docker compose up -d
  @echo ""
  @echo "Docker services started!"
  @echo ""
  @echo "Starting main program..."
  # docker compose run --rm app
  # python3 -m src.main
  @echo ""

app:
  @echo "Starting interactive application"
  docker compose run --rm app python -m assistant.main

logs:
  @echo "Streaming logs from /app/app.log..."
  @echo "Waiting for log file to be created..."
  docker compose exec app /bin/sh -c "touch /app/app.log && tail -f /app/app.log"
  @echo "log file created. Streaming the logs now."

mongo:
  docker exec -it mongodb mongosh -u admin -p password123

redis:
  docker exec -it redis redis-cli -a redis_pass_123

psql:
  docker compose exec -it langfuse-db psql -U langfuse -d langfuse

stop:
  @echo "Stopping the program. Taking down the docker containers."
  docker compose down
