# PruneMate - Docker资源自动清理助手

<p align="center">
  <img width="400" height="400" alt="prunemate-logo" src="https://github.com/user-attachments/assets/0785ea56-88f6-4926-9ae1-de736840c378" />
</p>

<h1 align="center">PruneMate</h1>
<p align="center"><em>定时自动清理Docker镜像和资源的实用助手</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.3.1-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/python-3.12-yellow?style=for-the-badge&logo=python&logoColor=ffffff"/>
  <img src="https://img.shields.io/badge/docker-compose-0db7ed?style=for-the-badge&logo=docker&logoColor=ffffff"/>
  <img src="https://img.shields.io/badge/license-AGPLv3-orange?style=for-the-badge"/>
  <a href="https://hub.docker.com/r/anoniemerd/prunemate">
    <img src="https://img.shields.io/docker/pulls/anoniemerd/prunemate?style=for-the-badge&logo=docker&logoColor=ffffff&label=docker%20pulls"/>
  </a>
  <a href="https://www.buymeacoffee.com/anoniemerd">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"/>
  </a>
</p>

PruneMate 是一个简洁轻量的Web界面工具，帮助你**按计划自动清理Docker资源**。它基于Python（Flask）、Docker SDK、APScheduler和Gunicorn构建。

**通过定时清理未使用的镜像、容器、网络和卷，让你的Docker主机保持整洁高效。**

> ⚠️ **免责声明**：PruneMate 使用Docker原生的`prune`命令来删除未使用的资源。这意味着它会移除Docker认为“未使用”的容器、镜像、网络和卷。请注意卷的清理，因为它们可能包含重要数据。在启用自动计划之前，请务必了解将被清理的内容。作者对任何数据丢失或系统问题不承担责任。**风险自负。**

---

## ✨ 主要特性

- 🕐 **灵活的计划任务** - 支持每日、每周或每月清理，也可以设置为仅手动模式
- 🔀 **计划开关控制** - 可以启用或禁用自动计划，让PruneMate仅在手动触发时运行
- 🔍 **清理预览** - 在执行手动清理前，可以查看即将被删除的具体内容
- 🌍 **时区支持** - 可以配置本地时区
- 🕒 **12/24小时时间格式** - 选择你偏好的时间显示方式
- 🐳 **多主机管理** - 从一个界面管理多个Docker主机（需要在远程主机上部署docker-socket-proxy）
- 🧹 **选择性清理** - 可以选择清理的内容：容器、镜像、网络、卷和**构建缓存**
- 🏗️ **构建缓存清理** - 通过清理Docker构建缓存 reclaim大量空间（通常可以释放10GB以上）
- 📊 **历史统计** - 跟踪所有清理操作累计回收的空间和删除的资源数量
- 🏠 **主页集成** - 在你的Homepage仪表板上显示统计信息（支持登录认证）
- 🎨 **现代化UI** - 深色主题，带有流畅动画和响应式设计
- 🔒 **安全认证** - 可选的登录保护，支持密码哈希和Basic Auth
- 🏗️ **多架构支持** - 原生支持amd64和arm64 Docker镜像（Intel/AMD、树莓派、Apple Silicon）
- 🔒 **安全可控** - 手动触发时带有预览功能和详细日志
- 📈 **详细报告** - 清晰展示清理了哪些内容以及回收了多少空间

---

## 📋 V1.3.1 新增功能

- 🔀 **计划启用/禁用开关** - 新的UI开关控制自动计划
  - 计划部分新增“启用自动计划”开关
  - 允许仅运行手动清理而不影响计划任务
  - 调度器仍会每分钟心跳但在禁用时跳过执行
  - 设置会保存在config.json中，现有安装默认启用
- 🏗️ **多架构Docker镜像支持** - 一次构建，随处运行
  - 原生支持amd64和arm64架构
  - 无缝运行在Intel/AMD、树莓派4/5、Apple Silicon M1/M2/M3以及基于ARM的NAS上
  - 使用Docker Buildx多平台构建进行高效分发
  - ARM系统不再需要本地构建
  - 单个docker-compose.yaml适用于所有架构

