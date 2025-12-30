
# PruneMate

<p align="center">
  <img width="400" height="400" alt="prunemate-logo" src="https://github.com/user-attachments/assets/0785ea56-88f6-4926-9ae1-de736840c378" />
</p>

<h1 align="center">PruneMate</h1>
<p align="center"><em>Docker 镜像与资源清理助手，支持定时任务！</em></p>

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

一个简洁轻量的 Web 界面，用于**按计划自动清理 Docker 资源**。  
基于 Python（Flask）· Docker SDK · APScheduler · Gunicorn 构建。

**通过定时清理未使用的镜像、容器、网络和卷，让你的 Docker 主机保持干净整洁。**

> ⚠️ **免责声明**：PruneMate 使用 Docker 原生的 `prune` 命令删除未使用资源。  
> 这意味着它会删除 Docker 判定为“未使用”的容器、镜像、网络和卷——特别要注意卷，因为其中可能包含重要数据。  
> 在启用自动调度之前，请务必确认你已经理解哪些内容会被清理。作者不对任何数据丢失或系统问题负责。**使用本工具需自担风险。**

***

## ✨ 功能特性

- 🕐 **灵活调度**：支持每天、每周或每月运行清理任务，亦可设置为仅手动模式  
- 🔀 **调度开关控制**：可启用/禁用自动调度，让 PruneMate 只在手动触发时运行  
- 🔍 **清理预览**：在执行手动清理前，先预览将要删除的内容  
- 🌍 **时区感知**：可配置你的本地时区  
- 🕒 **12/24 小时制**：自由选择时间显示格式  
- 🐳 **多主机支持**：在一个界面中管理多台 Docker 主机（远程主机需使用 docker-socket-proxy）  
- 🧹 **选择性清理**：可选择要清理的资源类型：容器、镜像、网络、卷、**构建缓存**  
- 🏗️ **构建缓存清理**：通过清理 Docker 构建缓存回收大量空间（通常可达 10GB+）  
- 📊 **全时统计**：统计所有运行中累计释放的空间和删除的资源数量  
- 🏠 **Homepage 集成**：在 Homepage 仪表盘中展示统计信息（在启用认证时也能使用）  
- 🎨 **现代化界面**：暗色主题、平滑动画与响应式设计  
- 🔒 **安全认证**：可选登录保护，支持密码哈希与 Basic Auth  
- 🏗️ **多架构支持**：原生支持 amd64 与 arm64 Docker 镜像（Intel/AMD、树莓派、Apple Silicon 等）  
- 🔒 **安全可控**：手动触发配合预览与详细日志  
- 📈 **详细报告**：清晰展示具体清理内容以及回收了多少空间  

***

## 📋 V1.3.1 更新内容

- 🔀 **调度启用/禁用开关**：可仅运行手动清理，而不启用定时自动化  
- 🏗️ **多架构支持**：Docker 镜像现在开箱即用支持 amd64 与 arm64  
- 🏠 **修复 Homepage 小组件集成**：在启用认证时，统计端点可正常工作  
- 📦 **改进 Docker Compose 默认配置**：默认使用预构建的多架构镜像，无需本地构建  

查看完整更新说明请见 [CHANGELOG.md](./CHANGELOG.md)。

***

## 📷 截图

### 主控制台  
PruneMate 控制台的整体界面与外观。

<p align="center">
  <img width="400" height="800" src="https://github.com/user-attachments/assets/f69df1a9-5a40-47a6-a955-91f6449f1ea2" />
</p>

### 认证页面  
登录页面（当在 docker-compose.yaml 的环境变量中启用了认证时显示）。

<p align="center">
  <img width="400" height="800" src="https://github.com/user-attachments/assets/29ea359c-452e-4e1d-8567-c8fd65b08d4e" /> 
</p>

### 外部 Docker 主机  
通过 [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) 添加外部 Docker 主机。

<p align="center">
  <img width="400" height="400" alt="prunemate-cleanup" src="https://github.com/user-attachments/assets/28abdbe4-bd9e-4272-a6fc-24a4a8dc83bb" />
