#!/bin/sh
# Том /app/data на Fly/Docker монтируется владельцем root. Приложение пишет
# data/users/<uid>.db и data/secret.key под непривилегированным michi — без
# этого chown ленивое создание базы упало бы с PermissionError на первой записи.
set -e

mkdir -p /app/data
chown -R michi:michi /app/data

# Стартовали под root только ради chown — дальше работаем под michi.
# exec gosu заменяет процесс (корректный PID 1: проброс сигналов/останов).
exec gosu michi "$@"