### 修复
- 🏠 **登录状态下的Homepage小部件集成** - 统计端点现在在登录启用时也可访问
  - `/stats` 和 `/api/stats` 端点无需认证即可访问
  - 确保在启用登录时Homepage和Dashy小部件仍能显示统计信息
  - 向后兼容：端点仅包含非敏感的Docker清理统计数据

### 变更
- 📦 **Docker Compose默认设置** - 从本地构建改为预构建的多架构镜像
  - docker-compose.yaml现在默认使用`image: anoniemerd/prunemate:latest`
  - 在拉取时自动检测正确的架构（amd64/arm64）
  - 显著加快部署速度和减少初始设置时间

---

## 📷 截图

### 主仪表板
PruneMate仪表板的整体外观和风格

<p align="center">
  <img width="400" height="800" src="https://github.com/user-attachments/assets/f69df1a9-5a40-47a6-a955-91f6449f1ea2" />
</p>

### 认证页面
登录页面（在docker-compose.yaml环境变量中启用时）

<p align="center">
  <img width="400" height="800" src="https://github.com/user-attachments/assets/29ea359c-452e-4e1d-8567-c8fd65b08d4e" /> 
</p>

### 外部Docker主机
通过[docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)添加外部Docker主机

<p align="center">
  <img width="400" height="400" alt="prunemate-cleanup" src="https://github.com/user-attachments/assets/28abdbe4-bd9e-4272-a6fc-24a4a8dc83bb" />
</p>

### 通知设置
配置通过Gotify、ntfy.sh、Discord或Telegram接收清理结果通知

<p align="center">
  <img width="400" height="400" alt="prunemate-notifications" src="https://github.com/user-attachments/assets/73a06c4d-fffa-40eb-a010-239d7d364004" /> 
</p>

### 清理预览
显示下一次清理运行时将被删除的Docker资源的简要界面，无论是手动触发还是计划执行

<p align="center">
  <img width="400" height="400" alt="prunemate-preview" src="https://github.com/user-attachments/assets/34fb445d-8956-46e8-84df-b6718db3f556" /> 
</p>


---

## 🚀 使用Docker Compose快速开始

### 前置条件

- 已安装Docker和Docker Compose
- 可访问Docker套接字（`/var/run/docker.sock`）

### 安装步骤

1. **创建`docker-compose.yaml`文件：**

```yaml
services:
  prunemate:
    image: anoniemerd/prunemate:latest  # 支持amd64和arm64
    container_name: prunemate
    ports:
      - "7676:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs:/var/log
      - ./config:/config
    environment:
      - PRUNEMATE_TZ=Europe/Amsterdam # 更改为你所在的时区
      - PRUNEMATE_TIME_24H=true # false表示使用12小时格式（AM/PM）
      # 可选：启用认证（使用以下命令生成哈希：docker run --rm anoniemerd/prunemate python prunemate.py --gen-hash "password")
      # - PRUNEMATE_AUTH_USER=admin
      # - PRUNEMATE_AUTH_PASSWORD_HASH=your_base64_encoded_hash_here
    restart: unless-stopped
```

2. **启动PruneMate：**

```bash
docker-compose up -d
```

3. **访问PruneMate的Web界面：**

在浏览器中打开：

```
http://<你的服务器IP>:7676/
```

---

## 🚀 使用Docker Run快速开始

**使用Docker命令行：**

```bash
docker run -d \
  --name prunemate \
  -p 7676:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/logs:/var/log \
  -v $(pwd)/config:/config \
  -e PRUNEMATE_TZ=Europe/Amsterdam \
  -e PRUNEMATE_TIME_24H=true \
  --restart unless-stopped \
  anoniemerd/prunemate:latest
```

**访问Web界面：**

```
http://<你的服务器IP>:7676/
```



**卷说明：**
- `/var/run/docker.sock` - 用于访问Docker API
- `./logs` - 存储应用日志（自动轮转，每个文件最大5MB）
- `./config` - 存储配置和状态文件

---

