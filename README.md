langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t sealos-brian-ai:v0.8

docker tag sha256:deecf5f7c6a933f6a5267f5fd4fb384379cabe233e9dd1ec48b94c09bfdb3acc puddlecat/sealos-brain-ai:v0.15.5

docker tag sha256:5a56e6a151c4e8d8999716f86ab58d3b7d1bba7b6d6c96dccbf9a06202d8c9e6 crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
