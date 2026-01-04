langgraph dev --port 2025 --allow-blocking --no-browser

langgraph build --platform linux/amd64 -t puddlecat/sealos-brain-ai:0.20.63

docker push puddlecat/sealos-brain-ai:0.20.63
