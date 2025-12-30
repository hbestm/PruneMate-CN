# PruneMate 架构与设计

本文档提供了 PruneMate 内部架构和工作流程的详细可视化说明。[1]

## 系统架构

```mermaid
flowchart TD
    Start([PruneMate]) --> Auth{认证<br/>已启用？}
    Auth -->|No| WebUI[Web 界面<br/>端口 8080]
    Auth -->|Yes| Login[登录页面<br/>会话认证]
    Login -->|Authenticated| WebUI
    Login -->|API Client| BasicAuth[Basic 认证<br/>回退方式]
    BasicAuth -->|Valid| WebUI
    
    Start --> Scheduler[调度器<br/>每分钟运行一次]
    Start --> API[API 端点<br/>/stats, /api/stats<br/>无需认证]
    
    WebUI --> |Configure| Config[(config.json<br/>• 启用调度<br/>• 运行频率<br/>• 清理选项<br/>• 通知设置<br/>• 远程主机)]
    WebUI --> |View Stats| StatsUI[显示 stats.json<br/>全时统计]
    WebUI --> |Manual/Preview| Manual[手动触发]
    API --> |Homepage Widget| StatsUI
    
    Scheduler --> CheckSchedule{调度<br/>已启用？}
    CheckSchedule --> |No| Scheduler
    CheckSchedule --> |Yes| CheckTime{已到<br/>计划时间？}
    CheckTime --> |No| Scheduler
    CheckTime --> |Yes| LoadConfig[加载配置]
    
    Manual --> |Preview| Preview[获取预览<br/>按主机拆分<br/>显示资源列表]
    Preview --> |User confirms| LoadConfig
    
    LoadConfig --> Lock{是否已在<br/>运行中？}
    Lock --> |Yes| Skip[跳过]
    Lock --> |No| CheckHosts{存在<br/>远程主机？}
    
    CheckHosts --> |Yes| Remote[本地 + 远程主机<br/>经由 docker-socket-proxy<br/>tcp://host:2375]
    CheckHosts --> |No| Local[仅本地主机<br/>unix:///var/run/docker.sock]
    
    Remote --> CheckOptions
    Local --> CheckOptions
    
    CheckOptions{检查已启用的<br/>清理选项}
    CheckOptions --> |Containers ✓| PruneC[清理容器<br/>已停止/已退出]
    CheckOptions --> |Images ✓| PruneI[清理镜像<br/>所有未使用]
    CheckOptions --> |Networks ✓| PruneN[清理网络<br/>未使用]
    CheckOptions --> |Volumes ✓| PruneV[清理卷<br/>所有未使用 + 具名卷]
    CheckOptions --> |Build Cache ✓| PruneB[清理构建缓存<br/>Docker 构建缓存]
    
    PruneC --> Aggregate
    PruneI --> Aggregate
    PruneN --> Aggregate
    PruneV --> Aggregate
    PruneB --> Aggregate
    
    Aggregate[汇总结果<br/>空间 + 数量] --> Stats[更新 stats.json<br/>• 总运行次数<br/>• 删除的资源<br/>• 回收的空间<br/>• 时间戳]
    
    Stats --> Notify{通知<br/>已启用？}
    
    Notify --> |Yes + Changes| Send[发送通知<br/>Gotify / ntfy / Discord / Telegram<br/>按主机拆分结果]
    Notify --> |No or No changes| Log[写入<br/>prunemate.log]
    Send --> Log
    Log --> Done[完成]
    
    style Start fill:#4a90e2
    style WebUI fill:#50c878
    style Scheduler fill:#9b59b6
    style Config fill:#f39c12
    style CheckOptions fill:#e74c3c
    style Stats fill:#16a085
    style Send fill:#3498db
    style Preview fill:#e67e22
    style API fill:#2ecc71
    style Remote fill:#8e44ad
    style CheckSchedule fill:#c0392b

```

## 组件说明

### 核心组件

- **Web UI（端口 8080）**：基于 Flask 的 Web 界面，用于配置和手动操作。[1]
- **调度器（Scheduler）**：APScheduler 每分钟运行一次，用来检查是否启用了调度以及是否到达执行清理的时间。  
  - 可以通过界面中的 “Enable automatic schedule（启用自动调度）” 开关禁用  
  - 遵守配置的频率（每天、每周、每月）  
