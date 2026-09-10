CREATE DATABASE IF NOT EXISTS vokit_control CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS vokit_tenant_a CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS vokit_tenant_b CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON vokit_control.* TO 'vokit'@'%';
GRANT ALL PRIVILEGES ON vokit_tenant_a.* TO 'vokit'@'%';
GRANT ALL PRIVILEGES ON vokit_tenant_b.* TO 'vokit'@'%';
FLUSH PRIVILEGES;