</p>

### 通知设置  
通过 Gotify、ntfy.sh、Discord 或 Telegram 配置通知，以便及时了解清理结果。

<p align="center">
  <img width="400" height="400" alt="prunemate-notifications" src="https://github.com/user-attachments/assets/73a06c4d-fffa-40eb-a010-239d7d364004" /> 
</p>

### 清理预览  
简洁的界面展示在下一次清理任务（手动或定时）中将要被清理的 Docker 资源。

<p align="center">
  <img width="400" height="400" alt="prunemate-preview" src="https://github.com/user-attachments/assets/34fb445d-8956-46e8-84df-b6718db3f556" /> 
</p>

---

## 🚀 使用 Docker Compose 快速开始

### 前置条件

- 已安装 Docker 和 Docker Compose  
- 可以访问 Docker 套接字（`/var/run/docker.sock`）

### 安装步骤

1. **创建 `docker-compose.yaml` 文件：**

```yaml
services:
  prunemate:
    image: anoniemerd/prunemate:latest  # 支持 amd64 和 arm64
    container_name: prunemate
    ports:
      - "7676:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs:/var/log
      - ./config:/config
    environment:
      - PRUNEMATE_TZ=Europe/Amsterdam # 修改为你需要的时区
      - PRUNEMATE_TIME_24H=true # false 为 12 小时制（AM/PM）
      # 可选：启用认证（生成哈希命令：docker run --rm anoniemerd/prunemate python prunemate.py --gen-hash "password"）
      # - PRUNEMATE_AUTH_USER=admin
      # - PRUNEMATE_AUTH_PASSWORD_HASH=your_base64_encoded_hash_here
    restart: unless-stopped
```

2. **启动 PruneMate：**

```bash
docker-compose up -d
```

3. **访问 PruneMate Web 界面：**

在浏览器中打开：

```
http://<你的服务器 IP>:7676/
```

***

## 🚀 使用 Docker Run 快速开始

**使用 Docker CLI：**

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

**访问 Web 界面：**

```
http://<你的服务器 IP>:7676/
```

**挂载卷说明：**

- `/var/run/docker.sock`：用于访问 Docker API（必须挂载）  
- `./logs`：存储应用日志（滚动日志，单个文件最大约 5MB）  
- `./config`：存储配置和状态文件  

***

## ⚙️ 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PRUNEMATE_TZ` | `UTC` | 调度使用的时区（例如 `Europe/Amsterdam`、`America/New_York`） |
| `PRUNEMATE_TIME_24H` | `true` | 时间格式：`true` 为 24 小时制，`false` 为 12 小时制（AM/PM） |
| `PRUNEMATE_CONFIG` | `/config/config.json` | 配置文件路径 |
| `PRUNEMATE_AUTH_USER` | `admin` | 认证用户名（可选，仅在启用认证时使用） |
| `PRUNEMATE_AUTH_PASSWORD_HASH` | _(无)_ | Base64 编码的密码哈希（设置后启用认证） |

### 🔐 认证（可选）

PruneMate 支持为 Web 界面和 API 端点启用可选密码保护。

**主要特性：**

- 🔒 **表单登录**：与应用风格一致的登录页面  
- 🔑 **安全哈希**：密码使用 scrypt 进行哈希（行业标准）  
- 🌐 **API 兼容**：为外部工具（Homepage、Dashy 等）提供 Basic Auth 兼容模式  
- 🚪 **注销按钮**：方便的会话管理  

**启用认证的步骤：**

1. **使用内置工具生成密码哈希：**

```bash
docker run --rm anoniemerd/prunemate:latest python prunemate.py --gen-hash "your_password"
```

这会输出一个 Base64 编码的哈希（适用于 YAML，不会产生特殊字符问题）：

