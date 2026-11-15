# Harbor 中文文档与 Cookbook

访问地址：<https://xingshuozhu1998.github.io/harbor-zh/>。

包含 Harbor 文档站 Docs 页签的 72 篇页面、Cookbook（实践示例集）的 17 篇 README，以及文档首页和 Docs MCP 说明，共 91 篇中文页面。专有名词保留英文并补充首次中文解释；434 个代码块与英文源文件一致。API & SDK、News、Changelog 保留英文。

## 发布

在本仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。之后向 `main` 推送内容会自动构建并发布；也可以在 Actions 中手动运行“构建并发布 Harbor 中文文档”。首次启用时，如果之前的发布任务已经失败，请重新运行该任务。

网站发布后，个人主页 <https://xingshuozhu1998.github.io/> 会自动发现此 Pages 项目；主页另提供中文名称和介绍。

## 本地构建

需要 Node.js（JavaScript 运行环境）、npm 和 Python 3：

```bash
npm ci
npm run build
```

`build.py` 从固定上游提交获取图片和视频，使用 Mintlify（文档网站工具）4.2.893 与客户端 0.0.3697 导出页面，然后适配 `/harbor-zh/` 路径。产物位于 `.build/site/`，GitHub Actions 发布整个目录。

构建脚本修正了当前 Mintlify 导出器把 API 操作名称误当网页路径的问题，并导出未列入侧栏的文档页面。站内导航使用完整页面跳转；原有代码高亮、复制、标签页和折叠组件仍使用 Mintlify 的页面资源。静态站点没有本地开发服务器的热更新通道，Mintlify 在线搜索和其他服务端功能不由 GitHub Pages 提供。

## 来源与范围

- Harbor：<https://github.com/harbor-framework/harbor>，提交 `ec6aeab7fe0eb51df52b4e72c524daf5ea9cc5f4`。
- Cookbook：<https://github.com/harbor-framework/harbor-cookbook>，提交 `2700bb28301ca93b191899c88d1cd10384024a81`。
- 译文位于 `docs/`，上游许可见 `LICENSE`；Mintlify 资源由其原版导出工具生成并保留品牌标识。

这里只发布阅读文档。运行 Cookbook 示例仍需使用原 Cookbook 仓库，并按对应文档准备环境和凭据。

## 发布前核验

在本地模拟 GitHub Pages 的 `/harbor-zh/` 子路径后，91 篇中文页面全部返回 HTTP 200 并显示中文正文，浏览器未捕获页面 JavaScript 异常。静态产物中的 16,746 个本地资源和页面链接均能找到对应文件。已实际测试标签页切换、折叠内容展开、代码复制、进入 Cookbook，以及 390 像素手机视口下无横向溢出。

云端构建也已通过：[首次 Actions 运行](https://github.com/xingshuozhu1998/harbor-zh/actions/runs/43680590010)的 build 任务完成了依赖安装、静态导出与产物上传。该次 deploy 任务因当时尚未启用 Pages 而失败；启用 Pages 后由后续提交重新触发发布。
