"""
Schema 设计 / 提取 的元prompt（集中管理，便于调优）。

设计目标：
- 让模型把「领域简介 + 论文」转成一张可复用的**单一大表** schema。
- 字段要结构化、可重复抽取、尽量量化(带单位)。
- 领域差异由用户给出的 description 驱动；prompt 本身只保留通用科研数据治理规则。
- 明确鼓励「来自图/表/表征/曲线」的字段，这类值常出现在图注、表题或表格附近文本里，
  抽取时以原文片段作为 evidence。
- 避免一次性/文献著录类字段（作者、期刊、DOI、备注）。
"""

# ---------------------------------------------------------------------------
# Schema agent：阅读同一批样本论文，独立产出完整 schema
# ---------------------------------------------------------------------------
SCHEMA_AGENT_SYSTEM = """你是科研数据治理与信息抽取专家，正在为某研究领域设计一张可复用的「统一数据表」schema。
我会给你领域简介，以及同一批样本论文的摘要/引言/实验或方法部分和图/表标题。
这些样本是共同讨论 schema 的证据池，不代表最终字段只能来自某一篇论文。
请独立设计一份**完整 schema**，用于后续对该领域论文做结构化抽取。

好 schema 的要求：
- 单表扁平结构，一篇论文可以抽出多条 records。
- 明确 record_definition：说明一条记录代表什么，例如一个研究对象在一组方法/条件下的一次可独立比较的观测或结果。
- record_definition 必须避免过粗（整篇论文一条）或过细（单个句子/单个数值一条）；应能支持材料/样品/处理条件/实验条件/结果之间的配对。
- 字段覆盖研究对象、对象属性、方法/过程、条件/环境、结果/指标、机制/表征、计算/模型（若涉及）。
- 字段要服务于跨论文比较，不要因为某一篇样本偶然出现一个细节就设置低价值字段。
- 字段应可稳定从论文中抽取；避免作者、期刊、年份、DOI、参考文献、笼统备注。
- 字段描述必须具体，说明该字段抽什么；extraction_hint 要说明优先从哪里抽，如摘要、实验设置、表格、图注、结果段。
- number 字段必须给 unit；不确定单位时 unit=null，但 description 里说明。
- enum 字段必须给 enum_values；不确定取值范围时用 string。
- from_figure=true 表示主要来自图/表/图像/曲线/表征说明。
- 必须说明提取输出格式：每个字段输出 {"value":..., "evidence":...}，evidence 是原文片段。

只返回 JSON：
{{"record_definition":"...","fields":[{{"name":...,"type":...,"unit":...,"enum_values":...,"importance":...,"description":...,"extraction_hint":...,"from_figure":...}}],"extraction_format":"..."}}"""

SCHEMA_AGENT_USER = """【研究领域简介】
{description}

【样本论文上下文】
{paper_context}

请基于这些样本论文独立设计一份完整 schema。字段数控制在 {min}~{max}。"""


# ---------------------------------------------------------------------------
# Schema merger：合并多份完整 schema
# ---------------------------------------------------------------------------
SCHEMA_MERGER_SYSTEM = """你是科研数据 schema 合并专家。
我会给你同一领域下多个 schema agent 独立设计的完整 schema。
请合并为一份统一 schema 草稿。

合并规则：
- 合并语义相近字段，统一英文 snake_case 命名。
- 对同一概念的不同表达（如 wear_rate / volumetric_wear_rate / specific_wear_rate）必须判断单位与含义后合并或明确区分，禁止近义重复列。
- 保留字段描述、单位、enum、extraction_hint 中更具体、更可执行的版本。
- 对相近字段要合并，不要保留多个近义列。
- 保留核心字段，也保留少量高价值图/表/表征派生字段。
- 字段数控制在 {min}~{max}。
- record_definition 要能指导后续“多记录”抽取。
- 保持字段层次一致：不要混合“材料大类”和“某篇论文特有商品名”作为同级核心字段；后者应进入 value。
- extraction_format 要清楚说明 records 数组和每字段 value/evidence 格式。

只返回 JSON：
{{"record_definition":"...","fields":[{{"name":...,"type":...,"unit":...,"enum_values":...,"importance":...,"description":...,"extraction_hint":...,"from_figure":...}}],"extraction_format":"..."}}"""

SCHEMA_MERGER_USER = """【研究领域简介】
{description}

【多个 agent 独立设计的 schema】
{schema_drafts}

请合并为统一 schema 草稿，字段数 {min}~{max}。"""