```
c2NyeXB0OjMyNzY4Ojg6MSRvcDdnZFlGR1JmRFp4Y1RjJDBmMzNlYzc4NzExZTI4MzllYjk0MWFiOTZkOGUyZGNjNGRhMzU2NTlmMGI1ZDg0NjhjZTdkMThhODhmNmQ3ZGRhOGU4YzdmMDYxMWZiNzAyYjA0ZGNhNTBjZWMxZjFlYzc3ZjhlNzJhYmM0MmQ3OTQ5NDM2MDUzZWRlZjlhZGY0
```

> **为什么使用 Base64？**  
> 原始 scrypt 哈希中包含 `$` 字符，而 Docker Compose 会把 `$` 解析为环境变量，从而破坏哈希。  
> 使用 Base64 编码后得到的字符串只包含字母和数字，YAML 可以安全处理，无需转义。

> **✅ 建议使用的特殊字符（在密码中）：**  
> - 井号：`#`  
> - at 符号：`@`  
> - 百分号：`%`  
> - 星号：`*`  
> - 和号：`&`  
> - 插入号：`^`  
>
> **⚠️ 建议避免的字符：**  
> - 感叹号：`!`（可能触发 shell 历史记录扩展）  
> - 美元符：`$`（变量展开——即便 Base64 后，在某些场景仍可能有问题）  
>
> **安全示例：**  
> - `MyPassword#123`  
> - `Test@secure%pass`  
> - `prunemate&admin^2024`  
> - `MyPass*Admin#99`  

2. **将结果写入 docker-compose.yaml：**

```yaml
environment:
  - PRUNEMATE_AUTH_USER=admin  # 可选（默认：admin）
  - PRUNEMATE_AUTH_PASSWORD_HASH=c2NyeXB0OjMyNzY4Ojg6MSRvcDdnZFlGR1JmRFp4Y1RjJDBmMzNlYzc4...
```

3. **重启容器：**

```bash
docker-compose up -d
```

**重要说明：**

- 认证为**可选**，仅在设置了 `PRUNEMATE_AUTH_PASSWORD_HASH` 时启用  
- 未设置该变量时，应用以开放模式运行（向下兼容）  
- 对于 API 客户端（如 Homepage），使用 Basic Auth 时需填写**明文密码**（而不是哈希）  
- 哈希采用 Base64 编码，避免 Docker Compose 将 `$` 解析为变量  

### Web 界面设置

通过 `http://localhost:7676/`（或你的服务器 IP）访问 Web 界面进行配置：

**调度设置：**

- **频率**：每天、每周或每月  
- **时间**：清理任务执行时间（支持 12/24 小时制）  
- **日期**：每周的星期几（用于每周），或每月的几号（用于每月）  

**清理选项：**

- ☑️ 所有未使用的容器  
- ☑️ 所有未使用的镜像  
- ☑️ 所有未使用的网络  
- ☑️ 所有未使用的卷  

**通知设置：**

- **服务提供方**：Gotify、ntfy.sh、Discord 或 Telegram  
- **配置项**：不同服务对应的凭据（Gotify 的 URL/Token，ntfy 的 URL/Topic，Discord 的 Webhook URL，Telegram 的 Bot Token/Chat ID）  
- **优先级**：低（静默）、中或高优先级通知（取决于提供方支持）  
- **仅在有变化时通知**：只在实际清理了内容时发送通知  

***

## 🧠 工作原理

1. **调度器**每分钟检查一次是否到了执行时间  
2. **从持久化存储加载最新配置**  
3. **根据所选资源类型执行 Docker prune 命令**  
4. **统计删除了什么以及释放的空间**  
5. **更新全时统计**（累计空间、数量和时间戳）  
6. **发送通知**（如果已配置并启用）  
7. **记录日志**（使用带时区的时间戳）  

📊 **查看详细架构与流程图：** [ARCHITECTURE.md](ARCHITECTURE.md)

### 文件结构

```text
/config/
├── config.json          # 配置（持久化）
├── stats.json           # 全时统计（累计数据）
├── prunemate.lock       # 防止并发运行
└── last_run_key         # 记录最近一次成功运行

/var/log/
└── prunemate.log        # 应用日志（滚动日志，单文件最大约 5MB）
```

