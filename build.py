#!/usr/bin/env python3
"""导出 Mintlify 原版页面，并适配 GitHub Pages 的 /harbor-zh/ 路径。"""
import json
import html
import os
import re
import shutil
import subprocess
import zipfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / 'docs'
BUILD = ROOT / '.build'
SITE = BUILD / 'site'
BASE = '/harbor-zh'
CLIENT_VERSION = '0.0.3697'
UPSTREAM_COMMIT = 'ec6aeab7fe0eb51df52b4e72c524daf5ea9cc5f4'
ASSET_PATHS = ['harbor-logo.png', 'harbor-wordmark-dark.png', 'harbor-wordmark-light.png', 'images/acp-simulated-user.png', 'images/agent-auth-resolution/parsing-and-routing-dark.svg', 'images/agent-auth-resolution/parsing-and-routing-light.svg', 'images/agent-auth-resolution/skip-parsing-dark.svg', 'images/agent-auth-resolution/skip-parsing-light.svg', 'images/artifact-viewer-file.png', 'images/artifact-viewer-manifest.png', 'images/asp-agent-run.png', 'images/asp-architecture-terse-labels.svg', 'images/asp-current.png', 'images/asp-diagram.png', 'images/asp-managed-agents-edge.png', 'images/asp-managed-agents-interface.png', 'images/environment-variable-reach.png', 'images/error-classification-dark.png', 'images/error-classification.png', 'images/hosted-harbor/add-secrets-dark.png', 'images/hosted-harbor/add-secrets.png', 'images/hosted-harbor/advanced-options-dark.png', 'images/hosted-harbor/advanced-options.png', 'images/hosted-harbor/harbor-api-key-dark.png', 'images/hosted-harbor/harbor-api-key.png', 'images/hosted-harbor/hub-home-dark.png', 'images/hosted-harbor/hub-home.png', 'images/hosted-harbor/hub-settings-dark.png', 'images/hosted-harbor/hub-settings.png', 'images/hosted-harbor/org-add-secret-dark.png', 'images/hosted-harbor/org-add-secret.png', 'images/hosted-harbor/org-button-dark.png', 'images/hosted-harbor/org-button.png', 'images/hosted-harbor/org-settings-dark.png', 'images/hosted-harbor/org-settings.png', 'images/hosted-harbor/secret-modal-dark.png', 'images/hosted-harbor/secret-modal.png', 'images/hosted-harbor/select-agent-dark.png', 'images/hosted-harbor/select-agent.png', 'images/hosted-harbor/select-job-settings-dark.png', 'images/hosted-harbor/select-job-settings.png', 'images/hosted-harbor/select-organization-dark.png', 'images/hosted-harbor/select-organization.png', 'images/hosted-harbor/select-secret-settings-dark.png', 'images/hosted-harbor/select-secret-settings.png', 'images/hosted-harbor/select-source-dark.png', 'images/hosted-harbor/select-source.png', 'images/langsmith-experiments.jpeg', 'images/netpolicy.png', 'images/rollout-lifecycle.png', 'images/separate-verifier-environment-variable-reach.png', 'images/separate-verifier-sandbox-variables.png', 'images/shared-sandbox-variables.png', 'images/stream-viewer.jpg', 'images/viewer-agent-files.png', 'images/viewer-artifacts.png', 'images/viewer-jobs.png', 'images/viewer-new-run.png', 'images/viewer-trial-config.png', 'images/viewer-trial-lock.png', 'images/viewer-trial-overview.png', 'images/viewer-verifier-files.png', 'videos/handoff-demo.mp4', 'videos/simulated-user-demo.mp4', 'videos/stream-demo.mp4']


def fetch_assets():
    # 图片和视频从译文对应的上游提交获取，不把二进制副本重复提交进仓库。
    def fetch(rel):
        target = DOCS / rel
        if target.exists():
            return
        url = f'https://raw.githubusercontent.com/harbor-framework/harbor/{UPSTREAM_COMMIT}/docs-mintlify/{rel}'
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=90) as response:
            target.write_bytes(response.read())
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, ASSET_PATHS))


def prepare_export():
    # CLI 4.2.893 会把 OpenAPI 操作名误当成路径；实际 API 页面由 decorated nav 提供。
    module = ROOT / 'node_modules/@mintlify/previewing/dist/local-preview/export.js'
    code = module.read_text()
    old = 'for (const navPath of getAllPathsInDocsNav(config.navigation)) {\n            routes.add(`/${navPath}`);'
    new = 'for (const navPath of getAllPathsInDocsNav(config.navigation)) {\n            if (/^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\\s+\\//.test(navPath)) continue;\n            routes.add(`/${navPath}`);'
    code = code.replace(old, new)
    # 侧栏之外的首页、文档连接说明和历史路径也必须导出，避免现有链接失效。
    routes = ['/' + str(p.relative_to(DOCS).with_suffix('')) for p in sorted(DOCS.rglob('*.mdx'))]
    code = re.sub(r'    // harbor-extra-routes:start[\s\S]*?    // harbor-extra-routes:end\n', '', code)
    code = code.replace('    // Also collect routes from',
        '    // harbor-extra-routes:start\n    for (const route of ' + json.dumps(routes) + ') routes.add(route);\n    // harbor-extra-routes:end\n    // Also collect routes from')
    module.write_text(code)
    # 多个文档项目可能同时导出。使用独立缓存，避免 shared 缓存混入其他项目页面。
    constants = module.parent.parent / 'constants.js'
    constants.write_text(constants.read_text().replace("setPreviewPath('shared');", "setPreviewPath('harbor-zh-export');"))
    BUILD.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['PATH'] = str(ROOT / 'node_modules/node/bin') + os.pathsep + env['PATH']
    subprocess.run([str(ROOT / 'node_modules/.bin/mint'), 'export', '--client-version', CLIENT_VERSION,
                    '--output', str(BUILD / 'export.zip')], cwd=DOCS, env=env, check=True)