## ⚙️ 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `PRUNEMATE_TZ` | `UTC` | 计划任务使用的时区（例如：`Europe/Amsterdam`, `Asia/Shanghai`） |
| `PRUNEMATE_TIME_24H` | `true` | 时间格式：`true`为24小时制，`false`为12小时制（AM/PM） |
| `PRUNEMATE_CONFIG` | `/config/config.json` | 配置文件路径 |
| `PRUNEMATE_AUTH_USER` | `admin` | 认证用户名（可选，仅在启用认证时使用） |
| `PRUNEMATE_AUTH_PASSWORD_HASH` | _(无)_ | Base64编码的密码哈希（设置后启用认证） |

### 🔐 认证（可选）

PruneMate 支持对Web界面和API端点进行可选的密码保护。

**主要特性：**
- 🔒 **基于表单的登录** - 与应用设计风格一致的登录页面
- 🔑 **安全哈希** - 使用scrypt加密密码（行业标准）
- 🌐 **API兼容性** - 为外部工具（Homepage、Dashy等）提供Basic Auth支持
- 🚪 **注销按钮** - 方便的会话管理

**启用认证步骤：**

1. **使用内置工具生成密码哈希：**

```bash
docker run --rm anoniemerd/prunemate:latest python prunemate.py --gen-hash "your_password"
```

此命令会输出Base64编码的哈希（适合YAML格式，无特殊字符）：
```
c2NyeXB0OjMyNzY4Ojg6MSRvcDdnZFlGR1JmRFp4Y1RjJDBmMzNlYzc4NzExZTI4MzllYjk0MWFiOTZkOGUyZGNjNGRhMzU2NTlmMGI1ZDg0NjhjZTdkMThhODhmNmQ3ZGRhOGU4YzdmMDYxMWZiNzAyYjA0ZGNhNTBjZWMxZjFlYzc3ZjhlNzJhYmM0MmQ3OTQ5NDM2MDUzZWRlZjlhZGY0
```

> **为什么使用Base64？** 原始的scrypt哈希包含`$`字符，Docker Compose会将其解释为环境变量，导致哈希损坏。Base64编码生成的字母数字字符串可以被YAML安全处理，无需转义。

> **✅ 适合使用的特殊字符：**
> - 井号：`#`
> - at符号：`@` 
> - 百分号：`%`
> - 星号：`*`
> - 和号：`&`
> - 脱字符：`^`
>
> **⚠️ 需要避免的字符：**
> - 感叹号：`!`（bash历史扩展）
> - 美元符号：`$`（变量扩展 - 即使Base64编码后，在某些情况下仍可能导致问题）
>
> **安全示例：**
> - `MyPassword#123`
> - `Test@secure%pass`
> - `prunemate&admin^2024`
> - `MyPass*Admin#99`

2. **添加到docker-compose.yaml：**

```yaml
environment:
  - PRUNEMATE_AUTH_USER=admin  # 可选（默认：admin）
  - PRUNEMATE_AUTH_PASSWORD_HASH=c2NyeXB0OjMyNzY4Ojg6MSRvcDdnZFlGR1JmRFp4Y1RjJDBmMzNlYzc4...
```

3. **重启容器：**

```bash
docker-compose up -d
```

**重要注意事项：**
- 认证是**可选的** - 仅当设置了`PRUNEMATE_AUTH_PASSWORD_HASH`时才启用
- 不设置哈希变量时，应用以开放模式运行（向后兼容）
- 对于API客户端（Homepage等），使用实际密码而非哈希进行Basic Auth认证
- 哈希使用Base64编码以防止Docker Compose将`$`字符解释为变量


### Web界面设置

访问Web界面`http://localhost:7676/`（或你的服务器IP）进行配置：

**计划设置：**
- **频率**：每日、每周或每月
- **时间**：清理任务的执行时间（支持12h和24h格式）
- **日期**：每周的星期几或每月的几号

**清理选项：**
- ☑️ 所有未使用的容器
- ☑️ 所有未使用的镜像  
- ☑️ 所有未使用的网络
- ☑️ 所有未使用的卷

