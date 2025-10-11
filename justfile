start:
  docker compose up -d
  @echo ""
  @echo "Docker services started!"
  @echo ""
  @echo "Starting main program..."
  python3 -m src.main
  @echo ""

mongo:
  docker exec -it memory-framework-mongodb-1 mongosh

stop:
  @echo "Stopping the program. Taking down the docker containers."
  docker compose down
