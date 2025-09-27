langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t sealos-brian-ai:v0.8

docker tag sha256:ad86634ac03d214f893bfcf318eb33c951061e9ff8b7982b84a3035abe8bd8f9 puddlecat/sealos-brain-ai:v0.15.1

docker tag sha256:5a56e6a151c4e8d8999716f86ab58d3b7d1bba7b6d6c96dccbf9a06202d8c9e6 crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.8

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
