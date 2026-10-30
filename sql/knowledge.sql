-- ============================================================
-- 知识管理模块 · 种子数据脚本
-- 执行方式：python scripts/run_knowledge.py（幂等，可重复执行）
-- 说明：kb_entry 的知识管理扩展字段由 run_knowledge.py 先按需 ALTER 补齐：
--   knowledge_type varchar(30)  NOT NULL DEFAULT '事项知识'  知识类型
--   source_dept    varchar(100) NOT NULL DEFAULT ''          来源部门
--   keywords       varchar(255) NOT NULL DEFAULT ''          关键词（英文逗号分隔）
--   status         tinyint      NOT NULL DEFAULT 1            0=草稿 1=已发布 2=已下线
--   publish_at     datetime     NULL                          发布时间
-- 本文件只负责：分类树 + 示例知识 + 标签关联，全部 INSERT ... WHERE NOT EXISTS 幂等
-- ============================================================

-- ---------- 1. 政务知识分类树 ----------
SET @root := (SELECT id FROM kb_category WHERE name = '政务知识资源' AND parent_id = 0 AND is_deleted = 0 ORDER BY id LIMIT 1);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT 0, '政务知识资源', 1, '', 100
WHERE NOT EXISTS (
  SELECT 1 FROM (SELECT id FROM kb_category WHERE name = '政务知识资源' AND parent_id = 0 AND is_deleted = 0) x
);

SET @root := (SELECT id FROM kb_category WHERE name = '政务知识资源' AND parent_id = 0 AND is_deleted = 0 ORDER BY id LIMIT 1);
UPDATE kb_category SET path = CAST(id AS CHAR) WHERE id = @root AND (path IS NULL OR path = '');

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '政务服务事项', 2, '', 60
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '政务服务事项' AND is_deleted = 0) x);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '政策法规', 2, '', 50
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '政策法规' AND is_deleted = 0) x);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '高效办成一件事', 2, '', 40
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '高效办成一件事' AND is_deleted = 0) x);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '办事指南', 2, '', 30
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '办事指南' AND is_deleted = 0) x);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '常见问答', 2, '', 20
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '常见问答' AND is_deleted = 0) x);

INSERT INTO kb_category (parent_id, name, level, path, sort_order)
SELECT @root, '数据标准规范', 2, '', 10
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_category WHERE parent_id = @root AND name = '数据标准规范' AND is_deleted = 0) x);

UPDATE kb_category SET path = CONCAT(@root, '/', id) WHERE parent_id = @root AND (path IS NULL OR path = '');

SET @c_item   := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '政务服务事项' AND is_deleted = 0 ORDER BY id LIMIT 1);
SET @c_policy := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '政策法规' AND is_deleted = 0 ORDER BY id LIMIT 1);
SET @c_thing  := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '高效办成一件事' AND is_deleted = 0 ORDER BY id LIMIT 1);
SET @c_guide  := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '办事指南' AND is_deleted = 0 ORDER BY id LIMIT 1);
SET @c_faq    := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '常见问答' AND is_deleted = 0 ORDER BY id LIMIT 1);
SET @c_std    := (SELECT id FROM kb_category WHERE parent_id = @root AND name = '数据标准规范' AND is_deleted = 0 ORDER BY id LIMIT 1);

SET @admin := (SELECT id FROM sys_user WHERE username = 'admin' AND is_deleted = 0 LIMIT 1);
SET @admin := IFNULL(@admin, 1);

-- ---------- 2. 标签字典 ----------
INSERT IGNORE INTO kb_tag (name) VALUES
('一网通办'),('企业开办'),('政策解读'),('跨省通办'),('一件事'),('办事指南'),
('电子证照'),('数据标准'),('常见问题'),('材料清单'),('社会保险'),('民生保障'),
('营商环境'),('数据共享'),('标准化'),('知识管理'),('工程建设项目'),('不动产登记'),('元数据');