**通知设置：**
- **提供商**：Gotify、ntfy.sh、Discord或Telegram
- **配置**：提供商特定的凭据（Gotify的URL/Token，ntfy的URL/Topic，Discord的Webhook URL，Telegram的Bot Token/Chat ID）
- **优先级**：低（静默）、中、高优先级通知（取决于提供商）
- **仅在发生变化时通知**：仅在实际清理了资源时发送通知

---

## 🧠 工作原理

1. **调度器每分钟运行一次**，检查是否到了执行时间
2. **加载最新配置**，从持久存储中读取
3. **执行Docker prune命令**，针对选定的资源类型
4. **收集统计数据**，记录删除的内容和回收的空间
5. **更新历史统计**，累积数据（空间、数量、时间戳）
6. **发送通知**（如果配置并启用）
7. **记录所有操作**，包含时区感知的时间戳

📊 **[查看详细架构和流程图](ARCHITECTURE.md)**

### 文件结构

```
/config/
├── config.json          # 配置文件（持久存储）
├── stats.json           # 历史统计数据（累积数据）
├── prunemate.lock       # 防止并发运行
└── last_run_key         # 跟踪上次成功运行

/var/log/
└── prunemate.log        # 应用日志（自动轮转，最大5MB）
```

### 历史统计

PruneMate 跟踪所有清理操作的累积统计数据：

**统计指标：**
- 💾 **总回收空间** - 累积释放的磁盘空间（以MB/GB/TB显示）
- 📦 **已删除容器** - 累计删除的未使用容器数量
- 🖼️ **已删除镜像** - 累计删除的未使用镜像数量
- 🔗 **已删除网络** - 累计删除的未使用网络数量
- 💿 **已删除卷** - 累计删除的未使用卷数量
- 🔄 **总清理次数** - 执行清理的总次数
- 📅 **首次运行** - 第一次清理执行的时间戳
- 🕐 **上次运行** - 最近一次清理执行的时间戳

**技术细节：**
- 统计数据持久保存在`/config/stats.json`中，使用文件锁定实现原子写入
- 每次清理后更新，无论是否删除了资源
- 时间戳是时区感知的，遵循`PRUNEMATE_TZ`设置
- UI中显示的日期和时间遵循配置的12h/24h格式
- 统计数据在容器重启和更新后保持
- 手动清理后UI自动刷新

---

## 🔔 通知设置

### Gotify

