langgraph dev --port 2025 --allow-blocking
langgraph build --platform linux/amd64 -t puddlecat/ai:latest

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
