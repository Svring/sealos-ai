langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t puddlecat/sealos-brain-ai:0.18.3

docker push puddlecat/sealos-brain-ai:0.18.3
