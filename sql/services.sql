-- =====================================================================
-- 知识服务市场（kb_service）—— 表结构 + 演示种子数据
-- 幂等：可重复执行；已存在的服务按 svc_code 跳过
-- =====================================================================

-- 1. 表结构
CREATE TABLE IF NOT EXISTS kb_service (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    svc_code      VARCHAR(30)  NOT NULL COMMENT '服务编码，如 SVC-001',
    svc_name      VARCHAR(100) NOT NULL COMMENT '服务名称',
    provider_dept VARCHAR(100) DEFAULT NULL COMMENT '提供部门',
    svc_type      VARCHAR(20)  NOT NULL COMMENT '服务类型：API/图谱/匹配/订阅/工具/交换',
    description   VARCHAR(500) DEFAULT NULL COMMENT '服务描述',
    tags          VARCHAR(300) DEFAULT NULL COMMENT '能力标签，逗号分隔',
    call_count    INT          NOT NULL DEFAULT 0 COMMENT '累计调用次数（演示数据）',
    api_count     INT          NOT NULL DEFAULT 0 COMMENT '接口数',
    doc_version   VARCHAR(20)  DEFAULT NULL COMMENT '接口文档版本，如 v2.4',
    doc_url       VARCHAR(300) DEFAULT NULL COMMENT '接口文档地址（预留）',
    status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1=已上架 0=已下架',
    sort_order    INT          NOT NULL DEFAULT 0 COMMENT '排序，越大越靠前',
    creator_id    BIGINT       DEFAULT NULL COMMENT '创建人用户ID',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted    TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_svc_code (svc_code),
    KEY idx_svc_type (svc_type),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识服务市场';

-- 2. 种子数据（6 项演示服务，对齐 demo；其中 2 项 created_at 设为本月以满足"本月新增"演示）
INSERT INTO kb_service (svc_code, svc_name, provider_dept, svc_type, description, tags, call_count, api_count, doc_version, status, sort_order, created_at)
SELECT * FROM (
    SELECT 'SVC-001' AS svc_code, '政策法规智能问答服务' AS svc_name,
           '市教育局 · 政策法规处' AS provider_dept, 'API' AS svc_type,
           '面向政务问答场景，提供政策条文级检索、条款引用与时效状态校验，支持按事项统一编码精确召回。' AS description,
           'QPS 50,返回条款原文,按部门授权' AS tags,
           12486 AS call_count, 6 AS api_count, 'v2.4' AS doc_version, 1 AS status, 600 AS sort_order,
           DATE_SUB(NOW(), INTERVAL 5 MONTH) AS created_at
    UNION ALL SELECT 'SVC-002', '政务服务事项知识图谱服务', '市政务服务和数据管理局 · 数据资源处', '图谱',
           '以事项、材料、部门、政策为实体构建知识图谱，支持一件事联办的材料关联与前置条件推导。',
           '实体 3.2 万,关系 11 万,支持多跳查询',
           8164, 4, 'v1.8', 1, 550, DATE_SUB(NOW(), INTERVAL 4 MONTH)
    UNION ALL SELECT 'SVC-003', '企业扶持政策匹配服务', '市工业和信息化局 · 企业服务处', '匹配',
           '依据企业规模、行业、资质与纳税信息，输出可申报政策清单及申报要点，附政策时效与受理期提醒。',
           '政策 368 条,按条件打分,结果可解释',
           6842, 5, 'v3.1', 1, 500, DATE_SUB(NOW(), INTERVAL 3 MONTH)
    UNION ALL SELECT 'SVC-004', '民生政策订阅推送服务', '市民政局 · 社会救助处', '订阅',
           '按人群标签订阅救助、养老、就业等民生政策，政策变更或受理期开启时以消息方式推送到服务对象。',
           '标签 24 类,支持短信/站内,推送留痕',
           4126, 3, 'v1.5', 1, 450, DATE_SUB(NOW(), INTERVAL 2 MONTH)
    UNION ALL SELECT 'SVC-005', '知识文档结构化解析服务', '市政务服务和数据管理局 · 信息化服务中心', '工具',
           '对扫描件、PDF、Word 文档执行 OCR 与版式还原，自动抽取标题、发文机关、发文字号与生效日期等字段。',
           'OCR 准确率 98%,批量 500 份/次,字段可映射',
           3968, 2, 'v2.0', 1, 400, DATE_SUB(NOW(), INTERVAL 12 DAY)
    UNION ALL SELECT 'SVC-006', '跨部门知识共享交换服务', '市大数据中心 · 共享交换部', '交换',
           '依据共享目录与授权清单完成部门间知识条目交换，支持增量同步、密级过滤与交换过程全程留痕。',
           '增量同步,密级过滤,交换留痕',
           2736, 4, 'v1.2', 1, 350, DATE_SUB(NOW(), INTERVAL 6 DAY)
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM kb_service);
