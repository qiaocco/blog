---
title: "使用github actions部署博客"
date: 2021-01-10T22:20:24+08:00
draft: false
tags: ["hugo"]
---



# 背景

使用hugo搭建了博客，可以正常运行了。博客分为两个仓库，分别是源代码和编译后的静态文件。

```
# github

1. blog仓库：存放源代码
2. qiaocci.github.io仓库：存放静态文件
```

每次写完博客，需要先在本地编译，提交到qiaocci.github.io。然后把源代码提交到blog仓库。需要做两次提交操作，有点麻烦。



# 解决方案

我想到了使用github actions，提交源代码后，自动编译，部署到qiaocci.github.io。

<img src="https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210204223245.png" style="zoom: 67%;" />



解释一下最后一步：代码提交后，会触发github actions，自动把源文件编译成静态文件，然后把编译好的静态文件，推送到qiaocci.github.io，这样只需要推送一次代码，就能完成博客发布流程。



# 具体方法

在blog仓库，创建`.github/workflows/gh-pages.yml`文件：

```yaml
name: github pages # 任务名称

on: # 什么情况下会触发任务，为了方便调试，我写的情况比较多，大家可以只保留push的情况。
  push:
    branches:
      - "*" # Set a branch to deploy
  issues:
    types:
      - "opened"
  issue_comment:
    types: [created, edited]

jobs:
  deploy:
    runs-on: ubuntu-18.04
    steps:
      - uses: actions/checkout@v2 # 获取代码
        with:
          submodules: true # Fetch Hugo themes (true OR recursive)
          fetch-depth: 0 # Fetch all history for .GitInfo and .Lastmod

      - name: Setup Hugo # 安装hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: "0.79.1"
          # extended: true

      - name: Build
        run: hugo --minify # 使用minify参数，可以压缩assets文件

      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
          deploy_key: ${{ secrets.ACTIONS_DEPLOY_KEY }} # 默认情况下，不能把代码推送到其他仓库。如果确实要推送，需要设置一个deploy key。设置方法见文章末尾的链接。
          external_repository: qiaocci/qiaocci.github.io # 静态文件仓库地址
          publish_branch: master # default: gh-pages	# 推送的分支
          cname: blog.qiaocci.com # 自定义域名
```



参考：

1.  actions-hugo 文档：https://github.com/peaceiris/actions-hugo
2.  如何设置deploy key：https://github.com/peaceiris/actions-gh-pages#%EF%B8%8F-create-ssh-deploy-key
3. https://ruddra.com/hugo-deploy-static-page-using-github-actions/



