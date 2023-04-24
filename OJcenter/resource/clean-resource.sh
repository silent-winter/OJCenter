kubectl get deployment -o=name | grep -E '^deployment.apps/(server-913[0-9]|server-914[0-9]|server-9150)' | xargs kubectl delete
kubectl get pvc -o=name | grep -E "^persistentvolumeclaim/(pvc-913[0-9]|pvc-914[0-9]|pvc-9150)" | xargs kubectl delete
redis-cli KEYS "pod:metaInfo:91[3-5]*" | xargs redis-cli del
for i in {9130..9150}; do
    redis-cli LREM pod:portList 0 $i;
done