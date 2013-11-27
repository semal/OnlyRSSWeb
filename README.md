##Only RSS Web 项目

一个 `RSS` 阅读器的 Web 版本，基于 `Python`、`Django` 和 `MySQL`。

demo：rss.tonghs.com，用户名密码均为 tonghs，请不要删除已有项目，多谢。

**部署**

分 Web 端和后台脚本两部分。

Web 端：可使用 `nginx` + `uWSGI` 部署，`ubuntu 12.10` 测试可正常部署，其他发行版本未试。

后台脚本：用于定时获取订阅内容，可配合任务计划工作。

    crontab -e

添加以下语句：

    */5 * * * * python /home/username/update_service.py

**配置**

1. 修改 `Django` 配置文件，配置数据库，以 `MySQL` 为例。
2. 新建数据库 onlyrss 并同步数据表到 `MySQL`，注意，编码方式请选择 utf8。
3. 新建用户。可执行以下 SQL 脚本添加用户。


            use onlyrss;
            insert into OnlyRSS_user （username, password, name) values ('username', 'password', 'name');

**使用**

首次使用，使用用户名密码登录后可在设置中导入订阅列表或在首页输入订阅地址添加订阅。

**To do list**

1. 密码加密
2. 代码进一步优化
3. 改善成单用户使用模式

**已知问题**

1. 网络环境不理想情况下加载速度慢，即使是空列表
2. 前段 js 警告


**主要更新历史：**

2013-08-28 19:31

* 新建项目

2013-09-24 17:22

* 完成基本功能
    * 订阅添加
    * 滚动鼠标标记为已读
    * 点击项目标记为已读
    * 全部标记为已读
    * 点击查看全部更新订阅内容
* 添加网站图标（测试，目前为百度图标）
* 部分代码重构

2013-10-14 22:11

* 进一步完善功能
    * 功能基本完工
* 改进网站图标
* 开始总结bug
* 已经发布到公网

2013-10-19 5:26

* RSS相关功能已基本完成
    * 订阅添加/删除
    * 导入导出
    * 首页菜单
    * 文章更新独立成系统服务
* 用户登录
* 相关bug修改

2013-11-23

* 加载速度优化
    * 图片延迟加载
* 单用户模式