- **API 端点**：用于外部集成的 REST API。  
  - `/stats` 与 `/api/stats`：公开端点（无需认证），用于 Homepage、Dashy 等小组件  
  - 返回全时统计和最近一次运行的信息  

### 配置与状态

- **config.json**：持久化配置，包括：  
  - `schedule_enabled`：是否启用自动调度的布尔开关  
  - 调度频率（每天/每周/每月）、时间和日期设置  
  - 清理选项（容器、镜像、网络、卷、构建缓存）  
  - 通知服务提供方和相关设置  
  - 远程 Docker 主机列表  
- **stats.json**：累积的全时统计（释放空间、删除资源数量、时间戳）。  
- **prunemate.lock**：用于防止并发执行清理的文件锁。  
- **last_run_key**：记录最近一次成功的定时运行，用于防止重复执行。  

### 清理操作

- **容器（Containers）**：删除已停止/已退出/已死亡的容器。  
- **镜像（Images）**：删除所有未使用镜像（不仅仅是悬空镜像），使用 `filters={"dangling": False}`。  
- **网络（Networks）**：删除未使用的网络（不包括默认的 bridge/host/none）。  
- **卷（Volumes）**：删除所有未使用卷，包括具名卷，使用 `filters={"all": True}`。  
- **构建缓存（Build Cache）**：删除 Docker 构建缓存（通常可以回收大量空间，如 10GB+）。  

### 多主机支持

- **本地主机**：通过 `unix:///var/run/docker.sock` 直接访问。  
- **远程主机**：通过 docker-socket-proxy 使用 `tcp://host:2375` 安全访问。  
- **按主机统计**：对每个主机分别统计结果和错误信息。  

### 通知流程

- **通知服务提供方**：Gotify（自托管）、ntfy.sh（发布/订阅）、Discord（Webhook）、Telegram（Bot API）。  
- **认证方式**：  
  - Gotify：应用 Token  
  - ntfy：Bearer Token、Basic Auth 或无认证  
  - Discord：Webhook URL  
  - Telegram：Bot Token + Chat ID  
- **优先级系统**：基于文本的优先级（Low/Medium/High），由各服务按自己的方式处理：  
  - Gotify：数值映射（Low=2，Medium=5，High=8）  
  - ntfy：数值映射（Low=2，Medium=3，High=5）  
  - Discord：颜色映射（Low=绿色，Medium=橙色，High=红色）  
  - Telegram：通知声音（Low=静音，Medium/High=有声音）  
- **智能通知**：可选 “仅在有变化时通知” 模式以减少打扰。  
- **按主机拆分结果**：在多主机场景下，会展示每个 Docker 主机的详细结果。  

## 工作流程说明

1. **触发方式**：  
   - 定时触发：调度器按分钟检查当前时间是否与配置的计划时间匹配。  
   - 手动触发：用户在界面中点击 “Run now（立即运行）”，可以先预览再执行。  

2. **预览模式（仅手动）**：  
   - 向每个 Docker 主机查询未使用资源。  
   - 显示将要删除的详细列表。  
   - 只有用户确认后才会真正执行。  
   - 在预览和设置页面之间切换时，复选框状态会自动保存。  

3. **执行阶段**：  
   - 获取文件锁，防止并发运行。  
   - 从磁盘加载最新配置。  
   - 连接本地和/或远程 Docker 主机。  
   - 对每个主机执行已启用的清理操作。  
   - 聚合所有主机的执行结果。  

4. **执行后处理**：  
   - 更新 `stats.json` 中的累积统计数据。  
   - 如果启用了通知（并且符合 “仅在有变化时通知” 的条件），则发送通知。  
   - 使用带时区的时间戳写入详细日志。  
   - 释放文件锁。  

## 文件结构

```text
/config/
├── config.json          # 用户配置（持久化）
├── stats.json           # 全时统计（累积数据）
├── prunemate.lock       # 防止并发运行
└── last_run_key         # 记录最近一次成功运行

/var/log/
└── prunemate.log        # 应用日志（滚动，最大约 5MB）
```

***

更多信息请参见主文档 [README.md](README.md)。

[1](https://github.com/anoniemerd/PruneMate)