def adapt_site():
    if SITE.exists():
        shutil.rmtree(SITE)
    with zipfile.ZipFile(BUILD / 'export.zip') as archive:
        archive.extractall(SITE)
    # GitHub Pages 没有 Next.js 服务端路由。页面间使用普通链接跳转；页内组件仍由原版 JS 驱动。
    bootstrap = r'''<script>
(()=>{const base='/harbor-zh';
const nativeFetch=window.fetch;
window.fetch=(input,options)=>{
 const url=new URL(input instanceof Request?input.url:input,location.href);
 if(url.origin===location.origin&&!url.pathname.startsWith(base+'/')){
  url.pathname=base+url.pathname;
  input=input instanceof Request?new Request(url,input):url;
 }
 return nativeFetch.call(window,input,options);
};
document.addEventListener('click',event=>{
 const link=event.target.closest?.('a[href]');
 if(!link||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||link.target||link.hasAttribute('download'))return;
 const url=new URL(link.href,location.href);
 if(url.origin===location.origin&&url.pathname.startsWith(base+'/')&&url.pathname!==location.pathname)event.stopImmediatePropagation();
},true);
})();
</script>'''
    for p in SITE.rglob('*'):
        if p.suffix not in ('.html', '.js', '.css'):
            continue
        content = p.read_text().replace('/favicons/favicon.ico', BASE + '/harbor-logo.png')
        if p.suffix == '.html':
            content = re.sub(r'\b(href|src|poster|action)="/(?!/|harbor-zh/)',
                             lambda m: m[1] + '="' + BASE + '/', content)
            content = content.replace('\\"/_next/', '\\"' + BASE + '/_next/')
            content = content.replace('<head>', '<head>' + bootstrap, 1)
            content = content.replace('https://docs.harborframework.com"', 'https://xingshuozhu1998.github.io/harbor-zh/"')
        elif p.suffix == '.js':
            # 使用 Mintlify 自身的 BASE_PATH 配置，不改正文、示例代码或第三方链接。
            content = content.replace('env.NEXT_PUBLIC_BASE_PATH??""', 'env.NEXT_PUBLIC_BASE_PATH??"/harbor-zh"')
            content = content.replace('"/_next/', '"' + BASE + '/_next/').replace("'/_next/", "'" + BASE + '/_next/')
            # 静态站点不连接本地开发服务器的热更新通道。
            content = content.replace('(n=s()).on("connect"', '(n=s({autoConnect:false})).on("connect"')
        else:
            content = re.sub(r'url\(([\"\']?)/(?!/|harbor-zh/)', lambda m: 'url(' + m[1] + BASE + '/', content)
        p.write_text(content)
    # Mintlify 的链接会省略结尾 /index；同时保留两种路径。
    for p in list(SITE.rglob('index/index.html')):
        shutil.copy2(p, p.parent.parent / 'index.html')
    guest = SITE / '_mintlify/api/user/index.html'
    guest.parent.mkdir(parents=True, exist_ok=True)
    guest.write_text('{"user":null}\n')
    # 提供“复制页面”所需的 Markdown 文本，以及文档索引。
    entries = []
    for p in sorted(DOCS.rglob('*.mdx')):
        rel = p.relative_to(DOCS).with_suffix('.md')
        out = SITE / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(p.read_text())
        entries.append(f'- [{rel.with_suffix("")}]({BASE}/{rel})')
    (SITE / 'llms.txt').write_text('# Harbor 中文文档\n\n' + '\n'.join(entries) + '\n')
    # API 参考页由 OpenAPI 自动生成，没有手写 MDX；补齐它们的 Markdown 下载。
    spec_path = DOCS / 'api-sdk/openapi.json'
    spec = json.loads(spec_path.read_text())
    generated = Path.home() / '.mintlify/previews/harbor-zh-export/mint/apps/client/src/_props/api-sdk'
    for p in generated.rglob('*.mdx'):
        match = re.search(r'^openapi: /api-sdk/openapi.json (\w+) (.+)$', p.read_text(), re.M)
        if not match:
            continue
        method, route = match.groups()
        operation = spec['paths'][route][method.lower()]
        dest = SITE / 'api-sdk' / p.relative_to(generated).with_suffix('.md')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f'# {method.upper()} {route}\n\n' + operation.get('description', '') + '\n\n```json\n' + json.dumps(operation, ensure_ascii=False, indent=2) + '\n```\n\n[完整 OpenAPI 定义](/harbor-zh/api-sdk/openapi.json)\n')
    shutil.copy2(spec_path, SITE / 'api-sdk/openapi.json')
    (SITE / 'llms-full.txt').write_text('\n\n'.join(p.read_text() for p in sorted(DOCS.rglob('*.mdx'))))
    urls = ['https://xingshuozhu1998.github.io/harbor-zh/' + p.parent.relative_to(SITE).as_posix().removeprefix('.').strip('/') for p in SITE.rglob('index.html') if '_mintlify' not in p.parts]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + html.escape(url) + '</loc></url>' for url in sorted(set(urls))) + '</urlset>')
    (SITE / '.nojekyll').touch()
    for name in ['serve.js', 'Start Docs.command', 'Start Docs.bat']:
        (SITE / name).unlink(missing_ok=True)
    print(f'静态页面：{len(list(SITE.rglob("*.html")))}；输出：{SITE}')


if __name__ == '__main__':
    fetch_assets()
    prepare_export()
    adapt_site()
