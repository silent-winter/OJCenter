#!/bin/bash

declare -A POD_CPU_VIOLATION_COUNTER
while true; do
  # 查找所有运行的 Pod。
  running_pods=$(kubectl get pods --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}')
  for pod_name in $running_pods; do
    # 获取此 Pod 的 CPU 使用情况和 Limit。
    cpu_usage=$(kubectl top pod "$pod_name" | awk '{print $2}' | tail -n 1 | awk '{print substr($1, 1, length($1)-1)}')
    # cpu_limit=$(kubectl get pod "$pod_name" -o jsonpath='{.spec.containers[*].resources.limits.cpu}' | tr -d 'm')
    if [[ $cpu_usage -gt 380 ]]; then
      if [[ -z ${POD_CPU_VIOLATION_COUNTER["$pod_name"]} ]]; then
        POD_CPU_VIOLATION_COUNTER["$pod_name"]=1
      else
        POD_CPU_VIOLATION_COUNTER["$pod_name"]=$((POD_CPU_VIOLATION_COUNTER["$pod_name"]+1))
      fi
      echo "Pod $pod_name has exceeded its CPU limit ${POD_CPU_VIOLATION_COUNTER["$pod_name"]} times." >> /var/log/task.log
      if [[ ${POD_CPU_VIOLATION_COUNTER["$pod_name"]} -ge 2 ]]; then
        echo "Killing Pod $pod_name due to repeated CPU violations." >> /var/log/task.log
        kubectl delete pod "$pod_name"
        unset POD_CPU_VIOLATION_COUNTER["$pod_name"]
      fi
    else
      unset POD_CPU_VIOLATION_COUNTER["$pod_name"]
    fi
  done
  sleep 30s;
done

