#!/usr/bin/env bash
# Запуск всех тестов проекта Tech Store (Практическая работа №8).
# Unit-тесты прогоняются отдельно для каждого сервиса — в микросервисной
# архитектуре у каждого сервиса свой набор тестов, не зависящий от остальных.
set -u
cd "$(dirname "$0")"

status=0

for svc in user_service catalog_service inventory_service order_service payment_service review_service; do
  echo "==============================================================="
  echo "== Unit-тесты: $svc"
  echo "==============================================================="
  pytest "$svc/tests/unit" -v || status=1
done

echo "==============================================================="
echo "== Компонентные тесты (e2e): сервисы поднимаются фикстурами =="
echo "==============================================================="
pytest tests/component -v || status=1

exit $status