### 全时统计

PruneMate 会对所有清理任务进行累积统计：

**统计指标：**

- 💾 **总计释放空间**：累计释放的磁盘空间（界面中以 MB/GB/TB 显示）  
- 📦 **已删除容器数**：删除的未使用容器总数  
- 🖼️ **已删除镜像数**：删除的未使用镜像总数  
- 🔗 **已删除网络数**：删除的未使用网络总数  
- 💿 **已删除卷数**：删除的未使用卷总数  
- 🔄 **清理运行次数**：执行 prune 的总次数  
- 📅 **首次运行时间**：第一次执行清理的时间戳  
- 🕐 **最近运行时间**：最近一次执行清理的时间戳  

**技术细节：**

- 统计数据存储在 `/config/stats.json` 中，并通过文件锁进行原子写入  
- 每次清理任务结束后都会更新统计数据，无论是否实际删除了资源  
- 时间戳是带时区的，并遵循 `PRUNEMATE_TZ` 设置  
- 界面中的日期时间显示遵循配置的 12/24 小时制  
- 统计数据在容器重启和更新后仍会保留  
- 在 Web 界面手动执行清理后，统计信息会自动刷新  

***

## 🔔 通知配置

### Gotify

[Gotify](https://gotify.net/) 是一个自托管的通知服务。

**配置步骤：**

1. 安装并运行 Gotify 服务器  
2. 在 Gotify 中创建一个新应用  
3. 复制该应用的 Token  
4. 在 PruneMate 中进行配置：  
   - **Provider（服务）**：Gotify  
   - **URL**：`https://your-gotify-server.com`  
   - **Token**：你的应用 Token  

### ntfy.sh

[ntfy.sh](https://ntfy.sh) 是一个简单的发布/订阅通知服务（支持自托管或公共实例）。

**配置步骤：**

1. 选择一个唯一的主题名称（例如 `prunemate-alerts`）  
2. 在 PruneMate 中进行配置：  
   - **Provider（服务）**：ntfy  
   - **URL**：`https://ntfy.sh`（或你的自托管实例，支持 `username:password@host` 格式）  
   - **Topic**：你选择的主题名称  
   - **Token**：（可选）用于认证的 Bearer Token  

**认证方式：**

- **Bearer Token**：推荐用于 API 访问令牌（安全性更高）  
- **URL 凭据**：使用 `https://username:password@ntfy.example.com` 格式（符合 RFC 3986）  
- **无认证**：可用于公开主题  

**订阅通知：**

- **Web**：访问 `https://ntfy.sh/your-topic`  
- **移动端**：安装 ntfy App（[Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)），订阅你的主题  
- **桌面端**：使用 ntfy 桌面应用或浏览器订阅  

### Discord

[Discord](https://discord.com/) Webhook 可以直接向你的 Discord 服务器发送通知。

**配置步骤：**

1. 打开 Discord 服务器设置  
2. 进入 **Integrations（集成）** → **Webhooks**  
3. 点击 **New Webhook** 或编辑已有 Webhook  
4. 复制 **Webhook URL**  
5. 在 PruneMate 中进行配置：  
   - **Provider（服务）**：Discord  
   - **Webhook URL**：`https://discord.com/api/webhooks/...`  

**优先级颜色：**

- **低**：绿色（信息）  
- **中**：橙色（警告）  
- **高**：红色（严重）  

### Telegram

[Telegram Bot API](https://core.telegram.org/bots) 可通过机器人发送 Telegram 通知。

**配置步骤：**

1. 打开 Telegram，搜索 **@BotFather**  
2. 发送 `/newbot` 并按提示创建新 Bot  
3. 给 Bot 取一个名字（例如 “PruneMate Notifications”）  
4. 给 Bot 取一个以 `bot` 结尾的用户名（例如 `prunemate_notif_bot`）  
5. 复制 **Bot Token**（格式类似 `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）  
6. 获取你的 **Chat ID**：  
   - **简便方法**：给 **@userinfobot** 或 **@getmyid_bot** 发送消息，获取 Chat ID  
   - **另一种方法**：给你的 Bot 发消息，然后访问 `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`，在返回 JSON 中找到 `"chat":{"id":123456789}`  
7. 在 PruneMate 中进行配置：  
   - **Provider（服务）**：Telegram  
   - **Bot Token**：从 BotFather 获取的 Token  
   - **Chat ID**：你的数值 Chat ID（或频道用户名 `@channelname`）  

**优先级行为：**

- **低**：静默通知（无声音）  
- **中/高**：正常通知（带声音）  

**进阶用法：**

- **群组**：把 Bot 拉进群组，使用群组的 Chat ID（通常以 `-` 开头）  
- **频道**：使用频道用户名（带 `@`，如 `@mychannel`）或频道的数值 ID  

***

## 🌐 多主机设置（可选）

PruneMate 可以从一个界面管理多台 Docker 主机。每次清理会在所有启用的主机上执行，并聚合结果。

### 安全第一：使用 Docker Socket Proxy

⚠️ **切勿直接暴露 Docker 套接字！** 请务必使用 [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) 限制 API 访问。

### 快速配置

**1. 在每台远程主机上部署代理：**

```yaml
services:
  dockerproxy:
    image: ghcr.io/tecnativa/docker-socket-proxy:latest
    environment:
      - CONTAINERS=1
      - IMAGES=1
      - NETWORKS=1
      - VOLUMES=1
      - BUILD=1         # 开启构建缓存清理所必需
      - POST=1          # 允许执行 prune 等写操作
    ports:
      - "2375:2375"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
```

> **⚠️ 重要：** `BUILD=1` 环境变量是启用 Docker 构建缓存清理所**必须**的。  
> 否则，构建缓存清理操作会因 403 错误而失败。

**2. 在 PruneMate 界面中添加主机：**

- 打开 **Docker Hosts** 页面  
- 点击 **Add New Host（添加新主机）**  
- 输入名称（如 “NAS”）和 URL（如 `tcp://192.168.1.50:2375`）  
- 根据需要切换每台主机的启用/禁用状态  

**3. 测试连接：**

点击 **Run now（立即运行）**，并在日志中检查是否成功连接到所有主机。

### 故障排查

- **Connection refused（连接被拒绝）**：检查代理容器是否在运行 (`docker ps`)，以及 2375 端口是否可访问  
- **Permission denied（权限拒绝）**：确认代理环境变量中设置了 `POST=1`  
- **Host skipped（主机被跳过）**：检查 URL 格式是否以 `tcp://`、`http://` 或 `https://` 开头  

***

## 🏠 Homepage 仪表盘集成

PruneMate 在 `/api/stats` 提供了自定义 API 端点，以 Homepage 的自定义小组件格式返回全时统计数据。[3][4]

<p align="center">
  <img width="400" height="400" alt="prunemate-homepage" src="https://github.com/user-attachments/assets/942169f6-bc16-4cef-8b46-3ac012fe7fec" /> 
</p>

### 配置步骤

在 Homepage 的 `services.yaml` 中添加如下配置：

```yaml
- PruneMate:
    href: http://<your-server-ip>:7676
    description: Docker Cleanup Automation
    icon: https://cdn.jsdelivr.net/gh/selfhst/icons@main/webp/prunemate.webp
    widget:
      type: customapi
      url: http://<your-server-ip>:7676/api/stats
      mappings:
        - field: pruneRuns
          label: Prune Runs
          format: number
        - field: lastRunText
          label: Last Run
        - field: imagesDeleted
          label: Images Pruned
          format: number
        - field: spaceReclaimedHuman
          label: Space Saved
```

### 可用字段

`/api/stats` 端点会返回如下字段：

| 字段 | 类型 | 描述 | Homepage 格式 |
|------|------|------|----------------|
| `pruneRuns` | number | 执行 prune 的总次数 | `number` |
| `containersDeleted` | number | 删除的容器总数 | `number` |
| `imagesDeleted` | number | 删除的镜像总数 | `number` |
| `networksDeleted` | number | 删除的网络总数 | `number` |
| `volumesDeleted` | number | 删除的卷总数 | `number` |
| `buildCacheDeleted` | number | 删除的构建缓存条目总数 | `number` |
| `spaceReclaimed` | number | 累计释放空间（字节数） | `number` |
| `spaceReclaimedHuman` | string | 人类可读的空间大小（例如 `"2.5 GB"`） | `text` |
| `lastRunText` | string | 相对时间文本（例如 `"2h ago"`） | `text` |
| `lastRunTimestamp` | number | 最近一次运行的 Unix 时间戳（秒） | `number` |
| `lastRun` | string | 最近一次清理的 ISO 时间戳 | `date` |
| `firstRun` | string | 第一次清理的 ISO 时间戳 | `date` |

### `/api/stats` 示例输出

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
  "lastRunText": "2h ago",
  "lastRunTimestamp": 1733454000,
  "lastRun": "2025-12-06T03:00:00+01:00",
  "firstRun": "2025-01-15T03:00:00+01:00"
}
```

***

## 🧠 故障排查

| 问题 | 解决方案 |
|------|----------|
| ❌ 无法访问 Web 界面 | -  检查 7676 端口是否被占用或被防火墙阻止<br>-  确认容器正在运行：`docker ps`<br>-  查看日志：`docker logs prunemate` |
| 🏗️ ARM 架构错误 | -  从 V1.3.1 开始：镜像已原生支持多架构（amd64 + arm64）<br>-  直接拉取 `anoniemerd/prunemate:latest`，会自动选择适合你的平台<br>-  不再需要在 ARM 设备上本地构建<br>-  如使用旧版本，可在 docker-compose.yaml 中使用 `build: .` |
| ⚙️ 容器无法启动 | -  使用 `docker logs prunemate` 查看启动错误<br>-  确认 Docker 套接字可访问<br>-  检查 7676 端口是否已被其他程序占用 |
| 🔒 权限不足错误 | -  确认 `/var/run/docker.sock` 存在且可访问<br>-  在 Linux 上确保 Docker 守护进程正在运行<br>-  运行 Docker 的用户需要拥有相应权限 |
| 🕐 日志/调度时间不正确 | -  正确设置 `PRUNEMATE_TZ` 环境变量<br>-  修改后重启容器：`docker-compose restart`<br>-  检查日志中的时间是否符合预期 |
| 📧 通知不工作 | -  在 Web 界面测试通知设置<br>-  确认通知服务器 URL 可访问<br>-  检查 Token/Topic 是否正确<br>-  在日志中查看错误消息 |
| 🗂️ 配置无法持久化 | -  确认已正确挂载 `./config` 卷<br>-  检查宿主机上 `./config` 目录的文件权限<br>-  确保容器对该目录有写入权限 |
| 🧹 清理任务未按计划运行 | -  检查 Web 界面中的调度配置<br>-  确认时区设置正确<br>-  查看日志中的 “Next scheduled run” 信息<br>-  确保容器持续运行 |

***

### 日志

**日志包含内容：**

- ✅ 调度器心跳（每分钟一次）  
- 📝 配置变更  
- 🧹 清理任务执行及结果  
- 📨 通知发送状态  
- ❌ 错误和警告信息  

***

## 📜 发布说明

## [V1.3.1] - 2025 年 12 月

### 新增

- 🔀 **调度启用/禁用开关**：  
  - 在“调度”区域新增 “Enable automatic schedule（启用自动调度）” 开关  
  - 允许仅运行手动清理，而不影响定时任务设置  
  - 调度器仍每分钟心跳检查，但在关闭时跳过执行  
  - 设置会持久化保存到 `config.json`，对已有安装默认保持启用  

- 🏗️ **多架构 Docker 镜像支持**：一次构建，多处运行  
  - 原生支持 amd64 与 arm64 架构  
  - 可无缝运行在 Intel/AMD、树莓派 4/5、Apple Silicon M1/M2/M3 和 ARM NAS 上  
  - 使用 Docker Buildx 进行多平台构建，便于分发  
  - ARM 系统不再需要本地构建  
  - 一份 docker-compose.yaml 即可在所有架构上工作  

### 修复

- 🏠 **带认证的 Homepage 小组件集成**：  
  - 在启用登录保护时，`/stats` 和 `/api/stats` 端点现在可正常访问  
  - 用于 Homepage 与 Dashy 显示统计信息  
  - 向下兼容：这些端点仅包含非敏感的 Docker 清理统计信息  

- 📊 **调度配置日志**：  
  - 在有效配置日志输出中新增 `schedule_enabled` 字段  
  - 日志中会完整显示所有调度相关设置，包括新加的开关  

### 变更

- 📦 **Docker Compose 默认配置**：  
  - 从本地构建改为使用预构建的多架构镜像  
  - `docker-compose.yaml` 现在默认使用 `image: anoniemerd/prunemate:latest`  
  - 拉取时自动选择正确的架构（amd64/arm64）  
  - 加快部署速度，降低初始配置复杂度  

📖 **完整变更历史请见：** [CHANGELOG.md](CHANGELOG.md)

***

## 📬 支持与交流

如果有问题或需要帮助：

- 🐛 **Bug 反馈**：在 GitHub 上 [提交 issue](https://github.com/anoniemerd/PruneMate/issues)  
- 💡 **功能建议**：在 GitHub 上 [提交 issue](https://github.com/anoniemerd/PruneMate/issues)  
- 💬 **问题与讨论**：在 GitHub 上 [发起讨论](https://github.com/anoniemerd/PruneMate/discussions)  
- ⭐ **喜欢 PruneMate？** 欢迎点个 Star！  

***

## ☕ 支持这个项目

如果你觉得 PruneMate 对你有帮助，并希望支持后续开发，可以请作者喝杯咖啡！

<p align="center">
  <a href="https://www.buymeacoffee.com/anoniemerd" target="_blank">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"/>
  </a>
</p>

你的支持能帮助作者投入更多时间来维护和改进 PruneMate！❤️

***

## 👤 作者与许可证

**作者：** Anoniemerd  
🐙 GitHub：<https://github.com/anoniemerd>  
📦 仓库：<https://github.com/anoniemerd/PruneMate>

***

## 👥 贡献者

感谢所有让 PruneMate 变得更好的贡献者！

### 贡献者

- **[@difagume](https://github.com/difagume)** —— 🔐 实现认证系统（V1.3.0）  
- **[@shollyethan](https://github.com/shollyethan)** —— 🎨 标志（Logo）重设计，并将 Logo 添加到 Self-Hosted Dashboard Icons  

### 项目维护者/所有者

- **[anoniemerd](https://github.com/anoniemerd)** —— 项目创建者与维护者  

---

### 📜 许可证 — AGPLv3

本项目基于 **GNU Affero General Public License v3.0（AGPL-3.0）** 许可证发布。

使用、修改或分发本软件时，你**必须**：

- 保留版权声明  
- 公开任何修改版本的源代码  
- 在将本软件用于提供网络服务时公开相应的源代码  
- 任何派生作品需采用 **AGPL-3.0** 许可证  

完整许可证文本见：[`LICENSE`](./LICENSE)

### ⚠️ 免责声明

**使用风险自负。** PruneMate 按“原样”提供，不附带任何形式的担保。  
作者与贡献者不对以下情况负责：

- 因清理 Docker 资源导致的数据丢失  
- 服务中断或宕机  
- 系统不稳定或性能问题  
- 任何因使用或误用本软件引起的损害  

请务必：

- ✅ 明确了解哪些资源会被删除  
- ✅ 为重要数据和配置保留备份  
- ✅ 在清理操作后检查日志  
- ✅ 从较保守的设置开始使用  

© 2025 – PruneMate 项目

---

<p align="center">
  <strong>使用 PruneMate，让你的 Docker 主机保持干净整洁！ 🐳🧹</strong>
</p>