[Gotify](https://gotify.net/) 是一个自托管的通知服务。

**设置步骤：**
1. 安装并运行Gotify服务器
2. 在Gotify中创建一个新应用
3. 复制应用令牌
4. 在PruneMate中配置：
   - **提供商**：Gotify
   - **URL**：`https://your-gotify-server.com`
   - **Token**：你的应用令牌

### ntfy.sh

[ntfy.sh](https://ntfy.sh/) 是一个简单的发布-订阅通知服务（可自托管或使用公共服务）。

**设置步骤：**
1. 选择一个独特的主题名称（例如：`prunemate-alerts`）
2. 在PruneMate中配置：
   - **提供商**：ntfy
   - **URL**：`https://ntfy.sh`（或你的自托管实例，支持`username:password@host`格式）
   - **Topic**：你选择的主题名称
   - **Token**：（可选）Bearer令牌用于认证

**认证选项：**
- **Bearer令牌**：推荐用于API访问令牌（优先级更高）
- **URL凭据**：使用`https://username:password@ntfy.example.com`格式（符合RFC 3986标准）
- **无认证**：适用于公共主题

**订阅通知：**
- **Web**：访问`https://ntfy.sh/your-topic`
- **移动**：安装ntfy应用（[Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)）并订阅主题
- **桌面**：使用ntfy桌面应用或浏览器

### Discord

[Discord](https://discord.com/) Webhook 允许直接将通知发送到你的Discord服务器。

**设置步骤：**
1. 打开Discord服务器设置
2. 进入**集成** → **Webhook**
3. 点击**新建Webhook**或编辑现有Webhook
4. 复制**Webhook URL**
5. 在PruneMate中配置：
   - **提供商**：Discord
   - **Webhook URL**：`https://discord.com/api/webhooks/...`

**优先级颜色：**
- **低**：绿色（信息性）
- **中**：橙色（警告）
- **高**：红色（严重）

### Telegram

[Telegram Bot API](https://core.telegram.org/bots) 允许通过Telegram机器人发送通知。

**设置步骤：**
1. 打开Telegram，搜索**@BotFather**
2. 发送`/newbot`并按照提示操作
3. 为你的机器人命名（例如："PruneMate Notifications"）
4. 为你的机器人设置一个以"bot"结尾的用户名（例如："prunemate_notif_bot"）
5. 复制**Bot Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）
6. 获取**Chat ID**：
   - **简单方法**：发送消息给**@userinfobot**或**@getmyid_bot**获取Chat ID
   - **替代方法**：发送消息给你的机器人，然后访问`https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`找到`"chat":{"id":123456789}`
7. 在PruneMate中配置：
   - **提供商**：Telegram
   - **Bot Token**：从BotFather获取的机器人令牌
   - **Chat ID**：你的数字聊天ID（或`@channelname`用于频道）

**优先级行为：**
- **低**：静默通知（无声音）
- **中/高**：正常通知（带声音）

**高级用法：**
- **群组**：将机器人添加到群组，获取群组Chat ID（以`-`开头）
- **频道**：使用频道用户名加`@`（例如：`@mychannel`）或数字ID

---


## 🌐 多主机设置（可选）

PruneMate 可以从单个界面管理多个Docker主机。每次清理操作会在所有启用的主机上运行，并汇总结果。

### 安全第一：使用Docker Socket Proxy

⚠️ **永远不要直接暴露Docker套接字！** 请始终使用[docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)限制API访问。

### 快速设置

**1. 在每个远程主机上部署代理：**

```yaml
services:
  dockerproxy:
    image: ghcr.io/tecnativa/docker-socket-proxy:latest
    environment:
      - CONTAINERS=1
      - IMAGES=1
      - NETWORKS=1
      - VOLUMES=1
      - BUILD=1         # 清理构建缓存必需
      - POST=1          # 清理操作必需
    ports:
      - "2375:2375"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
```

> **⚠️ 重要**：`BUILD=1`环境变量**必须设置**才能启用Docker构建缓存清理。否则，构建缓存清理操作将因403错误失败。

**2. 在PruneMate UI中添加主机：**
- 导航到**Docker Hosts**部分
- 点击**Add New Host**
- 输入名称（例如："NAS"）和URL（例如：`tcp://192.168.1.50:2375`）
- 切换主机的启用/禁用状态

**3. 测试连接：**
点击**Run now**并检查日志是否成功连接到所有主机。


### 故障排除

- **连接拒绝**：验证代理是否正在运行（`docker ps`）并且2375端口可访问
- **权限拒绝**：确保代理设置了`POST=1`环境变量
- **主机被跳过**：检查URL格式是否以`tcp://`、`http://`或`https://`开头

---

## 🏠 Homepage仪表板集成

PruneMate 在`/api/stats`提供了一个自定义API端点，返回历史统计数据，格式兼容[Homepage](https://gethomepage.dev/)仪表板小部件。

<p align="center">
  <img width="400" height="400" alt="prunemate-homepage" src="https://github.com/user-attachments/assets/942169f6-bc16-4cef-8b46-3ac012fe7fec" /> 
</p>

### 设置

将以下配置添加到你的Homepage `services.yaml`：

```yaml
- PruneMate:
    href: http://<your-server-ip>:7676
    description: Docker自动清理工具
    icon: https://cdn.jsdelivr.net/gh/selfhst/icons@main/webp/prunemate.webp
    widget:
      type: customapi
      url: http://<your-server-ip>:7676/api/stats
      mappings:
        - field: pruneRuns
          label: 清理次数
          format: number
        - field: lastRunText
          label: 上次运行
        - field: imagesDeleted
          label: 已清理镜像
          format: number
        - field: spaceReclaimedHuman
          label: 已节省空间
```

### 可用字段

`/api/stats`端点返回以下字段：

| 字段 | 类型 | 描述 | Homepage格式 |
|-------|------|-------------|-----------------|
| `pruneRuns` | number | 执行清理的总次数 | `number` |
| `containersDeleted` | number | 累计删除的容器总数 | `number` |
| `imagesDeleted` | number | 累计删除的镜像总数 | `number` |
| `networksDeleted` | number | 累计删除的网络总数 | `number` |
| `volumesDeleted` | number | 累计删除的卷总数 | `number` |
| `buildCacheDeleted` | number | 累计删除的构建缓存条目数 | `number` |
| `spaceReclaimed` | number | 累计回收的空间（字节） | `number` |
| `spaceReclaimedHuman` | string | 人类可读的回收空间（例如："2.5 GB"） | `text` |
| `lastRunText` | string | 相对时间文本（例如："2小时前"） | `text` |
| `lastRunTimestamp` | number | 上次运行的Unix时间戳（秒） | `number` |
| `lastRun` | string | 最近一次清理的ISO时间戳 | `date` |
| `firstRun` | string | 第一次清理的ISO时间戳 | `date` |

### 示例 /api/stats 输出

```json
{
  "pruneRuns": 42,
  "containersDeleted": 156,
  "imagesDeleted": 89,
  "networksDeleted": 12,
  "volumesDeleted": 7,
  "buildCacheDeleted": 715,
  "spaceReclaimed": 5368709120,
  "spaceReclaimedHuman": "5.00 GB",
  "lastRunText": "2小时前",
  "lastRunTimestamp": 1733454000,
  "lastRun": "2025-12-06T03:00:00+01:00",
  "firstRun": "2025-01-15T03:00:00+01:00"
}
```
---

## 🧠 故障排除

| 问题 | 解决方案 |
|---------|----------|
| ❌ 无法访问Web界面 | • 检查7676端口是否可用且未被防火墙阻止<br>• 验证容器是否正在运行：`docker ps`<br>• 查看日志：`docker logs prunemate` |
| 🏗️ ARM架构错误 | • V1.3.1及以上版本：镜像原生支持多架构（amd64 + arm64）<br>• 拉取`anoniemerd/prunemate:latest` - 会自动检测你的平台<br>• 无需本地构建！<br>• 如果使用旧版本，在docker-compose.yaml中使用`build: .` |
| ⚙️ 容器无法启动 | • 查看启动错误：`docker logs prunemate`<br>• 验证Docker套接字是否可访问<br>• 检查7676端口是否已被占用 |
| 🔒 权限拒绝错误 | • 确保`/var/run/docker.sock`存在且可访问<br>• 在Linux系统上，Docker守护进程必须正在运行<br>• 运行Docker的用户必须有适当的权限 |
| 🕐 日志/计划中的时区错误 | • 正确设置`PRUNEMATE_TZ`环境变量<br>• 修改后重启容器：`docker-compose restart`<br>• 验证日志中的时区是否符合预期 |
| 📧 通知无法发送 | • 在Web界面中测试通知设置<br>• 验证通知服务器URL是否可访问<br>• 检查令牌/主题是否正确<br>• 查看日志中的错误信息 |
| 🗂️ 配置不持久化 | • 确保`./config`卷已正确挂载<br>• 检查主机`./config`目录的文件权限<br>• 验证容器是否有写入权限 |
| 🧹 计划清理未执行 | • 检查Web界面中的计划配置<br>• 验证时区设置正确<br>• 查看日志：“Next scheduled run”消息<br>• 确保容器持续运行 |

---

### 日志

**日志包含内容：**
- ✅ 调度器心跳（每分钟）
- 📝 配置变更
- 🧹 清理任务执行及结果
- 📨 通知发送状态
- ❌ 错误消息和警告

---

## 📜 版本更新日志

### [V1.3.1] - 2025年12月

#### 新增
- 🔀 **计划启用/禁用开关** - 新增UI开关控制自动计划
  - 计划部分添加“启用自动计划”开关
  - 允许仅运行手动清理而不影响计划任务
  - 调度器仍每分钟心跳但禁用时跳过执行
  - 设置保存在config.json中，现有安装默认启用
- 🏗️ **多架构Docker镜像支持** - 一次构建，随处运行
  - 原生支持amd64和arm64架构
  - 无缝运行在Intel/AMD、树莓派4/5、Apple Silicon M1/M2/M3以及基于ARM的NAS上
  - 使用Docker Buildx多平台构建进行高效分发
  - ARM系统不再需要本地构建
  - 单个docker-compose.yaml适用于所有架构

#### 修复
- 🏠 **登录状态下的Homepage小部件集成** - 统计端点现在在登录启用时也可访问
  - `/stats` 和 `/api/stats` 端点无需认证即可访问
  - 确保在启用登录时Homepage和Dashy小部件仍能显示统计信息
  - 向后兼容：端点仅包含非敏感的Docker清理统计数据
- 📊 **计划配置日志** - 在有效配置输出中添加`schedule_enabled`
  - 正确记录包括新开关在内的所有计划设置

#### 变更
- 📦 **Docker Compose默认设置** - 从本地构建改为预构建的多架构镜像
  - docker-compose.yaml现在默认使用`image: anoniemerd/prunemate:latest`
  - 在拉取时自动检测正确的架构（amd64/arm64）
  - 显著加快部署速度和减少初始设置时间

📖 **[查看完整更新日志](CHANGELOG.md)**

---

## 📬 支持

有问题需要帮助？

- 🐛 **Bug报告：** [在GitHub上提交Issue](https://github.com/anoniemerd/PruneMate/issues)
- 💡 **功能请求：** [在GitHub上提交Issue](https://github.com/anoniemerd/PruneMate/issues)
- 💬 **问题与讨论：** [在GitHub上发起讨论](https://github.com/anoniemerd/PruneMate/discussions)
- ⭐ **喜欢PruneMate？** 给它一个星标！

---

## ☕ 支持项目

如果你觉得PruneMate很有用，并希望支持项目的开发，欢迎请我买杯咖啡！

<p align="center">
  <a href="https://www.buymeacoffee.com/anoniemerd" target="_blank">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"/>
  </a>
</p>

你的支持帮助我投入更多时间维护和改进PruneMate！ ❤️

---

## 👤 作者与许可

**作者：** Anoniemerd  
🐙 GitHub：<https://github.com/anoniemerd>  
📦 仓库：<https://github.com/anoniemerd/PruneMate>

---

## 👥 贡献者

感谢所有为PruneMate做出贡献的开发者！

### 贡献者
- **[@difagume](https://github.com/difagume)** - 🔐 认证系统实现（V1.3.0）
- **[@shollyethan](https://github.com/shollyethan)** - 🎨 Logo重新设计，并添加到Self-Hosted Dashboard Icons

### 项目维护者/所有者
- **[anoniemerd](https://github.com/anoniemerd)** - 项目创建者和维护者


---

### 📜 许可 — AGPLv3

本项目采用**GNU Affero通用公共许可证第3版（AGPL-3.0）** 许可。

在使用、修改或分发本软件时，你**必须**：

- 保留此版权声明
- 披露任何修改版本的源代码
- 若用于提供网络服务，必须披露源代码
- 任何衍生作品必须采用**AGPL-3.0**许可

请查看完整的许可证文本：[`LICENSE`](./LICENSE)

### ⚠️ 免责声明

**风险自负。** PruneMate 按“原样”提供，不提供任何形式的担保。作者和贡献者不对以下内容负责：
- 因清理Docker资源导致的数据丢失
- 服务中断或停机
- 系统不稳定或性能问题
- 因使用或误用本软件导致的任何损失

请始终：
- ✅ 明确了解将被删除的资源
- ✅ 备份重要数据和配置
- ✅ 在清理操作后查看日志
- ✅ 从保守设置开始

© 2025 – PruneMate 项目

---

<p align="center">
  <strong>使用PruneMate，让你的Docker主机保持干净整洁！ 🐳🧹</strong>
</p>