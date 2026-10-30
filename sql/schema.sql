-- =============================================================
-- 知识库管理系统 · 建表脚本（阶段一）
-- 适用：MySQL 8.0，库 zwfw_zsk（库需已存在，本脚本不建库）
-- 引擎：InnoDB；字符集：utf8mb4；时间：应用层写 UTC
-- 通用字段：created_at / updated_at / is_deleted（软删除）
-- =============================================================

-- ---------- 1. 角色表 ----------
CREATE TABLE IF NOT EXISTS sys_role (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code        VARCHAR(20)  NOT NULL COMMENT '角色编码: ADMIN/USER',
    name        VARCHAR(50)  NOT NULL COMMENT '角色名称',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted  TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='角色表';

-- ---------- 2. 用户表 ----------
CREATE TABLE IF NOT EXISTS sys_user (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL COMMENT '用户名',
    password_hash VARCHAR(100) NOT NULL COMMENT 'bcrypt 哈希',
    email         VARCHAR(100) NOT NULL COMMENT '邮箱',
    nickname      VARCHAR(50)  NULL COMMENT '昵称',
    avatar        VARCHAR(255) NULL COMMENT '头像URL',
    role_id       BIGINT UNSIGNED NOT NULL DEFAULT 2 COMMENT '角色: 1=ADMIN 2=USER',
    status        TINYINT      NOT NULL DEFAULT 1 COMMENT '1=正常 0=禁用',
    token_version INT          NOT NULL DEFAULT 0 COMMENT '登出失效方案: 版本号',
    last_login_at DATETIME     NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted    TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_username (username),
    UNIQUE KEY uk_user_email (email),
    KEY idx_user_role (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户表';

-- ---------- 3. 知识分类表（多级，自关联） ----------
CREATE TABLE IF NOT EXISTS kb_category (
    id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    parent_id  BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '父分类ID, 0=顶级',
    name       VARCHAR(100) NOT NULL COMMENT '分类名',
    level      TINYINT      NOT NULL DEFAULT 1 COMMENT '层级 1~5',
    path       VARCHAR(500) NOT NULL DEFAULT '' COMMENT '物化路径 如 1/5/12, 便于树查询',
    sort_order INT          NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_cat_parent (parent_id),
    KEY idx_cat_path (path(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='知识分类表(多级)';

-- ---------- 4. 知识条目表 ----------
CREATE TABLE IF NOT EXISTS kb_entry (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_id BIGINT UNSIGNED NOT NULL COMMENT '所属分类',
    author_id   BIGINT UNSIGNED NOT NULL COMMENT '创建人',
    title       VARCHAR(200) NOT NULL COMMENT '标题',
    content     LONGTEXT     NULL COMMENT '富文本内容(存前白名单清洗)',
    summary     VARCHAR(500) NULL COMMENT '摘要',
    visibility  TINYINT      NOT NULL DEFAULT 0 COMMENT '0=私有 1=公开',
    view_count  INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览量',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted  TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_entry_category (category_id),
    KEY idx_entry_author (author_id),
    KEY idx_entry_visibility (visibility),
    KEY idx_entry_title (title(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='知识条目表';

-- ---------- 5. 标签表 ----------
CREATE TABLE IF NOT EXISTS kb_tag (
    id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(50) NOT NULL COMMENT '标签名',
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT     NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_tag_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='标签表';

-- ---------- 6. 条目-标签关联表 ----------
CREATE TABLE IF NOT EXISTS kb_entry_tag (
    entry_id BIGINT UNSIGNED NOT NULL,
    tag_id   BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (entry_id, tag_id),
    KEY idx_et_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='条目-标签关联';

-- ---------- 7. 附件表 ----------
CREATE TABLE IF NOT EXISTS kb_attachment (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    entry_id    BIGINT UNSIGNED NOT NULL COMMENT '所属条目',
    uploader_id BIGINT UNSIGNED NOT NULL COMMENT '上传人',
    file_name   VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path   VARCHAR(500) NOT NULL COMMENT '存储相对路径',
    file_size   BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '字节数',
    mime_type   VARCHAR(100) NOT NULL DEFAULT '' COMMENT 'MIME类型',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted  TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_att_entry (entry_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='附件表';

-- ---------- 8. 公告/轮播图表 ----------
CREATE TABLE IF NOT EXISTS sys_announcement (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    type         TINYINT      NOT NULL DEFAULT 1 COMMENT '1=公告 2=轮播图',
    title        VARCHAR(200) NOT NULL COMMENT '标题',
    content      TEXT         NULL COMMENT '公告正文',
    image_url    VARCHAR(500) NULL COMMENT '轮播图图片URL',
    link_url     VARCHAR(500) NULL COMMENT '跳转链接',
    sort_order   INT          NOT NULL DEFAULT 0,
    is_published TINYINT      NOT NULL DEFAULT 1 COMMENT '1=已发布 0=下线',
    publisher_id BIGINT UNSIGNED NOT NULL COMMENT '发布人(ADMIN)',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted   TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_ann_type_publish (type, is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='公告/轮播图表';

-- ---------- 初始化数据 ----------
INSERT INTO sys_role (id, code, name) VALUES (1, 'ADMIN', '管理员'), (2, 'USER', '普通用户')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 初始管理员账号 admin / 待填入 bcrypt 哈希（占位符由脚本替换）
INSERT INTO sys_user (username, password_hash, email, nickname, role_id, status)
VALUES ('admin', '$2b$12$eiyPlysjWwX0XiaPO.Wdmebwt0YWNC8y7FKyi5Gice2M/Aj4Y1zh.', 'admin@example.com', '系统管理员', 1, 1)
ON DUPLICATE KEY UPDATE nickname = VALUES(nickname);
