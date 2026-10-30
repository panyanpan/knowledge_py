-- ============================================================
-- 知识溯源：溯源主体 + 溯源环节（演示种子数据，待后续 API 对接调整）
-- 幂等执行：表存在则跳过建表；种子按 trace_no 幂等
-- ============================================================

-- 1. 溯源主体表
CREATE TABLE IF NOT EXISTS kb_trace (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  trace_no      VARCHAR(50)  NOT NULL COMMENT '溯源编号',
  title         VARCHAR(200) NOT NULL COMMENT '知识条目名称/主题',
  entry_no      VARCHAR(50)  NOT NULL COMMENT '知识编号',
  scene         VARCHAR(100) NOT NULL DEFAULT '' COMMENT '业务场景',
  category      VARCHAR(100) NOT NULL DEFAULT '' COMMENT '所属分类',
  version       VARCHAR(20)  NOT NULL DEFAULT 'V 1.0' COMMENT '当前版本',
  dept          VARCHAR(100) NOT NULL DEFAULT '' COMMENT '责任部门',
  secret_level  VARCHAR(20)  NOT NULL DEFAULT '公开' COMMENT '密级：公开/内部/涉密',
  chain_status  TINYINT      NOT NULL DEFAULT 1 COMMENT '链路状态：1完整可溯源 0缺失待补录',
  query_count   INT          NOT NULL DEFAULT 0 COMMENT '累计溯源查询次数',
  last_query_at DATETIME     NULL COMMENT '最近溯源时间',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_deleted    TINYINT      NOT NULL DEFAULT 0,
  UNIQUE KEY uk_trace_no (trace_no),
  KEY idx_trace_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识溯源主体';

-- 2. 溯源环节表
CREATE TABLE IF NOT EXISTS kb_trace_node (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  trace_id    INT          NOT NULL COMMENT '溯源主体ID',
  step_no     INT          NOT NULL COMMENT '环节序号 01-06',
  name        VARCHAR(50)  NOT NULL COMMENT '环节名称',
  sub         VARCHAR(200) NOT NULL DEFAULT '' COMMENT '环节副标题/说明',
  occurred_at DATETIME     NULL COMMENT '发生时间',
  actor       VARCHAR(100) NOT NULL DEFAULT '' COMMENT '操作主体',
  source_ref  VARCHAR(200) NOT NULL DEFAULT '' COMMENT '来源依据（系统/文件/单据）',
  result      VARCHAR(20)  NOT NULL DEFAULT '' COMMENT '校验结果文本',
  result_level VARCHAR(10) NOT NULL DEFAULT 'green' COMMENT '结果色：green/blue/warn',
  evidence    TEXT         NULL COMMENT '存证凭证（演示内容）',
  KEY idx_node_trace (trace_id, step_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识溯源环节';

-- 3. 溯源主体种子（4 个快捷溯源主题）
INSERT INTO kb_trace (trace_no, title, entry_no, scene, category, version, dept, secret_level, chain_status, query_count, last_query_at)
SELECT * FROM (SELECT
  'TR-2026-001', '外来务工人员子女入学', 'KB-MZ-2026-001284', '义务教育招生入学',
  '民生保障 / 教育服务', 'V 3.2', '市教育局 · 基础教育处', '内部', 1, 128, '2026-10-28 16:22:00'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM kb_trace WHERE trace_no = 'TR-2026-001');

INSERT INTO kb_trace (trace_no, title, entry_no, scene, category, version, dept, secret_level, chain_status, query_count, last_query_at)
SELECT * FROM (SELECT
  'TR-2026-002', '企业上市专题政策包', 'KB-QY-2026-000917', '企业上市培育服务',
  '企业发展 / 上市服务', 'V 2.1', '市地方金融管理局 · 资本市场处', '内部', 1, 96, '2026-10-26 10:41:00'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM kb_trace WHERE trace_no = 'TR-2026-002');

INSERT INTO kb_trace (trace_no, title, entry_no, scene, category, version, dept, secret_level, chain_status, query_count, last_query_at)
SELECT * FROM (SELECT
  'TR-2026-003', '建设工程施工许可核发', 'KB-GC-2026-000512', '工程建设项目审批',
  '工程建设 / 许可审批', 'V 4.0', '市住建局 · 行政审批处', '公开', 1, 74, '2026-10-21 09:05:00'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM kb_trace WHERE trace_no = 'TR-2026-003');

INSERT INTO kb_trace (trace_no, title, entry_no, scene, category, version, dept, secret_level, chain_status, query_count, last_query_at)
SELECT * FROM (SELECT
  'TR-2026-004', '社会救助一件事联办', 'KB-MZ-2026-000338', '社会救助综合受理',
  '民生保障 / 社会救助', 'V 1.6', '市民政局 · 社会救助处', '内部', 0, 44, '2026-10-15 14:30:00'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM kb_trace WHERE trace_no = 'TR-2026-004');

-- 4. 溯源环节种子（每个主题 6 个环节，按 trace_no 关联）
INSERT INTO kb_trace_node (trace_id, step_no, name, sub, occurred_at, actor, source_ref, result, result_level, evidence)
SELECT t.id, n.step_no, n.name, n.sub, n.occurred_at, n.actor, n.source_ref, n.result, n.result_level, n.evidence
FROM kb_trace t
JOIN (
  SELECT 'TR-2026-001' AS trace_no, 1 AS step_no, '数据源接入' AS name, '通过政务数据共享交换平台接口同步' AS sub,
         '2026-09-16 09:12:00' AS occurred_at, '市教育局 · 招生入学系统' AS actor,
         '接口批次 BT20260916-03' AS source_ref, '通过' AS result, 'green' AS result_level,
         '凭证编号 PZ-20260916-0001；时间戳 2026-09-16 09:12:36（可信时间源）；来源系统：招生入学系统 v5.2；接口批次 BT20260916-03 共同步记录 1,842 条，校验和一致。' AS evidence
  UNION ALL SELECT 'TR-2026-001', 2, '原始文档归集', '归集正文 1 份、附件 4 份，生成文档指纹',
         '2026-09-16 09:20:00', '系统自动', '《2026年义务教育招生入学工作实施意见》.pdf', '已归档', 'green',
         '凭证编号 PZ-20260916-0002；归集文档 5 份；SHA-256 指纹 7f3a…c21e；归档位置：政务云对象存储 /edu/2026/。'
  UNION ALL SELECT 'TR-2026-001', 3, '知识加工', '由原始文档抽取结构化知识条目 128 条',
         '2026-09-18 09:24:00', '张伟 · 数据资源处', '加工任务 JG-20260918-0012', '已完成', 'green',
         '凭证编号 PZ-20260918-0012；加工任务 JG-20260918-0012；抽取条目 128 条，人工抽检 20 条全部合格。'
  UNION ALL SELECT 'TR-2026-001', 4, '元数据校验', '按字段规范逐项校验，补正 2 处缺失字段',
         '2026-09-18 09:41:00', '系统自动', '元数据字段规范 V2.3（46 项）', '通过', 'green',
         '凭证编号 PZ-20260918-0009；校验规范 V2.3 共 46 项，通过 44 项，补正 2 项后复核通过。'
  UNION ALL SELECT 'TR-2026-001', 5, '审核发布', '经业务处室初审、数据资源处复审后发布',
         '2026-09-19 10:05:00', '李静 · 数据资源处', '发布单 FB-20260919-007', '已发布', 'green',
         '凭证编号 PZ-20260919-0007；发布单 FB-20260919-007；初审：基础教育处 王芳，复审：数据资源处 李静，双签留痕。'
  UNION ALL SELECT 'TR-2026-001', 6, '引用使用', '被政务服务网智能问答、便民服务站终端引用',
         '2026-10-18 16:22:00', '市政务服务网 · 智能问答', '引用记录 YY-20261018-2261', '正常', 'blue',
         '凭证编号 PZ-20261018-2261；累计引用 128 次；引用方：政务服务网智能问答、便民服务站终端（12 台）。'

  UNION ALL SELECT 'TR-2026-002', 1, '数据源接入', '从政策文件库与交易所公告双源同步', '2026-08-02 10:15:00',
         '系统自动', '接口批次 BT20260802-01', '通过', 'green',
         '凭证编号 PZ-20260802-0001；双源比对一致率 100%，时间戳 2026-08-02 10:15:22。'
  UNION ALL SELECT 'TR-2026-002', 2, '原始文档归集', '归集上市扶持政策及配套细则 9 份', '2026-08-02 10:40:00',
         '系统自动', '《企业上市培育扶持办法》等 9 份', '已归档', 'green',
         '凭证编号 PZ-20260802-0004；归集文档 9 份，SHA-256 指纹已登记。'
  UNION ALL SELECT 'TR-2026-002', 3, '知识加工', '拆解为政策要点 86 条、申报事项 12 项', '2026-08-05 14:02:00',
         '陈晨 · 资本市场处', '加工任务 JG-20260805-0006', '已完成', 'green',
         '凭证编号 PZ-20260805-0006；加工任务 JG-20260805-0006；产出政策要点 86 条、申报事项 12 项。'
  UNION ALL SELECT 'TR-2026-002', 4, '元数据校验', '按字段规范校验，一次性通过', '2026-08-05 14:20:00',
         '系统自动', '元数据字段规范 V2.3（46 项）', '通过', 'green',
         '凭证编号 PZ-20260805-0011；46 项校验全部通过。'
  UNION ALL SELECT 'TR-2026-002', 5, '审核发布', '经金融管理局领导审批后发布', '2026-08-06 09:30:00',
         '周敏 · 资本市场处', '发布单 FB-20260806-003', '已发布', 'green',
         '凭证编号 PZ-20260806-0003；审批人：资本市场处负责人，留痕完整。'
  UNION ALL SELECT 'TR-2026-002', 6, '引用使用', '被企业综合服务平台、金融服务专区引用', '2026-10-24 11:18:00',
         '企业综合服务平台', '引用记录 YY-20261024-1180', '正常', 'blue',
         '凭证编号 PZ-20261024-1180；累计引用 96 次。'

  UNION ALL SELECT 'TR-2026-003', 1, '数据源接入', '从工程建设项目审批管理系统同步', '2026-07-11 08:50:00',
         '市住建局 · 审批管理系统', '接口批次 BT20260711-05', '通过', 'green',
         '凭证编号 PZ-20260711-0005；同步办件指南 34 项，校验和一致。'
  UNION ALL SELECT 'TR-2026-003', 2, '原始文档归集', '归集办事指南、申报表单及图示 7 份', '2026-07-11 09:02:00',
         '系统自动', '《施工许可核发办事指南》等 7 份', '已归档', 'green',
         '凭证编号 PZ-20260711-0012；归集文档 7 份，指纹已登记。'
  UNION ALL SELECT 'TR-2026-003', 3, '知识加工', '结构化申报条件 42 项、材料清单 18 项', '2026-07-14 15:26:00',
         '刘洋 · 行政审批处', '加工任务 JG-20260714-0021', '已完成', 'green',
         '凭证编号 PZ-20260714-0021；产出申报条件 42 项、材料清单 18 项。'
  UNION ALL SELECT 'TR-2026-003', 4, '元数据校验', '校验发现 1 处时限字段缺失，已补正', '2026-07-14 15:55:00',
         '系统自动', '元数据字段规范 V2.3（46 项）', '通过', 'green',
         '凭证编号 PZ-20260714-0030；1 项缺失已补正并复核通过。'
  UNION ALL SELECT 'TR-2026-003', 5, '审核发布', '经行政审批处初审、局办复审后发布', '2026-07-15 10:12:00',
         '赵强 · 市住建局办公室', '发布单 FB-20260715-011', '已发布', 'green',
         '凭证编号 PZ-20260715-0011；双审留痕完整。'
  UNION ALL SELECT 'TR-2026-003', 6, '引用使用', '被工程建设项目审批综合服务窗口引用', '2026-10-20 09:40:00',
         '工改综合窗口', '引用记录 YY-20261020-0942', '正常', 'blue',
         '凭证编号 PZ-20261020-0942；累计引用 74 次。'

  UNION ALL SELECT 'TR-2026-004', 1, '数据源接入', '民政业务系统接口同步（部分批次未完成校验）', '2026-09-02 11:05:00',
         '市民政局 · 社会救助系统', '接口批次 BT20260902-08', '待复核', 'warn',
         '凭证编号 PZ-20260902-0008；批次 BT20260902-08 校验未完成，需补录来源确认单。'
  UNION ALL SELECT 'TR-2026-004', 2, '原始文档归集', '归集联办方案与办事指南 5 份', '2026-09-02 11:30:00',
         '系统自动', '《社会救助一件事联办方案》等 5 份', '已归档', 'green',
         '凭证编号 PZ-20260902-0015；归集文档 5 份。'
  UNION ALL SELECT 'TR-2026-004', 3, '知识加工', '抽取联办事项 9 项、材料清单 14 项', '2026-09-04 10:14:00',
         '孙丽 · 社会救助处', '加工任务 JG-20260904-0009', '已完成', 'green',
         '凭证编号 PZ-20260904-0009；产出联办事项 9 项、材料清单 14 项。'
  UNION ALL SELECT 'TR-2026-004', 4, '元数据校验', '按字段规范校验通过', '2026-09-04 10:36:00',
         '系统自动', '元数据字段规范 V2.3（46 项）', '通过', 'green',
         '凭证编号 PZ-20260904-0021；46 项校验通过。'
  UNION ALL SELECT 'TR-2026-004', 5, '审核发布', '待业务处室会签，暂未发布', '2026-09-05 09:00:00',
         '—', '发布单（待生成）', '待发布', 'warn',
         '凭证编号（待生成）；会签流程进行中，发布单尚未生成。'
  UNION ALL SELECT 'TR-2026-004', 6, '引用使用', '暂无引用记录', '2026-10-15 14:30:00',
         '—', '引用记录（暂无）', '未引用', 'warn',
         '暂无引用记录；该主题链路存在缺失环节，需在知识治理中发起整改。'
) n ON n.trace_no = t.trace_no
LEFT JOIN kb_trace_node en ON en.trace_id = t.id AND en.step_no = n.step_no
WHERE en.id IS NULL;
