kubectl get pod -o=name | grep "^pod/server-" | xargs kubectl delete
kubectl get pvc -o=name | grep "^persistentvolumeclaim/pvc-" | xargs kubectl delete
find /nfs/data -type d -name "default*" -exec rm -r {} \;