-- ---------- 3. 示例知识：政务服务事项知识 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '企业开办“一网通办”事项办理知识',
'<h3>事项概述</h3><p>企业开办“一网通办”整合设立登记、印章刻制、发票申领、社保登记、公积金开户等环节，实现“一次填报、一网通办、一日办结”。</p><h3>办理要素</h3><ul><li>实施主体：县级以上市场监督管理部门</li><li>办件类型：即办件，承诺时限 1 个工作日</li><li>申请材料：企业名称、经营范围、住所信息、法定代表人身份证明、章程或合伙协议</li><li>收费标准：不收费（印章刻制按地方政策执行）</li></ul><h3>知识要点</h3><p>名称自主申报通过后信息保留 30 日；经营范围应使用规范目录表述；住所实行申报承诺制，需留存合法使用证明备查。</p>',
'整合设立登记、印章刻制、发票申领、社保登记等环节，实现一次填报、一网通办、一日办结。',
1, 328, '事项知识', '省市场监督管理局', '企业开办,一网通办,商事登记', 1,
DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '企业开办“一网通办”事项办理知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '建筑工程施工许可证核发事项知识',
'<h3>事项概述</h3><p>建筑工程施工许可证是工程开工的法定前置条件，由县级以上住房和城乡建设主管部门核发。</p><h3>办理要素</h3><ul><li>办件类型：承诺件，承诺时限 7 个工作日</li><li>申请材料：用地批准文件、建设工程规划许可证、施工图设计文件审查合格书、中标通知书、质量安全监督手续</li><li>收费标准：不收费</li></ul><h3>常见退回原因</h3><p>施工图审查合格书与申报工程不一致、建设资金落实证明缺失、施工单位安全生产许可证过期。</p>',
'工程开工法定前置许可，需用地批准、规划许可、施工图审查等材料，承诺 7 个工作日办结。',
1, 214, '事项知识', '省住房和城乡建设厅', '工程建设项目,施工许可,材料清单', 1,
DATE_SUB(NOW(), INTERVAL 9 DAY), DATE_SUB(NOW(), INTERVAL 9 DAY), DATE_SUB(NOW(), INTERVAL 9 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '建筑工程施工许可证核发事项知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '食品经营许可证核发事项知识',
'<h3>事项概述</h3><p>从事食品销售和餐饮服务活动，应当依法取得食品经营许可，按经营项目分类核定。</p><h3>办理要素</h3><ul><li>实施主体：县级以上市场监督管理部门</li><li>承诺时限：10 个工作日（告知承诺制 1 个工作日）</li><li>申请材料：申请书、营业执照、经营场所平面布局图、食品安全管理制度、从业人员健康证明</li></ul><h3>知识要点</h3><p>仅销售预包装食品的，实行备案管理，无需办理许可证；网络经营需同步填报网络经营项目。</p>',
'食品销售与餐饮服务须取得经营许可，告知承诺制可 1 个工作日办结，预包装食品销售改为备案。',
1, 176, '事项知识', '省市场监督管理局', '食品药品,准入准营,告知承诺', 1,
DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '食品经营许可证核发事项知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '失业保险金申领事项知识',
'<h3>事项概述</h3><p>参保失业人员符合缴费满 1 年、非因本人意愿中断就业等条件的，可申领失业保险金。</p><h3>办理要素</h3><ul><li>实施主体：参保地失业保险经办机构</li><li>办件类型：即办件，线上申领 1 个工作日内审核</li><li>申请材料：社会保障卡或身份证、解除劳动关系证明（系统可核验时免提交）</li><li>待遇标准：按缴费年限核定领取月数，最长不超过 24 个月</li></ul><h3>知识要点</h3><p>失业登记与待遇申领可“一件事”联办；领取期间由经办机构代缴职工基本医疗保险费。</p>',
'参保失业人员线上即可申领失业保险金，失业登记与待遇申领联办，领取期间代缴医保。',
1, 265, '事项知识', '省人力资源和社会保障厅', '社会保险,失业保险,民生保障', 1,
DATE_SUB(NOW(), INTERVAL 22 DAY), DATE_SUB(NOW(), INTERVAL 22 DAY), DATE_SUB(NOW(), INTERVAL 22 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '失业保险金申领事项知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '不动产登记（存量房转移）事项知识',
'<h3>事项概述</h3><p>存量房买卖、赠与、互换等导致权属转移的，应申请转移登记，实行“一窗受理、并行办理”。</p><h3>办理要素</h3><ul><li>实施主体：不动产所在地登记机构</li><li>承诺时限：3 个工作日（一般登记）</li><li>申请材料：登记申请书、身份证明、不动产权属证书、买卖合同、税费缴纳凭证</li><li>收费标准：住宅类登记费 80 元/件</li></ul><h3>知识要点</h3><p>水电气过户可与转移登记同步申请；存在抵押的需先办理抵押注销或同步办理带押过户。</p>',
'存量房转移登记一窗受理，承诺 3 个工作日办结，可同步办理水电气过户与带押过户。',
1, 189, '事项知识', '省自然资源厅', '不动产登记,一窗受理,存量房', 1,
DATE_SUB(NOW(), INTERVAL 34 DAY), DATE_SUB(NOW(), INTERVAL 34 DAY), DATE_SUB(NOW(), INTERVAL 34 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '不动产登记（存量房转移）事项知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_item, @admin, '出生医学证明签发事项知识',
'<h3>事项概述</h3><p>出生医学证明由助产机构签发，是办理户口登记、医保参保、预防接种等事项的重要凭证。</p><h3>办理要素</h3><ul><li>实施主体：具备签发资质的助产机构</li><li>办件类型：即办件</li><li>申请材料：新生儿父母有效身份证件、分娩记录</li><li>办理渠道：助产机构窗口、政务服务网、移动端</li></ul><h3>知识要点</h3><p>出生医学证明与户口登记、医保参保、社保卡申领可“一件事”联办，一次提交、多证同发。</p>',
'出生医学证明由助产机构签发，可与户口登记、医保参保、社保卡申领一件事联办。',
1, 142, '事项知识', '省卫生健康委员会', '出生,民生保障,一件事', 1,
DATE_SUB(NOW(), INTERVAL 47 DAY), DATE_SUB(NOW(), INTERVAL 47 DAY), DATE_SUB(NOW(), INTERVAL 47 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '出生医学证明签发事项知识' AND is_deleted = 0) x);

-- ---------- 4. 示例知识：政务政策法规 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_policy, @admin, '《优化营商环境条例》核心条款解读',
'<h3>立法定位</h3><p>条例是我国营商环境领域第一部综合性行政法规，确立了对各类市场主体一视同仁、平等保护的基本导向。</p><h3>核心条款</h3><ul><li>市场主体保护：不得违法干预市场主体自主决策，不得设置不合理条件限制市场准入</li><li>政务服务：推行“一网通办”“最多跑一次”，压缩办理时限、精简申请材料</li><li>监管执法：推行“双随机、一公开”，避免多头重复检查</li></ul><h3>落地要求</h3><p>各级政务服务机构应对照条例清理证明事项，公布事项清单与办事指南，确保线上线下一致。</p>',
'营商环境领域首部综合性行政法规，明确市场主体保护、一网通办、双随机一公开等核心要求。',
1, 412, '政策法规', '省发展和改革委员会', '营商环境,政策解读,市场主体', 1,
DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '《优化营商环境条例》核心条款解读' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_policy, @admin, '《政务数据共享条例》要点与落地要求',
'<h3>适用范围</h3><p>规范政务数据的目录管理、共享使用、安全保障与监督评价，推动数据“一次采集、多方复用”。</p><h3>关键要求</h3><ul><li>目录管理：政务数据实行目录化管理，未列入目录的数据不得对外提供</li><li>共享原则：以共享为原则，不共享为例外，按无条件共享、有条件共享、不予共享分类</li><li>安全管理：落实数据分类分级保护，明确共享使用全过程留痕</li></ul><h3>落地建议</h3><p>建立政务数据共享责任清单，逐项明确共享方式、更新频率与责任处室，并与事项材料精简联动。</p>',
'政务数据目录化管理、以共享为原则，需建立共享责任清单并与材料精简联动。',
1, 356, '政策法规', '省政务服务和数据管理局', '数据共享,政策解读,数据治理', 1,
DATE_SUB(NOW(), INTERVAL 11 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '《政务数据共享条例》要点与落地要求' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_policy, @admin, '政务服务“跨省通办”政策要点',
'<h3>政策目标</h3><p>围绕高频政务服务事项，通过全程网办、异地代收代办、多地联办三种方式实现跨省办理。</p><h3>三种模式</h3><ul><li>全程网办：事项全流程线上办理，异地可办、结果快递送达</li><li>异地代收代办：由收件地窗口代收，转属地办理</li><li>多地联办：多地部门协同，一次申请、并联审批</li></ul><h3>知识要点</h3><p>跨省通办事项应统一事项名称、编码、材料、时限，并在政务服务网设置专区，明确办理渠道与联系人。</p>',
'跨省通办分全程网办、异地代收代办、多地联办三种模式，须统一事项要素并设专区。',
1, 298, '政策法规', '省政务服务和数据管理局', '跨省通办,政策解读,区域协同', 1,
DATE_SUB(NOW(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 18 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务“跨省通办”政策要点' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_policy, @admin, '《行政许可法》行政许可程序要点',
'<h3>设定与实施</h3><p>行政许可由法律、行政法规设定，实施机关应在法定权限内行使，不得增设法定条件以外的条件。</p><h3>程序要求</h3><ul><li>受理：材料不齐全应一次性告知补正内容</li><li>审查与决定：能当场决定的当场决定，不能的应在法定期限内作出</li><li>听证：涉及公共利益或重大利益关系的应告知听证权利</li><li>期限：一般 20 日，可依法延长 10 日</li></ul><h3>知识要点</h3><p>不得以备案、登记、年检、监制等名义变相设定许可，也不得指定中介服务。</p>',
'行政许可实施程序、期限与一次性告知要求，禁止以备案年检名义变相设许可。',
1, 203, '政策法规', '省司法厅', '依法行政,政策解读,行政许可', 1,
DATE_SUB(NOW(), INTERVAL 26 DAY), DATE_SUB(NOW(), INTERVAL 26 DAY), DATE_SUB(NOW(), INTERVAL 26 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '《行政许可法》行政许可程序要点' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_policy, @admin, '政务服务标准化规范化便利化建设要求',
'<h3>总体要求</h3><p>以标准化为基础、规范化为保障、便利化为目标，推动政务服务从“可办”向“好办、易办”转变。</p><h3>三项任务</h3><ul><li>标准化：统一事项名称、编码、类型、依据、材料、流程、时限与结果</li><li>规范化：规范审批自由裁量权，推行告知承诺制与容缺受理</li><li>便利化：推进“一网通办”“一件事一次办”、免证办与就近办</li></ul><h3>评价机制</h3><p>以“好差评”结果、办件时限压缩率、材料精简率作为主要考核指标。</p>',
'以标准化为基础、规范化保障、便利化为目标，统一事项要素并推行告知承诺与容缺受理。',
1, 241, '政策法规', '省政务服务和数据管理局', '标准化,政策解读,一件事', 1,
DATE_SUB(NOW(), INTERVAL 40 DAY), DATE_SUB(NOW(), INTERVAL 40 DAY), DATE_SUB(NOW(), INTERVAL 40 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务标准化规范化便利化建设要求' AND is_deleted = 0) x);

-- ---------- 5. 示例知识：高效办成一件事 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_thing, @admin, '企业开办“一件事”集成办理知识',
'<h3>集成范围</h3><p>整合企业设立登记、印章刻制、发票申领、社保登记、公积金开户、银行预约开户 6 个环节，一次填报、一次提交。</p><h3>办理流程</h3><ul><li>第一步：企业名称自主申报，确定经营范围与住所</li><li>第二步：一表填报，系统自动分发至各业务部门</li><li>第三步：并联办理，营业执照 0.5 个工作日核发</li><li>第四步：结果统一送达，电子证照同步生成</li></ul><h3>知识要点</h3><p>重复材料由系统复用，法定代表人身份证明只提交一次；银行开户可预约上门。</p>',
'整合设立登记、印章刻制、发票申领等 6 个环节，一表填报、并联办理、结果统一送达。',
1, 389, '一件事知识', '省市场监督管理局', '一件事,企业开办,集成办理', 1,
DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '企业开办“一件事”集成办理知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_thing, @admin, '新生儿出生“一件事”联办知识',
'<h3>集成范围</h3><p>出生医学证明签发、出生户口登记、城乡居民医保参保、社保卡申领、预防接种证办理 5 项事项联办。</p><h3>办理流程</h3><ul><li>线上：政务服务网或移动端“出生一件事”专区，一次填报、多证联办</li><li>线下：助产机构“出生一件事”综合窗口</li><li>时限：3 个工作日内完成，证件邮寄到家</li></ul><h3>知识要点</h3><p>需父母双方身份证、结婚证信息核验通过；姓名需符合户籍登记规范，避免生僻字无法制证。</p>',
'出生证明、户口登记、医保参保、社保卡、预防接种证 5 项联办，3 个工作日办结。',
1, 310, '一件事知识', '省卫生健康委员会', '一件事,出生,民生保障', 1,
DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '新生儿出生“一件事”联办知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_thing, @admin, '退休“一件事”办理知识',
'<h3>集成范围</h3><p>企业职工基本养老保险待遇申领、退休证办理、医保关系转移、公积金提取等事项打包联办。</p><h3>办理要素</h3><ul><li>适用对象：达到法定退休年龄且缴费年限满 15 年的参保人员</li><li>申请材料：身份证、社会保障卡、人事档案（视同缴费年限核定需要）</li><li>承诺时限：15 个工作日</li></ul><h3>知识要点</h3><p>档案出生时间与身份证不一致时，以档案最先记载为准；提前退休需提供特殊工种或病退鉴定材料。</p>',
'养老待遇申领、退休证、医保转移、公积金提取打包联办，承诺 15 个工作日。',
1, 256, '一件事知识', '省人力资源和社会保障厅', '一件事,社会保险,退休', 1,
DATE_SUB(NOW(), INTERVAL 13 DAY), DATE_SUB(NOW(), INTERVAL 13 DAY), DATE_SUB(NOW(), INTERVAL 13 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '退休“一件事”办理知识' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_thing, @admin, '军人退役“一件事”办理知识',
'<h3>集成范围</h3><p>退役报到、户口登记、社保关系接续、医保参保、预备役登记、一次性经济补助申领等联办。</p><h3>办理流程</h3><ul><li>退役军人事务部门“一站式”服务窗口受理</li><li>材料内部流转，避免退役士兵多部门跑动</li><li>承诺时限：10 个工作日</li></ul><h3>知识要点</h3><p>退役证明、行政介绍信为关键材料；社保关系接续需核对部队缴费记录，缺失时由安置地协助核查。</p>',
'退役报到、落户、社保接续、医保参保等一站式联办，承诺 10 个工作日。',
1, 148, '一件事知识', '省退役军人事务厅', '一件事,军人退役,一站式', 1,
DATE_SUB(NOW(), INTERVAL 29 DAY), DATE_SUB(NOW(), INTERVAL 29 DAY), DATE_SUB(NOW(), INTERVAL 29 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '军人退役“一件事”办理知识' AND is_deleted = 0) x);

-- ---------- 6. 示例知识：办事指南 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_guide, @admin, '政务服务网用户注册与实名认证指南',
'<h3>适用对象</h3><p>自然人用户、法人用户首次使用政务服务网办理业务前的账号注册与实名认证。</p><h3>操作步骤</h3><ul><li>第一步：进入政务服务网首页，点击注册，选择个人或法人类型</li><li>第二步：填写手机号并完成短信验证，设置登录密码</li><li>第三步：选择实名方式，人脸识别或银行卡要素核验</li><li>第四步：认证通过后即可在线申报，可同步申领电子证照</li></ul><h3>常见问题</h3><p>手机号已注册可直接找回密码；法人用户需法定代表人先完成个人实名认证再绑定企业。</p>',
'个人与法人用户注册、短信验证、人脸识别实名认证的完整操作步骤与常见问题。',
1, 520, '办事指南', '省政务服务和数据管理局', '办事指南,实名认证,账号', 1,
DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务网用户注册与实名认证指南' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_guide, @admin, '电子证照调用与核验操作指南',
'<h3>适用场景</h3><p>办事材料中的营业执照、身份证、结婚证等已归集电子证照的，可免于提交纸质材料。</p><h3>操作步骤</h3><ul><li>申报时勾选“电子证照共享”，系统自动调取本人名下证照</li><li>窗口办理时出示电子证照亮码，由工作人员扫码核验</li><li>核验结果以电子签章与二维码双重校验为准</li></ul><h3>注意事项</h3><p>电子证照与纸质证照具有同等效力；证照信息变更后需重新归集，避免调用到历史版本。</p>',
'已归集电子证照可免交纸质材料，申报勾选共享或窗口亮码核验，与纸质证照同等效力。',
1, 331, '办事指南', '省政务服务和数据管理局', '电子证照,办事指南,免证办', 1,
DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '电子证照调用与核验操作指南' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_guide, @admin, '政务服务“好差评”评价操作指南',
'<h3>评价范围</h3><p>线上线下办理的政务服务事项均可评价，评价结果分为非常满意、满意、基本满意、不满意、非常不满意五级。</p><h3>操作步骤</h3><ul><li>线上：办件办结后进入“我的办件”，点击评价</li><li>线下：窗口评价器、二维码扫码评价</li><li>未评价的，系统在办结后 5 个工作日内提醒</li></ul><h3>结果运用</h3><p>“不满意”评价 24 小时内转办核实，整改结果反馈评价人；评价数据纳入部门政务服务考核。</p>',
'五级评价体系、线上线下评价入口、不满意件 24 小时转办核实与结果运用机制。',
1, 197, '办事指南', '省政务服务中心', '好差评,办事指南,监督评价', 1,
DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 20 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务“好差评”评价操作指南' AND is_deleted = 0) x);

-- ---------- 7. 示例知识：常见问答 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_faq, @admin, '办事材料被退回的常见原因与处理',
'<h3>常见退回原因</h3><ul><li>材料不齐全：未按办事指南逐项上传，缺少签章或日期</li><li>材料不一致：证明文件信息与申报信息不一致，如住所地址、法定代表人姓名</li><li>格式不合规：扫描件模糊、非原件彩色扫描、图片方向倒置</li><li>超出有效期：身份证、资质证书、健康证明已过期</li></ul><h3>处理建议</h3><p>按退回意见一次性补正；对一次性告知内容有异议的，可通过“好差评”或12345热线反映。</p>',
'材料不齐、信息不一致、格式不合规、证件过期是四类主要退回原因，按一次性告知补正。',
1, 173, '常见问答', '省政务服务中心', '常见问题,材料清单,退件', 1,
DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 12 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '办事材料被退回的常见原因与处理' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_faq, @admin, '政务服务平台登录异常处理问答',
'<h3>问：提示账号或密码错误怎么办？</h3><p>先确认登录入口是否为统一认证平台，再通过“忘记密码”按手机号重置；连续 5 次失败账号将临时锁定 30 分钟。</p><h3>问：人脸识别一直不通过？</h3><p>检查光线与网络，摘除口罩眼镜；多次失败可切换银行卡要素核验方式。</p><h3>问：法人账号看不到企业信息？</h3><p>需法定代表人先完成个人实名认证，并在企业授权中确认经办人权限。</p>',
'账号锁定、人脸识别失败、法人账号无企业信息三类登录异常的排查与处理方式。',
1, 158, '常见问答', '省政务服务和数据管理局', '常见问题,账号,实名认证', 1,
DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 25 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务平台登录异常处理问答' AND is_deleted = 0) x);

-- ---------- 8. 示例知识：数据标准规范 ----------
INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_std, @admin, '政务服务事项元数据编制规范要点',
'<h3>元数据框架</h3><p>事项元数据分为基础属性、业务属性、管理属性、技术属性四类，共 12 个核心字段。</p><h3>核心字段要求</h3><ul><li>事项统一编码：18 位数字，全国唯一，作为跨系统关联主键</li><li>事项名称：与部门权责清单一致，不得自行增减字词</li><li>办件类型：即办件、承诺件，与承诺时限匹配</li><li>申请材料：需逐项标注来源渠道与可免提交情形</li></ul><h3>质量要求</h3><p>元数据完整率、准确率纳入政务服务数据质量考核，缺项字段须在 5 个工作日内补全。</p>',
'事项元数据四类 12 个核心字段，统一编码 18 位，完整率与准确率纳入数据质量考核。',
0, 121, '数据标准', '省政务服务和数据管理局', '数据标准,元数据,事项标准化', 0,
NULL, DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务服务事项元数据编制规范要点' AND is_deleted = 0) x);

INSERT INTO kb_entry
(category_id, author_id, title, content, summary, visibility, view_count, knowledge_type, source_dept, keywords, status, publish_at, created_at, updated_at)
SELECT @c_std, @admin, '政务知识库分类与编码规范要点',
'<h3>分类原则</h3><p>按“主题—业务域—知识类型”三级组织，主题层保持稳定，业务域可随改革任务扩展。</p><h3>编码规则</h3><ul><li>分类编码：4 位数字，前 2 位为主题码，后 2 位为业务域序号</li><li>知识编码：分类编码 + 6 位流水号，全局唯一</li><li>标签：不受层级约束，用于跨类聚合与检索召回</li></ul><h3>维护要求</h3><p>分类调整需评估存量知识的影响范围，保留历史编码映射关系，避免知识检索断链。</p>',
'主题—业务域—知识类型三级分类，编码 4 位数字加流水号，标签用于跨类聚合。',
2, 96, '数据标准', '省政务服务和数据管理局', '数据标准,知识管理,分类编码', 2,
DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_SUB(NOW(), INTERVAL 16 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY)
WHERE NOT EXISTS (SELECT 1 FROM (SELECT id FROM kb_entry WHERE title = '政务知识库分类与编码规范要点' AND is_deleted = 0) x);

-- ---------- 9. 标签关联（按标题匹配，幂等） ----------
INSERT IGNORE INTO kb_entry_tag (entry_id, tag_id)
SELECT e.id, t.id FROM kb_entry e CROSS JOIN kb_tag t
WHERE e.is_deleted = 0 AND (
  (e.title = '企业开办“一网通办”事项办理知识' AND t.name IN ('企业开办','一网通办'))
  OR (e.title = '建筑工程施工许可证核发事项知识' AND t.name IN ('工程建设项目','材料清单'))
  OR (e.title = '食品经营许可证核发事项知识' AND t.name IN ('材料清单','一网通办'))
  OR (e.title = '失业保险金申领事项知识' AND t.name IN ('社会保险','民生保障'))
  OR (e.title = '不动产登记（存量房转移）事项知识' AND t.name IN ('不动产登记','一网通办'))
  OR (e.title = '出生医学证明签发事项知识' AND t.name IN ('民生保障','一件事'))
  OR (e.title = '《优化营商环境条例》核心条款解读' AND t.name IN ('营商环境','政策解读'))
  OR (e.title = '《政务数据共享条例》要点与落地要求' AND t.name IN ('数据共享','政策解读'))
  OR (e.title = '政务服务“跨省通办”政策要点' AND t.name IN ('跨省通办','政策解读'))
  OR (e.title = '《行政许可法》行政许可程序要点' AND t.name IN ('政策解读','标准化'))
  OR (e.title = '政务服务标准化规范化便利化建设要求' AND t.name IN ('标准化','一件事'))
  OR (e.title = '企业开办“一件事”集成办理知识' AND t.name IN ('一件事','企业开办'))
  OR (e.title = '新生儿出生“一件事”联办知识' AND t.name IN ('一件事','民生保障'))
  OR (e.title = '退休“一件事”办理知识' AND t.name IN ('一件事','社会保险'))
  OR (e.title = '军人退役“一件事”办理知识' AND t.name IN ('一件事','民生保障'))
  OR (e.title = '政务服务网用户注册与实名认证指南' AND t.name IN ('办事指南','一网通办'))
  OR (e.title = '电子证照调用与核验操作指南' AND t.name IN ('电子证照','办事指南'))
  OR (e.title = '政务服务“好差评”评价操作指南' AND t.name IN ('办事指南','标准化'))
  OR (e.title = '办事材料被退回的常见原因与处理' AND t.name IN ('常见问题','材料清单'))
  OR (e.title = '政务服务平台登录异常处理问答' AND t.name IN ('常见问题','一网通办'))
  OR (e.title = '政务服务事项元数据编制规范要点' AND t.name IN ('数据标准','元数据'))
  OR (e.title = '政务知识库分类与编码规范要点' AND t.name IN ('数据标准','知识管理'))
);
