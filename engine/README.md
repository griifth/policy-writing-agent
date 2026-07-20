# engine —— 实际工作模型模块（写作实体执行引擎）

> 路径约定：本文件内相对路径一律以 direction_workflow/ 为根。
> 定位：把内容生产实体（构思/组稿）的执行从 agent 直写切换为 DeepSeek 执行，兑现"落笔全国产"承诺。
> 编写日期：2026-07-13。

## 一、用法

```bash
python3 engine/run_entity.py <实体提示词文件> <输出文件> [--attach 材料文件 ...] [--env .env路径] [--effort max|high|medium|low]
```

- **实体提示词文件**：装配工按宪法第 4 条制造的自包含四节提示词（`runs/<id>/generated/` 下）。
- **--attach**（可多次）：DeepSeek 不能读盘。实体提示词第 3 节【本篇材料】若以路径引用输入
  （方向书/料包/勾选记录等），须逐个 `--attach` 内联进提示词，使之真正自包含。
  内联即留痕：stdout 打印每个附件的字符数，提示词尾部有内联标头。
- **stdout 留痕**：提示词长度、每级降级尝试的参数与结果、token 用量
  （prompt/completion/reasoning/total、finish_reason）、产出落盘路径与字符数。
  建议 `| tee` 存档进本 run 留痕。

示例（同料 A/B 那单）：

```bash
cd direction_workflow
python3 engine/run_entity.py \
  "runs/2026-07-13-拔尖创新人才/generated/写作实体_drafting.md" \
  "runs/2026-07-13-拔尖创新人才/outputs/成稿_deepseek版.md" \
  --attach "runs/2026-07-13-拔尖创新人才/方向书.md" \
  --attach "runs/2026-07-13-拔尖创新人才/outputs/结构提案.md" \
  --attach "runs/2026-07-13-拔尖创新人才/outputs/触点二勾选记录_AGENT-WRITER.md" \
  --attach "runs/2026-07-13-拔尖创新人才/outputs/料包.md"
```

## 二、执行引擎分工表

| 环节 | 执行引擎 | 说明 |
|---|---|---|
| 侦察 / 全量检索 | agent | 需真实联网检索与溯源核对，DeepSeek 不能联网读盘 |
| 结构单实例化 / 实体提示词制造 | agent（装配工） | 调度本体职责，宪法第 4 条 |
| **构思（立论，契约②）** | **DeepSeek（经 engine/run_entity.py）** | 生产环境；试跑/测试可 agent 直写，须在台账标注执行引擎 |
| **组稿（写作，契约③）** | **DeepSeek（经 engine/run_entity.py）** | 同上 |
| 四闸（溯源/承重/方向保真/语域预检） | agent ＋ gates/precheck.py | 闸门需回料包核对，零裁量规程 |
| 预读提词 / 调度与汇装 | agent | skill 分工路由（宪法第 6 条） |

## 三、密钥配置说明（密钥零泄漏纪律）

- **本目录不存放任何密钥。** 密钥仍从旧引擎既有 `.env` 位置读取：默认为 **direction_workflow/ 上一级目录**下的 `.env`（按相对位置定位，与目录名无关）。
- 所需变量：`DEEPSEEK_API_KEY`（必填）、`DEEPSEEK_BASE_URL`、
  `DEEPSEEK_MODEL`、`DEEPSEEK_TIMEOUT_SECONDS`、`DEEPSEEK_MAX_TOKENS`、
  `DEEPSEEK_REASONING_EFFORT`、`DEEPSEEK_THINKING_ENABLED`。
- 覆盖方式：进程环境变量最优先；或 `--env` / `DEEPSEEK_ENV_PATH` 指定其他 `.env`
  （路径须在包上一级目录范围内，越界即报错）。
- 新机移植：整包拎走后在包的上一级目录自备 `.env`（变量清单见 依赖说明.md），
  用 `--env` 指向即可；**严禁把密钥写进 engine/ 或任何将提交的文件、严禁打印**。

## 四、血换的降级重试（务必保留，勿"简化"）

空响应几乎总是推理（thinking）烧穿 `max_tokens`（`finish_reason=length`），根因见
2026-07 排查记录（DeepSeek 服务端时段性 thinking 失控）。`run_entity.py` 移植旧引擎
`workflow/report_pipeline._ask_deepseek` 的逐级降级重试，原样保留：

1. 第 1 级：原参数（`--effort` 或配置的 reasoning_effort）；
2. 第 2 级：`reasoning_effort=low`；
3. 第 3 级：`reasoning_effort=low` ＋ 关闭 thinking（`thinking.type=disabled`）；
4. 三级仍空 → 报错中止，**绝不把空产物落盘**。每级重试间隔 5s×级数，全程 stdout 留痕。

客户端层（`engine/deepseek_client.py`，移植自 `example1/workflow/deepseek_client.py`）的
空响应防护同样原样保留：content 为空即抛 `DeepSeekEmptyResponseError`，并刻意不保存、
不拼接、不外露 `reasoning_content`。
