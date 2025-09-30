langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t sealos-brian-ai:v0.8

docker tag sha256:9eb0d4a8a7c28fd933caa9511b3ec7db2b1936ad0ad181f0ba6e7f1c0aa1db4e puddlecat/sealos-brain-ai:v0.16.2

docker tag sha256:5a56e6a151c4e8d8999716f86ab58d3b7d1bba7b6d6c96dccbf9a06202d8c9e6 crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
