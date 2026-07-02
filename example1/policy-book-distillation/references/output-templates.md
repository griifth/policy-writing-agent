# Output Templates

Use concise structures. Emit only the formats the user needs.

## Template 1: Single-Book Method Card

```md
# 《书名》方法卡

## 一句话方法论

## 显性方法
- 核心框架：
- 典型分析顺序：
- 关键概念：

## 隐含思考模型
- 默认起手点：
- 因果解释偏好：
- 行动者与制度观：
- 证据偏好：

## 可复用启发式

## 适用边界与失真风险

## 证据基础与置信度
- 材料：
- 覆盖等级：
- 置信度：
```

## Template 2: Author Thinking Model Card

```md
# 作者名的政策研究思维模型

## 默认如何进入一个政策问题

## 如何组织因果链

## 如何看待行动者、制度与执行

## 如何把诊断转成建议

## 反复出现的取舍

## 常见盲点或压缩项

## 可模仿部分

## 不应机械照搬部分
```

## Template 3: Cross-Book Comparison Matrix

Use a table with these columns:

| 书/作者 | 问题定义 | 分析单位 | 因果机制 | 行动者观 | 实施逻辑 | 评估标准 | 隐含假设 | 适用议题 |
|---|---|---|---|---|---|---|---|---|

## Template 4: Reusable Policy Prompt

```md
请按以下框架分析【议题】：
1. 先定义政策问题、边界与历史基线；
2. 识别关键行动者、制度约束与政策工具；
3. 画出“目标-机制-执行-反馈”链条；
4. 判断哪一环最可能失效，并说明证据；
5. 给出政策建议，同时说明适用条件、副作用与实施风险。
```

## Template 5: Skill Seed Draft

Use this when the user wants to convert a distilled book into a new skill:

```md
- 触发语：
- 适用议题：
- 显性方法：
- 隐含心智模型：
- 决策启发式：
- 默认输出结构：
- 证据门槛：
- 使用边界：
- 需要预读的参考资料：
```

## Template 6: Literature Review Backbone

```md
# 文献综述骨架

## 一组著作共同回答的政策问题

## 主要分歧：问题定义

## 主要分歧：分析单位与机制

## 主要分歧：实施与评估

## 可综合出的中层框架

## 仍未解决的问题
```

## Output Rule

Whenever practical, keep a visible split between:

- `直接证据支持的显性方法`
- `基于重复信号推断的隐含模型`
