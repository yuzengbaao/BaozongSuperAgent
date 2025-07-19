@echo off
REM BaozongSuperAgent GitHub上传脚本 (Windows)
REM 生成时间: 2025-07-19 17:47:47

echo 🚀 开始上传BaozongSuperAgent到GitHub...

REM 进入GitHub准备目录
cd /d "C:\vscode\baozong_agent\github_ready"

REM 初始化Git仓库
echo 📁 初始化Git仓库...
git init

REM 添加所有文件
echo 📄 添加项目文件...
git add .

REM 提交初始版本
echo 💾 提交初始版本...
git commit -m "🎉 Initial release: BaozongSuperAgent v1.0.0"

REM 设置远程仓库
echo 🔗 添加远程仓库...
git remote add origin https://github.com/yuzengbaao/BaozongSuperAgent.git

echo 🌿 设置主分支...
git branch -M main

echo 📤 推送到GitHub...
git push -u origin main

echo.
echo 🎊 GitHub准备完成！
echo 📁 项目位置: C:\vscode\baozong_agent\github_ready
pause
