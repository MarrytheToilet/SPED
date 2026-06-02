# 架构文档

SPED 把「PDF → 结构化数据」拆成三段，彼此通过磁盘产物解耦，任一段可单独重跑。

## 1. 解析层 (src/pdfs, src/database)

- `scripts/pdf.py` 调 MinerU 把 PDF 解析为 `data/processed/parsed/<paper_id>/full.md`（含 `images/`）。
- `src/database/catalog.py` 维护已解析论文目录（自建 sqlite），`src/pdfs/` 维护 PDF 处理状态。
- MinerU 的常见问题（公式/表格线性化、图片引用）在下游以「宽松解析 + 证据核验」消化，不再缝补。

## 2. Schema 设计层 (src/schema) ⭐ 多智能体

输入：领域简介 + 若干已解析论文。输出：`data_schema/generated/<slug>.json`。

```
select_sample(papers)            # 按体量分层选样本
   └─ 对每篇:
        build_excerpt(text)      # 章节感知截断到预算
        collect_figures(text)    # 抽取 Fig./Table/图/表 标题行
        proposer_{a,b,c}.call →  # 轮转分配，单篇候选字段(可标 from_figure)
   merge_candidates()            # 规范化名去重 + coverage(被多少篇独立提出)
   consolidator.call →           # 合并为单表草稿(record_definition + fields)
   critic.call →                 # 查漏/去冗/控字段数/保留图表字段 → 定稿
   validate_schema(min,max)      # 字段数与一致性校验(警告不阻断)
```

关键模块：

| 文件 | 职责 |
|------|------|
| `prompts.py` | 提议/整合/评审/抽取的元prompt（鼓励图表派生字段与图注证据） |
| `discovery.py` | `SchemaDiscovery`：编排多智能体，按 `settings` 角色构建客户端 |
| `sampling.py` | `select_sample` / `build_excerpt` / `collect_figures` / `load_paper_text` |
| `models.py` | `GeneratedSchema` / `SchemaField`（含 `coverage`、`from_figure`） |
| `store.py` | 生成 schema 的保存/加载/列出 |
| `_json.py` | `parse_json_loose`（json_repair 兜底模型偶发的坏 JSON） |

角色到端点的映射由 `settings.get_agent_config(role)` 决定，默认全部回退基础 `LLM_*`，
可用 `AGENT_<ROLE>_MODEL/_API_BASE/_API_KEY` 单独覆盖，实现跨模型家族协作。

## 3. 提取层 (src/extractors, src/prompts/modes)

- `ExtractionService(schema, agent_role="extractor")` 用定稿 schema 构建 `GenericFlatMode`。
- `GenericFlatMode`：
  - 系统prompt 复用 `schema/prompts.py: EXTRACTOR_SYSTEM`，字段表标注图表派生字段。
  - 要求输出 `{"records":[ {字段:{"value":..,"evidence":..}}, .. ]}`，一篇可多记录。
  - **证据核验**：对 value 的 evidence 做 NFKC 归一 + 去 LaTeX 命令 + 保留字母数字与 CJK，
    再做整串包含或 16 字符窗口匹配；未命中（多为表格数值线性化差异）如实标记。
- 结果写入 `data/processed/extracted/<paper_id>.json`，含证据核验统计。

## LLM 客户端 (src/llm)

- `OpenAICompatibleClient`（`openai_client.py`/`base.py`）：OpenAI 兼容、`response_format=json_object`、
  截断时自动抬高 `max_tokens`（上限 `LLM_MAX_OUTPUT_TOKENS`，默认 65536，适配推理模型）。
- `factory.py`：`create_llm_client()`、`create_llm_client_for_agent(role)`。

## 数据流与解耦

```
raw/pdfs ─▶ processed/parsed ─▶ data_schema/generated ─▶ processed/extracted
   pdf.py        (MinerU)          schema_pipeline design     schema_pipeline extract
```

三段产物均落盘，重跑任一段不影响其它段；保留 `parsed/` 即可反复试验 schema 与提取。