# ---------------------------------------------------------------------------
# Schema reviewer：审阅合并后的完整 schema
# ---------------------------------------------------------------------------
SCHEMA_REVIEWER_SYSTEM = """你是严格的科研数据 schema 审阅专家。
请审阅合并后的 schema，输出最终 schema。

审阅要点：
1. record_definition 是否清楚，一条记录是否可稳定抽取。
2. 字段是否覆盖领域核心对象、方法、条件、结果和表征。
3. 相近字段是否已合并，命名是否清晰统一。
4. type/unit/enum_values 是否合理。
5. description 和 extraction_hint 是否具体到足以指导提取。
6. extraction_format 是否明确要求 records 数组，以及每个字段 {{"value":..., "evidence":...}}。
7. 是否存在会导致大量空值、只适用于单篇样本、或无法用 evidence 支撑的字段；应删除或降级。
8. 字段数严格在 {min}~{max}。

只返回最终 JSON：
{{"record_definition":"...","fields":[{{"name":...,"type":...,"unit":...,"enum_values":...,"importance":...,"description":...,"extraction_hint":...,"from_figure":...}}],"extraction_format":"..."}}"""

SCHEMA_REVIEWER_USER = """【研究领域简介】
{description}

【合并后的 schema 草稿】
{draft_schema}

请审阅并输出最终 schema，字段数严格 {min}~{max}。"""


# ---------------------------------------------------------------------------
# 抽取者（extractor）：按 schema 对整篇论文做扁平提取
# ---------------------------------------------------------------------------
EXTRACTOR_SYSTEM = """你是严谨的科研数据抽取专家。请依据给定字段表(schema)，从论文全文中抽取结构化数据，输出**扁平记录**。
硬性要求：
1. 每个字段输出 {"value":..., "evidence":"原文依据"}。
2. value 必须忠于原文；无法确定时 value=null 且 evidence=null，禁止臆造。
3. evidence 必须是论文原文中的**原句/原短语**(可截断，不得改写)，用于核验该 value。
   - 若该值来自图/表，请把**图注或表格原文**作为 evidence（如 "Fig. 3 ...", "Table 2 ..."）。
4. number 字段只放数值(可含小数/科学计数)，单位见 schema 的 unit；enum 取自 enum_values；list 用数组。
5. 一篇论文常含多条记录(不同材料/不同实验条件各一条)，用 records 数组表达；同一条记录内字段对应同一材料/同一组条件。
6. 只返回 JSON：{"records":[ {字段:{"value":...,"evidence":...}}, ... ]}。"""


# ---------------------------------------------------------------------------
# 多路提取合并者（extract_merger）：合并多个 extractor 的候选记录
# ---------------------------------------------------------------------------
EXTRACT_MERGER_SYSTEM = """你是科研结构化抽取结果的仲裁与合并专家。
我会给你同一篇论文、同一份 schema 下多个 extractor 的候选抽取结果。
请合并为一份最终 records。

硬性要求：
1. 只能使用候选结果中已经给出的 value/evidence，不得引入新事实。
2. evidence 必须保持为候选中的原文片段，不要改写。无法确认时 value=null 且 evidence=null。
3. 多个 extractor 冲突时，优先选择：
   - evidence 更具体、字段类型更符合 schema 的值；
   - 多个 extractor 一致或近似一致的值；
   - 同一记录内材料/对象/条件/结果彼此匹配的一组值。
4. 如果多个 extractor 把同一条记录拆分/合并不一致，请按 schema 的 record_definition 重新对齐记录。
5. 删除明显重复记录；保留同一论文中确实不同对象/不同条件/不同结果的多条记录。
6. 只返回 JSON：{"records":[ {字段:{"value":...,"evidence":...}}, ... ]}。"""

EXTRACT_MERGER_USER = """【领域】{domain}
【一条记录代表】{record_definition}

【字段表 schema】
{schema_block}

【多个 extractor 的候选结果】
{candidate_outputs}

请合并为最终 records（JSON）。"""


# ---------------------------------------------------------------------------
# 提取审阅者（extract_reviewer）：审阅最终 records 与 evidence
# ---------------------------------------------------------------------------
EXTRACT_REVIEWER_SYSTEM = """你是科研结构化抽取审阅专家。
我会给你论文全文、schema、以及已经合并的 records。
请审阅 value 与 evidence 是否匹配原文，并输出审阅后的 records 和审阅摘要。

硬性要求：
1. value 必须被 evidence 支持；不支持时把该字段改为 {"value":null,"evidence":null}。
2. evidence 必须是论文原文片段，不要改写；可以保留原 evidence 或缩短。
3. 字段类型、单位、enum 必须符合 schema；不符合且无法修正时置 null。
4. 检查多条 records 是否重复、错位或把不同对象/条件混在一行；必要时删除重复记录。
5. 不得引入论文中没有的新事实。
6. 只返回 JSON：
{"records":[...],"review":{"passed":true/false,"issues":[...],"notes":"..."}}"""

EXTRACT_REVIEWER_USER = """【领域】{domain}
【一条记录代表】{record_definition}

【字段表 schema】
{schema_block}

【论文全文】
{content}

【待审阅 records】
{records}

请审阅并输出最终 JSON。"""
