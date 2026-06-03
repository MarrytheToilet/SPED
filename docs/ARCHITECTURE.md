# 架构文档

SPED 把「PDF → 结构化数据」拆成三段，彼此通过磁盘产物解耦，任一段可单独重跑。

## 1. 解析层 (src/pdfs, src/database)

- `scripts/pdf.py` 调 MinerU 把 PDF 解析为 `data/collections/<collection>/parsed/<paper_id>/full.md`（含 `images/`）。
- `src/database/catalog.py` 维护已解析论文目录（自建 sqlite），`src/pdfs/` 维护 PDF 处理状态。
- MinerU 的常见问题（公式/表格线性化、图片引用）在下游以「宽松解析 + 证据核验」消化，不再缝补。

## 2. Schema 设计层 (src/schema) ⭐ 多智能体

输入：领域简介 + 若干已解析论文。输出：`data/collections/<collection>/schemas/<slug>.json`。

```
select_sample(papers)            # 按体量分层选样本
   build_schema_context_for_papers()
        # 每篇样本优先保留摘要 / 引言 / 实验或方法部分 + 图/表标题
   schema_agent_{a,b,c}.call →
        # 每个 agent 独立阅读同一批样本，产出完整 schema 草案
   schema_merger.call →          # 合并多份完整 schema，统一相近字段/描述/单位/格式
   schema_reviewer.call →        # 审阅记录定义、字段可抽取性、提取格式 → 定稿
   deterministic repair          # 重复字段/字段数/enum/extraction_format 兜底
   validate_schema(min,max)      # 字段数与一致性校验(警告不阻断)
```

关键模块：

| 文件 | 职责 |
|------|------|
| `prompts.py` | schema 草案/合并/审阅/抽取/提取审阅的元prompt |
| `discovery.py` | `SchemaDiscovery`：编排多智能体，按 `settings` 角色构建客户端 |
| `sampling.py` | `select_sample` / `build_schema_context_for_papers` / `collect_figures` / `load_paper_text` |
| `models.py` | `GeneratedSchema` / `SchemaField`（含 `extraction_format`、`from_figure`） |
| `store.py` | 生成 schema 的保存/加载/列出 |
| `_json.py` | `parse_json_loose`（json_repair 兜底模型偶发的坏 JSON） |

角色到端点的映射由 `settings.get_agent_config(role)` 决定，默认全部回退基础 `LLM_*`，
可用 `AGENT_<ROLE>_MODEL/_API_BASE/_API_KEY` 单独覆盖，实现跨模型家族协作。

默认 `SCHEMA_AGENT_ROLES=schema_agent_a,schema_agent_b,schema_agent_c`。每个 schema agent
读取的是同一批样本论文上下文，并输出完整 schema；系统不要求保留 agent 草案给前端展示，
但 `discovery_trace` 会记录角色、字段数、合并草稿和修复记录，便于调试。

## 3. 提取层 (src/extractors, src/prompts/modes)

- `ExtractionService(schema, agent_role="extractor")` 默认按 `EXTRACTOR_ROLES=extractor_a,extractor_b`
  构建多路提取：extractor 独立抽取 → `extract_merger` 合并 → `extract_reviewer` 审阅。
- `GenericFlatMode`：
  - 系统prompt 复用 `schema/prompts.py: EXTRACTOR_SYSTEM`，字段表标注图表派生字段。
  - 要求输出 `{"records":[ {字段:{"value":..,"evidence":..}}, .. ]}`，一篇可多记录。
  - **证据核验**：对 value 的 evidence 做 NFKC 归一 + 去 LaTeX 命令 + 保留字母数字与 CJK，
    再做整串包含或 16 字符窗口匹配；未命中（多为表格数值线性化差异）如实标记。
- 结果写入 `data/collections/<collection>/extracted/<schema_slug>/<paper_id>.json`，含证据核验统计。

## LLM 客户端 (src/llm)

- `OpenAICompatibleClient`（`openai_client.py`/`base.py`）：OpenAI 兼容、`response_format=json_object`、
  截断时自动抬高 `max_tokens`（上限 `LLM_MAX_OUTPUT_TOKENS`，默认 65536，适配推理模型）。
- `factory.py`：`create_llm_client()`、`create_llm_client_for_agent(role)`。

## 数据流与解耦

```
collections/<collection>/pdfs ─▶ parsed ─▶ schemas ─▶ extracted/<schema_slug>
          pdf.py (MinerU)       schema_pipeline design   schema_pipeline extract
```

三段产物均落盘，重跑任一段不影响其它段；保留 `parsed/` 即可反复试验 schema 与提取。
