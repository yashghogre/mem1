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

stop:
  @echo "Stopping the program. Taking down the docker containers."
  docker compose down
