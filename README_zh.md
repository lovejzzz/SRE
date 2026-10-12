[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**告诉它要重建哪个软件、运行在哪个平台，以及哪些地方应该更好。**

SRE 是供 agent 使用的 skill：研究已有软件，保留所需行为，适配新平台，并增加或增强功能。目标覆盖游戏、桌面应用、命令行工具、网页和移动应用；实际可行性取决于证据、依赖和目标平台能力。

**v0.2：skill + 可执行研究与验证工具。** 调查和编程由宿主 agent 完成，目前不保证任何软件都能一键完整复刻。

## 快速开始

需要支持本地 skill 的宿主，辅助工具需要 **Python 3.10+**，无第三方 Python 依赖。[REA](https://github.com/morluto/rea) 可选；安装器不会安装 REA 或反编译引擎。

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

默认安装到 `$CODEX_HOME/skills` 或 `~/.codex/skills`，拒绝覆盖已有安装。可用 `--skills-dir /path/to/skills` 指定目录。升级时保留本地修改；让宿主重新加载 skill 后调用：

> 使用 $software-resynthesis，研究这个桌面应用，把它重建为离线网页应用。保留文档工作流，加入批量操作，并与原软件对照验证。先交付经过测试的里程碑，但不要丢掉完整任务范围。

## 工作方式

发现软件与功能 → 提出假设、设计实验 → 实现与增强 → 原软件对照及目标验收 → 根据差异继续研究 → 带覆盖说明交付。

| 能力 | 已实现内容 |
| --- | --- |
| 功能覆盖审计 | 多来源发现、功能映射、依赖、遗漏检查和版本化基线 |
| 研究实验 | 竞争假设、预测结果、区分性实验排序、矛盾检测 |
| 原软件适配器接口 | 显式命令执行、独立运行目录、重置/操作/观察/结束协议、哈希、日志与超时处理 |
| 领域验证 | 规范化图像误差、文件语义往返、交互轨迹、设备与工作负载匹配的性能预算 |
| 完成检查 | 重新计算验证证据并审计研究；陈旧策略、遗漏项和阻塞问题不能通过 |
| 续跑 | 项目文件和检查点；没有无人值守后台调度器 |

REA 可提供分析能力，SRE 将研究衔接到规格、实现和验收。没有内置 REA 客户端，也没有声称经过测量优于 REA。保留、适配、增强功能分别验收。

## 运行示例

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

示例通过适配器实际运行 Python `posixpath.normpath` 与独立 JavaScript 实现，对照 **417 个输入**，用原程序观察解决研究问题，并检出故意引入的错误。需要 Node.js 18+，输出目录不能已存在。这是跨语言证据链演示，不是完整软件自主重建的独立评测。

## 研究工具

入口为 `skills/software-resynthesis/scripts/sre.py`：

- `init`、`fingerprint`：创建私有项目状态、计算指定文件指纹。
- `seal`、`audit`：冻结研究范围和策略、检查发现覆盖情况。
- `plan`：按区分假设的能力排序已设计的实验。
- `run-adapter`：执行经过检查的应用适配器并保留诊断。
- `compare`、`domain-check`：轨迹对照或领域验证。
- `check`：同时要求行为证据和研究审计通过。

子命令的 `--help` 提供参数。默认不覆盖输出。退出码 0 表示成功，1 表示比较/验收/运行未通过，2 表示输入或执行错误。**从 v0.1 升级：**旧工作区需要补充真实发现记录并建立研究基线，才能通过 `check`。

## 当前边界

不能证明所有功能都已发现，不能由客户端恢复不可访问的服务端实现，也不保证任何负载都能适配任何平台。里程碑通过不等于完整产品完成。来源收集和假设设计仍由 agent 执行，没有通用爬虫。适配器是应用专用代码，以宿主权限执行，不是安全沙箱。领域验证读取规范化 JSON；PSD 解析、图片解码、GUI 操作和设备测量需相应适配器。尚未提供 PZ/Photoshop 运行适配器。

哈希可以检出记录过期，不能认证实验真实性。独立 agent 评测尚未执行。专有样本、密钥和个人数据留在私有研究工作区；复用代码遵循原许可证。

## 文档与贡献

[Skill 入口](skills/software-resynthesis/SKILL.md) · [研究协议](skills/software-resynthesis/references/research-protocol.md) · [适配器协议](skills/software-resynthesis/references/adapters.md) · [领域验证](skills/software-resynthesis/references/domain-validation.md) · [PZ 路线](skills/software-resynthesis/references/pz-inventory.md) · [评测协议](evals/behavioral.md)

欢迎提交可复现、脱敏的失败案例：版本、输入、预期/实际行为和证据，并保留回归测试。欢迎改进翻译；各语言的能力和限制声明应保持一致。详细技术协议目前使用英文。

证据完整性更新：目标验证和研究观察必须记录 SHA-256。参见[迁移方法与校验边界](skills/software-resynthesis/references/validation.md#recorded-evidence-integrity)及[变更记录](CHANGELOG.md)。
