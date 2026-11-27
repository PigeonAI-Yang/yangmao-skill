# 羊毛团开源项目

我们做 AI 省钱资讯，也把自己用的工具开放出来。做日报时，我们需要把同一期视频配上不同语言的标题和不同尺寸的封面；用 AI 连续修图时，我们遇到过同一批旧图反复上传、缓存被占满。这些问题分别做成了浏览器扩展和 Magpie 插件。下面列出我们维护的实现、能解决的问题，以及从哪里开始读源码。

## 内容工具和 Agent Skills

| 项目 | 什么时候用 | 我们维护的部分 |
| --- | --- | --- |
| [羊毛团发布助手](https://github.com/PigeonAI-Yang/yangmao-publisher) | 同一期视频要发到 B 站、微信视频号、YouTube 和 X | 在麦田发布助手基础上增加了[日报目录识别与分平台素材分配](https://github.com/PigeonAI-Yang/yangmao-publisher/blob/main/lib/yangmao-daily.js)，以及 B 站独立双封面。扩展准备投稿，用户决定何时发布。 |
| [免费 AI 额度 Skill](https://github.com/PigeonAI-Yang/yangmao-skill) | 想让自己的助手按地区、资格和用量查免费额度 | [目录刷新脚本](https://github.com/PigeonAI-Yang/yangmao-skill/blob/main/scripts/refresh.py)把公开资料更新成中英两份快照；[查询规则](https://github.com/PigeonAI-Yang/yangmao-skill/blob/main/skills/yangmao-public/SKILL.md)让助手回答时能给出条件和出处。 |
| [X 长文写作 Skill](https://github.com/PigeonAI-Yang/x-article-creator) | 想把一个实际用过的工具写成别人能照着试的长文 | 我们把选题、实例、配图和稿件检查写成了可直接阅读和修改的[写作流程](https://github.com/PigeonAI-Yang/x-article-creator/blob/main/SKILL.md)。 |

## Magpie 插件

| 项目 | 遇到的问题 | 从哪里看实现 |
| --- | --- | --- |
| [Codex 图片瘦身](https://github.com/PigeonAI-Yang/yangmao-magpie-image-slim) | 长对话反复发送旧图，请求越来越大 | [图片处理中间件](https://github.com/PigeonAI-Yang/yangmao-magpie-image-slim/blob/main/image-slim.middleware.js)：优先保留当前图片，较早的图使用预览或本地引用，需要时再找回原图。 |
| [Devin 图片缓存](https://github.com/PigeonAI-Yang/yangmao-magpie-devin-image-history) | 在 Windows 上通过 Magpie 使用 Devin 时，想复用历史图片，又不想让缓存无限增长 | 基于社区 Devin 插件增加[本地图片缓存与空间不足时的处理](https://github.com/PigeonAI-Yang/yangmao-magpie-devin-image-history/blob/main/image-history.mjs)，附[对应测试](https://github.com/PigeonAI-Yang/yangmao-magpie-devin-image-history/blob/main/image-history.test.mjs)。 |

安装说明、适用版本和许可证以各仓库为准。遇到问题，直接在对应仓库开 Issue；如果是额度或活动信息，也可以先核对[羊毛团免费 AI 目录](https://ymtuan.live/free-ai)的来源。

<!-- Maintenance: This file is the canonical index. When adding, renaming or retiring a maintained public project, update this index, the README links in the listed repositories and the yangmao topic. Link to the independent distribution, preserve upstream attribution, and describe what Yangmao maintains. -->
