# 羊毛团公开资料 Skill

查免费 AI 额度、适用条件和官方规则。网站与 GitHub 使用同一份公开资料：网站是实时入口，GitHub 是方便阅读和安装的快照。

- **网站**：[中文资料索引](https://ymtuan.live/llms.txt) · [English index](https://ymtuan.live/en/llms.txt)。索引会列出已经开放的栏目。
- **GitHub**：[中文快照](skills/yangmao-public/references/catalog-zh.md) · [English snapshot](skills/yangmao-public/references/catalog-en.md)。每条保留来源与核验日期；快照中的日期不等于今天仍可领取。额度没有明确证据时，标记为未核实。

## 安装与使用

把 [`skills/yangmao-public/`](skills/yangmao-public/) 整个目录复制到 Agent 工具使用的 Skill 目录。安装目录名保持 `yangmao-public`，其中应直接包含 `SKILL.md` 和 `references/`。使用支持 Agent Skills 的工具，可按该工具的方式调用 `yangmao-public`。使用读取功能不需要 Python、站点账号或 API 密钥。

试问：“个人免费版每天有没有模型额度？按我所在地区说明条件，给官方规则和核验日期；拿不准的数字请标未核实。”

## 快照如何更新

GitHub Actions 每天约北京时间 09:23 读取网站的两种公开语言版本，管理员也可以在 Actions 手动运行。它保留网站已发布的主题、文章链接、公开免费额度说明、适用条件和来源链接，不复制文章或供货商页面全文。两版都验证成功后才更新快照；内容有变化才提交。上游 403、限流或格式异常时保留上次快照。维护者可运行 `python scripts/refresh.py` 复现；具体调度以 GitHub 执行时间为准。

仓库中的 Skill 和同步代码以 [MIT](LICENSE) 提供。链接指向的网站内容和第三方规则仍由原权利人管理。
