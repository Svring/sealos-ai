langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t sealos-brian-ai:v0.7

docker tag sha256:c8a43c42cb4ac517d13ecb4fe4b1dd139d00f91a77c8ecef6e7593d2cf95d799 crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.3

docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.3

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
