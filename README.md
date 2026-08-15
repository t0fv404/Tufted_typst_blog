# Fork From Tufted Blog Template 

个人用博客模板，fork 自 [Tufted-Blog-Template](https://github.com/Yousa-Mirage/Tufted-Blog-Template)，在 deepseek-v4-pro 的参与下进行了一定修改。模板相关代码仍然采用 MIT。

示例网站：https://t0fv404.codeberg.page/Tufted_typst_blog/

## 使用说明

基本编译方式和原仓库说明无异，请看原仓库 README 相关说明。

关于使用 codeberg pgae 且自定义域名的想法，请您修改 `.forgejo\workflows\deploy.yml` 的 `Deploy to Codeberg Pages` 为：
```yml
- name: Deploy to Codeberg Pages
uses: https://codeberg.org/git-pages/action@v2
with:
site: https://{yourdomain.com}/ # 注意修改
server: codeberg.page
token: ${{ forge.token }}
source: _site/
```