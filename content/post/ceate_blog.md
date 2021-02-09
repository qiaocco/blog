---
title: "搭建博客"
date: 2021-01-01T22:29:27+08:00
draft: false
---

1. 安装hugo `https://gohugo.io/`

2. 创建博客

    ```bash
    hugo new site blog
    ```

3. 添加主题

    ```bash
    git submodule add https://github.com/olOwOlo/hugo-theme-even themes/even
    ```

4. 创建第一篇文章

   ```bash
   hugo new post/first_post.md
   ```

5. 自定义域名 https://gohugo.io/hosting-and-deployment/hosting-on-github/