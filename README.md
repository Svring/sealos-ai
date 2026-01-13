langgraph dev --port 2025 --allow-blocking --no-browser

langgraph build --platform linux/amd64 -t puddlecat/sealos-brain-ai:kb.0.20.68

docker push puddlecat/sealos-brain-ai:kb.0.20.68
