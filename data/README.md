# 课程起点反馈与组内访谈数据

## 当前材料

| 路径 | 内容 | Git提交与使用范围 |
|---|---|---|
| `raw/initial-survey/feedback.json` | 47份真实课程起点反馈的脱敏记录，含选择、自评、开放回答与追问 | 受限教学材料，已被Git忽略，由教师定向分发 |
| `raw/initial-survey/text_units.jsonl` | 570个非空文本单元，每行一条，保留匿名参与者及问题关联 | 同上；不是570名受访者 |
| `raw/initial-survey/processing_summary.json` | 筛选数量、移除字段和脱敏处理计数 | 与受限数据一起提供 |
| `samples/teaching_fragments.jsonl` | 24条根据真实回答概括、泛化的去关联教学片段 | 可随仓库提供，用于流程练习；不是逐字引文或统计样本 |
| `questions.json` | 问题编号、题干与分支题目说明 | 可随仓库提供 |
| `processed/` | 各组本地分析结果 | 默认不提交Git |

原始导出为2026年10月7日的课程起点反馈：共64条，57份已提交，筛选其中同意保存且允许AI辅助整理的47份。草稿与未允许AI整理的记录未进入本教学分析文件；它不是全班回收率或完整总体。保留47份中的空回答和未回答字段，不将它们改写为“不清楚”。原始文件仍留在教师资料目录，没有复制进项目仓库。

## 脱敏处理与限制

移除姓名、学号、原系统ID、精确时间、自动分析字段、进度字段、原追问ID及重复保存原话的`basis`。重新随机排列记录并编号为`P001`等，不保存身份映射；编号仅在本版本内关联。对文本检查直接身份、电话、邮箱、链接等，并对个人敏感经历和少量易识别细节移除或泛化。

这属于教学脱敏，不保证文本无法被熟悉受访者的人重新识别。原问卷的保存与AI辅助同意没有包含逐人原话公开发表；因此真实逐人数据默认不推送GitHub，也不上传额外第三方服务。使用模型须遵循教师指定的数据与模型服务范围。需要公开演示时，使用去关联教学改写片段或另获明确授权的材料。

`teaching_fragments.jsonl`只保留常见学习主题的概括，不提供与真实个体的对应关系；不能据24条片段计算学生比例，也不能把改写文本放进引号当作原话。

## 真实脱敏数据的字段

`feedback.json`是带元信息的对象，`records`为记录数组：

- `participant_id`：本版本内随机匿名编号，不是学号或原始系统ID。
- `answers`：原问题ID对应的答案；选择题为数组或字符串，`q11`为技术自评对象，开放题为脱敏文本。
- `question_variants`：区分`q5`的使用经历／未使用原因，以及`q10`的Agent经历／期望流程。愿望不能当作已经做过的经历。
- `followups`：追问编号、所属问题、脱敏题目与回答，以及`answered`、`unanswered`或`skipped`状态。只有已回答的追问进入文本单元文件。

`text_units.jsonl`中的`unit_id`定位脱敏材料，`participant_id`用于同一份答卷内关联，`source`区分主回答和追问，`question_id`指向题目，`text`保存脱敏文本。统计人数时同一人同一主题最多计一次；按文本单元统计则须标明单位。

保留回答中概念不清、矛盾或尚未确定的内容，不代学生纠正。材料中的经历为自述，不能直接当作实际能力测验或已验证的项目成果。

## 读取方式

无需第三方依赖。先用公开教学片段练习：

```python
import json
from pathlib import Path

units = [json.loads(line) for line in
         Path("data/samples/teaching_fragments.jsonl").read_text(encoding="utf-8").splitlines()
         if line.strip()]
print(len(units))  # 24个教学片段
```

收到教师分发的受限数据后，可以读取：

```python
package = json.loads(Path("data/raw/initial-survey/feedback.json").read_text(encoding="utf-8"))
records = package["records"]
```

只有教师重新制作数据时才需要运行脱敏脚本：

```bash
python3 scripts/prepare_initial_survey.py --input /path/to/original-export.json
```

脚本在本地运行，不调用外部模型。重建会重新编号，旧版人工标注不能直接按编号合并。

## 学生自行开展的组内访谈

按[项目任务与访谈安排](../docs/PROJECT_BRIEF.md)进行。空白格式见[访谈模板](../examples/group_interview.template.json)。真实访谈记录放`data/raw/group-interviews/`，转写、编码及分析放`data/processed/`；身份映射与录音另行受限保管。模板中的同意字段默认均为`false`，需由真实参与者选择后再记录。

组内访谈与课程问卷分别标记来源、阶段和问题编号；不凭相似表达关联个体。课前、课后的整体调查数据由教师提供，课中由研究小组通过访谈等方式收集过程数据。新增材料补充数据说明与版本，不用现在的教学片段或访谈小样本冒充全班数据。

## 全过程数据组织

项目分析课程前、课程中、课程后三个阶段：教师提供课前与课后整体调查数据，研究小组负责课中访谈等过程数据的采集。新增数据应记录`stage`（`pre`、`mid`或`post`）、`source`（调查或访谈）、数据版本、题目版本和使用范围；当前起点反馈属于`pre`，尚未提供的阶段不创建虚构记录。组内访谈模板中的`early_project`表示项目早期采集安排，不能直接替代课程阶段，录入实际访谈时需另行标明课程阶段。

跨阶段保留相近的核心问题，并允许围绕当期体验增加追问。仅在教师提供获准使用且稳定的关联标识时进行个体追踪；当前随机编号不支持跨版本匹配。否则按阶段和主题比较，同时报告样本构成、缺失及题目差异。具体分析维度与成果要求见[项目任务与访谈安排](../docs/PROJECT_BRIEF.md)。
