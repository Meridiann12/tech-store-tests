@echo off
rem Запуск всех тестов проекта Tech Store (Практическая работа №8).
rem Unit-тесты прогоняются отдельно для каждого сервиса.
setlocal
cd /d "%~dp0"

for %%s in (user_service catalog_service inventory_service order_service payment_service review_service) do (
  echo ===============================================================
  echo == Unit-тесты: %%s
  echo ===============================================================
  pytest %%s\tests\unit -v
)

echo ===============================================================
echo == Компонентные тесты (e2e): сервисы поднимаются фикстурами ==
echo ===============================================================
pytest tests\component -v

endlocal
