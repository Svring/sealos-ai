langgraph dev --port 2025 --allow-blocking

langgraph build --platform linux/amd64 -t sealos-brian-ai:v0.3

docker tag sha256:20d82c477558d2f02a25a0840e153d84ec925ae7133b6e08e421b30ce43eb333 crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.3

docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-ai:v0.3

docker tag ai puddlecat/ai:latest
docker push puddlecat/ai:latest
