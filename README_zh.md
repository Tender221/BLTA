# BLTA：正常日志驱动的工具适配

项目地址：https://github.com/Tender221/BLTA 。英文入口与方法示意图见 README.md。

本包从缓存的完整窗口特征重算跨工具结果、正常日志预算结果，并从真实保存的逐任务执行记录汇总 Agent 主任务结果。CPU 即可运行，读取已归档数据时无需联网、GPU、PyTorch、模型 API 或当前工作区的其他目录。

## 快速运行

使用 Python 3.11 或更高版本。安装本包记录的 NumPy/SciPy 版本后执行：

```text
python -m pip install -r requirements.txt
python reproduce.py --output results
python reproduce.py --refit --output results_refit
python -m unittest discover -s tests -v
```

第一条复现命令使用已保存的源读出参数，重新计算每条测试观察的分数、固定源阈值下的拦截和 FP/TP 计数。`--refit` 还会从相同源训练特征重新拟合 90 个源读出头，并与归档参数和源正常校准阈值核对。两种模式都执行源/目标数据隔离检查、目标日志选择检查及文件校验。

已安装依赖后，可断网运行上述复现命令。无需安装 LaTeX；该包不承担论文 PDF 编译。

## 覆盖范围

| 输出 | 计算来源 | 覆盖范围 |
|---|---|---|
| cross_tool.csv | 测试特征、源读出、正常日志、固定源阈值 | 3 个护栏 × 5 个划分 × 6 个新工具；直接迁移、BLTA、最近源工具对齐 |
| telemetry.csv | 相同源头与测试数据，重新计算各日志预算的偏移 | 8、16、32、64、128、完整历史；超过可用历史的预算按实际数量截断 |
| agent_main.csv | 2,688 条已记录任务执行结果 | 两个 Agent；无护栏及三种护栏的直接迁移/BLTA；每配置 96 正常 + 96 攻击任务 |
| deployable_heads.json | 经过重算验证的源参数和每工具偏移 | 按护栏、源划分和被留工具区分；每个条目是对应实验的一套源护栏 |
| verification.json | 所有隔离、参数和计数比对 | 成功时 archived_count_mismatches 为 0 |

Agent 部分重算已有执行结果的统计，不调用受害模型产生新回答。神经网络特征提取、末层微调、完整源基线和其他次要诊断的全流程仍保存在上一级研究档案中。该复现包针对论文的核心跨工具机制与配对 Agent 主结果，不将缓存重算称作新的端到端模型实验。

五个划分之间存在样本重叠。输出中的汇总次数是评估次数，不能解读成相互独立的新样本。

## 单独使用分类头

`blta.py` 提供 `BLTA.fit`、`BLTA.adapt`、`BLTA.scores`、`BLTA.blocked` 及参数导入导出。输入是对应冻结编码器的分类器输入特征，必须使用与训练时一致的编码器、token 窗口和窗口选择规则。

```python
import json
from blta import BLTA

heads = json.load(open('results/deployable_heads.json', encoding='utf-8'))
head = BLTA.from_dict(heads['wolf|20261015|retail::get_order_details'])
# executor_tools 必须由可信执行器给出；features 是冻结编码器特征。
decisions = head.blocked(features, executor_tools)
```

每个留工具源头对应独立训练数据口径。这个实验导出不能将不同留工具源头混称为同一套所有工具通用权重。对一套固定源头接入多个真实新工具，可分别调用 `head.adapt(tool_id, trusted_normal_features)`，从而维护多个标量偏移。

## 数据、来源与发布

- `data/clean.jsonl`、`data/injected.jsonl` 是既有派生语料的原文件副本；`data/*_features.npz` 只保留完整窗口所选特征，不使用 `first_vectors`。
- `data/folds.json` 保存源拟合、源校准、目标正常历史和测试索引、归档读出参数以及用于验收的计数。验收计数不参与拟合和适配。
- `data/agent_outcomes.jsonl` 保留对应任务的逐条执行记录，并标出原检查点与校验值；不将合成业务信息、审计码或模拟邮件当作真实业务记录与真实外发行为。
- `input_manifest.json` 记录本包输入校验值、原文件校验值和验证环境；`third_party` 保留上游版本信息及两份原始 MIT 许可文本。
- 包内没有护栏或 Qwen 的大型底座权重，公开模型标识与版本见 `third_party/guard_model_provenance.json`。重新运行编码器和受害模型时需恢复相应公开权重并使用完整研究代码。
- BLTA原创代码采用MIT许可证（LICENSE）；上游材料保留其原有许可，详见 THIRD_PARTY.md。三种护栏与两种受害模型的完整版本映射见 third_party/model_revisions.json，完整上游模型卡随仓库保留。

## 对应论文材料

本仓库对应论文《BLTA: Adapting Prompt-Injection Guards Across Tools with Benign Logs》，作者 Enhui Wan、Xiaowan Wang。论文尚在作者通读阶段，草稿PDF、作者身份材料和人工确认表不随代码仓库发布。该仓库提供核心机制与主结果的可携带CPU复现，读者无需本地研究工作区即可运行。
