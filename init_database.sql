-- 数据库初始化脚本
-- 创建 cloud_resource 和 tmdb 表

-- 如果数据库不存在则创建
CREATE DATABASE IF NOT EXISTS pan_library DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE pan_library;

-- 创建网盘资源库表
CREATE TABLE IF NOT EXISTS cloud_resource (
    id INT AUTO_INCREMENT COMMENT '主键ID',
    drama_name VARCHAR(255) NOT NULL DEFAULT '' COMMENT '剧名',
    alias VARCHAR(200) NOT NULL DEFAULT '' COMMENT '别名',
    category1 VARCHAR(100) NOT NULL DEFAULT '' COMMENT '分类1,影视资源,学习资料',
    category2 VARCHAR(100) NULL COMMENT '分类2（如电影、电视剧、动漫等）',
    drive_type VARCHAR(50) NOT NULL COMMENT '网盘类型（如百度云、阿里云���腾讯云等）',
    link TEXT NULL COMMENT '网盘分享链接',
    is_expired TINYINT NOT NULL DEFAULT 1 COMMENT '是否失效（0：有效，1：失效）',
    view_count INT NOT NULL DEFAULT 0 COMMENT '浏览次数',
    share_count INT NOT NULL DEFAULT 0 COMMENT '分享次数',
    hot INT NOT NULL DEFAULT 0 COMMENT '热度',
    size VARCHAR(50) NULL COMMENT '文件大小',
    tmdb_id INT NULL COMMENT '影视资源信息ID',
    last_share_time DATETIME NULL COMMENT '上次分享时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NULL COMMENT '记录创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NULL COMMENT '记录修改时间',
    PRIMARY KEY (id),
    CONSTRAINT uk_drama_drive UNIQUE (drama_name, drive_type),
    INDEX idx_drama_name (drama_name),
    INDEX idx_drive_type (drive_type),
    INDEX idx_is_expired (is_expired),
    INDEX idx_tmdb_id (tmdb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='网盘资源库表';

-- 创建TMDB剧集信息表
CREATE TABLE IF NOT EXISTS tmdb (
    id INT AUTO_INCREMENT COMMENT '主键ID',
    tmdb_code VARCHAR(255) NOT NULL COMMENT 'tmdb的剧编号',
    title VARCHAR(255) NOT NULL COMMENT '剧的名称',
    year_released INT NULL COMMENT '上映/发行年份（如2023）',
    category VARCHAR(100) NULL COMMENT '分类（如剧情、喜剧、科幻等）',
    description TEXT NULL COMMENT '剧情描述',
    poster_url VARCHAR(500) NULL COMMENT '海报图片链接',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NULL COMMENT '记录创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NULL COMMENT '记录更新时间',
    PRIMARY KEY (id),
    CONSTRAINT uk_title_year UNIQUE (title, year_released),
    INDEX idx_tmdb_code (tmdb_code),
    INDEX idx_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='TMDB剧集信息表（含年份）';

-- 显示表结构
SHOW TABLES;
DESCRIBE cloud_resource;
DESCRIBE tmdb;

-- 提示信息
SELECT '✅ 数据库表创建完成！' AS message;
