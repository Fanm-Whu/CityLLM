# CityLLM

CityLLM 是一个基于大语言模型（LLM）驱动的城市时空动态模拟与可视化系统。用户通过自然语言与系统交互，系统智能解析意图、调度地理模拟算法，并将结果以 GIS 图层形式呈现在地图上。

## 系统架构

系统采用前后端分离架构，整体分为**客户端**、**服务器端**和**多源数据**三层：

- **客户端**：基于 Vue 3 的交互界面，提供自然语言对话与栅格影像可视化能力。
- **服务器端**：核心推理引擎，由地理工具、智能体引擎和城市模拟器组成。
- **多源数据**：通过 RAG 机制为智能体引擎提供土地、人口、经济及各类驱动因子的数据支撑。

## 后端核心流程

后端采用 **Plan-and-Solve** 架构，由主 AgentLoop 统一规划并调度各工具完成复杂任务。

### 1. 主 AgentLoop（Plan-and-Solve）

主 AgentLoop 是系统的中央调度器，负责接收用户查询、制定执行计划，并循环调用各类工具完成目标：

1. **计划（Plan）**：分析用户意图，生成可执行的任务计划（Task Plan）。
2. **执行（Solve）**：按顺序或依赖关系调用相应工具，获取中间结果。
3. **反思（Reflect）**：根据工具返回结果，判断是否需要调整计划或补充执行。
4. **输出（Answer）**：汇总各工具执行结果，生成最终响应并返回前端。

### 2. 工具层（Tools）

原有的独立 Agent 被重构为可复用的工具（Tool），每个工具封装单一原子能力，供 AgentLoop 按需调用：

| 工具 | 职责 |
|------|------|
| `TaskDecomposer` | 将复杂用户查询拆解为若干可并行的子任务 |
| `InterParser` | 解析子任务中的关键参数（目标城市、年份、情景模式等） |
| `DataDemand` | 分析当前任务所需的数据集，触发 RAG 数据检索 |
| `AlgorithmExe` | 调度地理模拟算法（土地/人口/GDP），执行计算并输出栅格结果 |
| `GeoProcessor` | 提供裁剪、标准化、投影等地理数据预处理能力 |

### 3. Skill 封装

系统将原 **ChainAgent** 的链式调用流程（TaskDecomposer → InterParser → DataDemand → AlgorithmExe）封装为一个可复用的 **Skill**：

```
ChainAgent Skill:
  输入: 用户自然语言查询
  输出: AlgorithmExeResult 列表
  内部流程:
    1. TaskDecomposer 分解任务 → 子任务列表
    2. 对每个子任务:
       a. InterParser 提取时空参数
       b. DataDemand 检索所需数据
       c. AlgorithmExe 执行模拟算法
    3. 聚合结果并返回
```

主 AgentLoop 可以直接调用该 Skill 完成标准模拟流程，也可以在复杂场景下绕过 Skill，直接编排底层工具实现更灵活的策略。

### 4. 请求处理时序

```
用户查询
   │
   ▼
┌─────────────────┐
│  AgentLoop      │  ← Plan-and-Solve 主循环
│  (计划/执行/反思) │
└─────────────────┘
   │
   ├──▶ TaskDecomposer ──▶ 子任务列表
   │
   ├──▶ InterParser ─────▶ 结构化参数
   │
   ├──▶ DataDemand ──────▶ RAG 数据检索
   │         │
   │         ▼
   │    多源数据（土地/人口/经济/因子）
   │
   └──▶ AlgorithmExe ────▶ 调用模拟器
                │
                ▼
         ┌─────────────┐
         │  LandSim    │  ← XGBoost + 改进 CA
         │  PopSim     │
         │  GDPSim     │
         └─────────────┘
                │
                ▼
         GeoTIFF 栅格结果
                │
                ▼
            最终响应
                │
                ▼
         前端地图可视化
```

## 目录结构

```
CityLLM/
├── frontend/                 # Vue 3 + Vite 前端
│   └── src/
│       ├── components/       # ChatPanel、MapView、DataLayerPanel
│       └── api/              # 后端 API 接口封装
│
└── backend/                  # Flask 后端
    ├── main.py               # Flask 服务入口
    ├── src/
    │   ├── core/
    │   │   └── agent_loop.py     # Plan-and-Solve 主循环
    │   ├── tools/                # 原子工具层
    │   │   ├── task_decomposer.py
    │   │   ├── inter_parser.py
    │   │   ├── data_demand.py
    │   │   ├── algorithm_exe.py
    │   │   └── geo_processor.py
    │   ├── skills/               # 可复用技能封装
    │   │   └── chain_agent.py    # 原 ChainAgent 流程
    │   └── algorithms/           # 地理模拟算法
    │       ├── LandSimulator.py
    │       ├── PopulationSimulator.py
    │       ├── GDPSimulator.py
    │       └── ...
    └── tests/
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3.5、Vite 5、OpenLayers 10、Element Plus 2 |
| 后端 | Flask 3、Flask-CORS |
| LLM | LangChain、DeepSeek API |
| 数据 | Pandas、NumPy、Rasterio、GDAL |
| 算法 | XGBoost、Scikit-learn、Statsmodels |

## 快速启动

```bash
# 后端
cd backend
pip install -r ../requirements.txt
python main.py          # 端口 5000

# 前端
cd frontend
npm install
npm run dev             # 端口 3000
```

访问 http://localhost:3000 使用系统。运行前需在 `backend/.env` 中配置 `DEEPSEEK_API_KEY`。

> **注意**：`data/` 目录已加入 `.gitignore`，GeoTIFF 数据需根据研究区域自行准备。GDAL 需单独安装（Windows 推荐 [OSGeo4W](https://trac.osgeo.org/osgeo4w/)）。
