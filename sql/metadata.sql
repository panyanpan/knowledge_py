-- ============================================================
-- 知识元数据字段定义表（知识元数据管理模块）
-- 执行前提：库已存在（zwfw_zsk），账号有建表权限
-- 幂等：CREATE TABLE IF NOT EXISTS + INSERT ... ON DUPLICATE KEY UPDATE
-- ============================================================

CREATE TABLE IF NOT EXISTS `kb_metadata_field` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `field_code` varchar(100) NOT NULL COMMENT '字段编码（唯一，英文标识）',
  `data_type` varchar(20) NOT NULL DEFAULT 'string' COMMENT '数据类型：string/enum/text/number/date/bool',
  `domain` varchar(20) NOT NULL DEFAULT '基础' COMMENT '所属元数据域：基础/业务/管理/技术',
  `is_required` tinyint NOT NULL DEFAULT '0' COMMENT '是否必填 1=是 0=否',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '状态 1=启用 0=停用',
  `description` varchar(500) DEFAULT NULL COMMENT '字段说明',
  `rule_type` varchar(20) DEFAULT NULL COMMENT '校验规则类型：none/length/regex/enum/range',
  `rule_config` varchar(500) DEFAULT NULL COMMENT '校验规则参数（JSON 文本）',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序值（越大越前）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_field_code` (`field_code`),
  KEY `idx_domain_status` (`domain`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='知识元数据字段定义表';

INSERT INTO `kb_metadata_field`
(`field_name`,`field_code`,`data_type`,`domain`,`is_required`,`status`,`description`,`rule_type`,`rule_config`,`sort_order`) VALUES
('知识标题','knowledge_title','string','基础',1,1,'用于知识条目的名称展示与检索，长度 2~120 字','length','{"min":2,"max":120}',100),
('知识分类编码','category_code','enum','基础',1,1,'关联知识分类目录，取自分类树叶子节点','enum','{"source":"category_tree"}',95),
('业务场景名称','biz_scene_name','string','业务',1,1,'知识适用的政务服务事项或专题名称，与场景库同源','length','{"min":2,"max":100}',90),
('事项统一编码','item_unified_code','string','基础',1,1,'对应政务服务事项目录中的统一编码，18 位','regex','{"pattern":"^[0-9]{18}$"}',85),
('适用对象','apply_target','enum','业务',1,1,'自然人 / 法人 / 个体工商户 / 其他组织，支持多选','enum','{"options":["自然人","法人","个体工商户","其他组织"]}',80),
('政策依据','policy_basis','string','业务',0,1,'引用法律法规或规范性文件，需填写文号与生效日期',NULL,NULL,75),
('时效状态','validity_status','enum','管理',1,0,'现行有效 / 已废止 / 即将失效，由人工审核环节确认','enum','{"options":["现行有效","已废止","即将失效"]}',70),
('责任部门','responsible_dept','string','管理',1,1,'知识内容的维护主体，需精确到内设机构','length','{"min":2,"max":100}',65),
('密级与共享类型','sec_level','enum','管理',1,1,'公开 / 内部 / 受限，与知识权限管理联动','enum','{"options":["公开","内部","受限"]}',60),
('数据来源系统','source_system','string','技术',1,1,'接入来源系统标识，用于知识加工与数据同步溯源','length','{"min":2,"max":100}',55),
('版本号','version_no','string','技术',0,1,'采用语义化版本 V 主.次，知识加工后自动递增','regex','{"pattern":"^V[0-9]+([.][0-9]+)?$"}',50),
('知识摘要（AI 生成）','ai_summary','text','技术',0,0,'由大模型抽取生成的内容摘要，需人工复核后方可对外发布',NULL,NULL,45)
ON DUPLICATE KEY UPDATE `field_name`=VALUES(`field_name`), `domain`=VALUES(`domain`);
