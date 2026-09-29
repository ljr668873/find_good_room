docker run -d \
--name mysql-local \
-p 3306:3306 \
--restart=always \
-e MYSQL_ROOT_PASSWORD="Root@123" \
-e TZ=Asia/Shanghai \
-v mysql-local-data:/var/lib/mysql \
mysql:latest \
--character-set-server=utf8mb4 \
--collation-server=utf8mb4_unicode_ci
