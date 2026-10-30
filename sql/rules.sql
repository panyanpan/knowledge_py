-- =====================================================================
-- 知识规则管理（kb_rule）—— 表结构 + 种子数据
-- 幂等：可重复执行；已存在的规则按 rule_code 跳过
-- =====================================================================

-- 1. 表结构
CREATE TABLE IF NOT EXISTS kb_rule (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    rule_code     VARCHAR(30)  NOT NULL COMMENT '规则编码，如 R-012',
    rule_name     VARCHAR(100) NOT NULL COMMENT '规则名称',
    description   VARCHAR(200) DEFAULT NULL COMMENT '规则副标题/用途说明',
    rule_type     VARCHAR(20)  NOT NULL COMMENT '规则类型：时效性/完整性/一致性/重复度/安全合规/规范性',
    scope_text    VARCHAR(200) DEFAULT NULL COMMENT '适用范围描述',
    condition_text VARCHAR(500) DEFAULT NULL COMMENT '判定条件描述',
    hit_count     INT          NOT NULL DEFAULT 0 COMMENT '最近一轮试运行命中数',
    run_count     INT          NOT NULL DEFAULT 0 COMMENT '累计试运行次数',
    last_run_at   DATETIME     DEFAULT NULL COMMENT '最近试运行时间',
    status        TINYINT      NOT NULL DEFAULT 2 COMMENT '状态：1=启用 0=停用 2=待复核',
    sort_order    INT          NOT NULL DEFAULT 0 COMMENT '排序，越大越靠前',
    creator_id    BIGINT       DEFAULT NULL COMMENT '创建人用户ID',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted    TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_rule_code (rule_code),
    KEY idx_rule_type (rule_type),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识质量规则';

-- 2. 种子数据（12 条，对齐规则清单 demo）
INSERT INTO kb_rule (rule_code, rule_name, description, rule_type, scope_text, condition_text, hit_count, run_count, last_run_at, status, sort_order)
SELECT * FROM (
    SELECT 'R-012' AS rule_code, '政策时效校验' AS rule_name,
           '校验知识标注有效期与所引政策文件的现行有效性' AS description,
           '时效性' AS rule_type, '政策类知识' AS scope_text,
           '有效期 ≥ 当前日期 + 45 天，且政策依据未废止' AS condition_text,
           46 AS hit_count, 12 AS run_count, NOW() AS last_run_at, 1 AS status, 120 AS sort_order
    UNION ALL SELECT 'R-007', '必填字段完整性', '检查元数据必填项是否为空，阻断不完整知识入库',
           '完整性', '全量知识', '政策依据、责任部门、办理时限等 6 项必填字段非空',
           38, 15, NOW(), 1, 115
    UNION ALL SELECT 'R-021', '知识重复度检测', '识别正文高度相似的知识条目，避免重复维护',
           '重复度', '全量知识', '正文相似度 ≥ 0.92，且标题相似度 ≥ 0.80',
           27, 9, NOW(), 1, 110
    UNION ALL SELECT 'R-015', '事项编码一致性', '与政务服务事项库比对，确保关联事项编码准确',
           '一致性', '事项关联知识', '事项编码与事项库逐位一致，且事项状态为在用',
           19, 11, NOW(), 1, 105
    UNION ALL SELECT 'R-009', '密级与共享类型匹配', '校验知识密级不低于内容敏感度，共享类型与密级一致',
           '安全合规', '民生类知识', '密级 ≥「内部」，共享类型不得为无条件共享',
           12, 8, NOW(), 1, 100
    UNION ALL SELECT 'R-018', '多源口径一致性', '比对政策库、部门网站与知识条目的关键口径',
           '一致性', '政策解读类知识', '奖励上限、申报条件等 5 个关键字段与政策原文一致',
           9, 7, NOW(), 1, 95
    UNION ALL SELECT 'R-030', '分类归口校验', '检查知识分类编码是否存在且处于启用状态',
           '一致性', '全量知识', '分类编码存在于分类目录，且分类状态为启用',
           8, 10, NOW(), 1, 90
    UNION ALL SELECT 'R-037', '业务场景标签完整性', '场景类知识需至少绑定一个业务场景标签',
           '完整性', '场景类知识', '业务场景标签数量 ≥ 1，且标签在场景库内',
           7, 5, NOW(), 0, 85
    UNION ALL SELECT 'R-024', '关联资源有效性', '检测附件与外部链接是否可正常访问',
           '完整性', '含附件知识', '附件与外部链接返回 HTTP 200，且文件大小 > 0',
           6, 6, NOW(), 1, 80
    UNION ALL SELECT 'R-026', '敏感个人信息识别', '识别正文中的身份证号、手机号等敏感信息',
           '安全合规', '全量知识', '命中身份证号、手机号等 8 类正则，且未脱敏',
           4, 13, NOW(), 1, 75
    UNION ALL SELECT 'R-031', '附件格式与大小', '限制附件类型与单文件体积，保障阅读体验',
           '规范性', '含附件知识', '仅允许 PDF / OFD，单文件 ≤ 20 MB',
           3, 4, NOW(), 0, 70
    UNION ALL SELECT 'R-033', '摘要生成质量', '校验 AI 生成摘要的长度与要素完整性',
           '规范性', 'AI 摘要知识', '摘要 80–200 字，含事项主体与办理结论',
           2, 3, NOW(), 2, 65
    UNION ALL SELECT 'R-040', '办理时限一致性', '比对事项承诺时限与法定时限，防止超期承诺',
           '时效性', '政务服务事项知识', '承诺办结时限 ≤ 法定办结时限，且时限单位一致',
           0, 0, NULL, 2, 60
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM kb_rule);
