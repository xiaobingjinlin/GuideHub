# 方案：LangChain 示例 · 阿里云模型开通清单

对照 [阿里云百炼 / 通义千问官方文档](https://help.aliyun.com/zh/model-studio/models) 整理，方便你在控制台按场景开通模型权限。  
你本地已有 `QWEN_API_KEY`、`QWEN_BASE_URL`（OpenAI 兼容模式，北京 MaaS），下列模型 ID 以**华北2（北京）**常见可用名为准；控制台若显示更新名称，以控制台为准。

对应《基本信息》里三个菜单：

| 菜单 | 能力 | 推荐开通（首选） | 备选 / 说明 |
| --- | --- | --- | --- |
| 文本对话机器人 | 纯文本多轮对话 | **`qwen-plus`** | 更省钱：`qwen-flash`；更新一代：`qwen3.5-plus` / `qwen3.6-plus` |
| 多模态对话机器人 | 图片理解 + 语音理解（识别） | **`qwen3.5-omni-flash`** | 只要看图：`qwen3-vl-flash` / `qwen3-vl-plus`；要更强：`qwen3.5-omni-plus` |
| 语音对话机器人 | 语音进、语音出（对话） | **`qwen3.5-omni-flash-realtime`** | 非实时（上传音频再回）：`qwen3.5-omni-flash`；更强实时：`qwen3.5-omni-plus-realtime` |

---

## 1. 文本对话机器人 → `qwen-plus`

**场景**：Gradio + LLM + 短期记忆（内存）+ 长期记忆（SQLite），纯文字问答。

**推荐模型 ID：`qwen-plus`**

- 官方文档与 OpenAI 兼容示例长期以 `qwen-plus` 为例，和现有 `llm_util.py` 默认一致，最省事。
- 适合教程级文本对话：效果稳、接入简单（Chat Completions）。

**可选**

| 模型 ID | 何时选 |
| --- | --- |
| `qwen-flash` | 更便宜、延迟更低，教程演示够用 |
| `qwen3.5-plus` / `qwen3.6-plus` | 想用更新一代文本能力（控制台有额度再开） |

**开通动作**：百炼控制台 → 模型广场 / 模型列表 → 搜索 `qwen-plus`（建议同时开 `qwen-flash` 备用）→ 开通/领取免费额度。

**参考文档**

- [模型大全](https://help.aliyun.com/zh/model-studio/models)
- [OpenAI 兼容 / Responses](https://help.aliyun.com/zh/model-studio/compatibility-with-openai-responses-api)

---

## 2. 多模态对话机器人（语音识别 + 图片识别）→ `qwen3.5-omni-flash`

**场景**：同一对话里能传图片、传音频，让模型「看懂图 / 听懂话」，再文本回复（教程演示够用）。

**推荐模型 ID：`qwen3.5-omni-flash`（HTTP，非实时）**

依据官方 [Qwen-Omni](https://help.aliyun.com/zh/model-studio/qwen-omni) / [全模态](https://help.aliyun.com/zh/model-studio/omni/)：

- 输入：文本、音频、图片、视频  
- 输出：文本（也可配置语音输出）  
- 适合「上传一张图 / 一段语音 → 理解并回答」，不必上 WebSocket 实时链路  

**为什么不主推旧版 Audio / 单独只开 VL**

| 方案 | 结论 |
| --- | --- |
| `qwen-audio-turbo` 等 Audio | 官方写明**仅免费体验、用完不可付费**，生产/长期教程不推荐，建议迁 Omni |
| 只开 `qwen3-vl-*` | **图片很合适**，但不覆盖语音理解；多模态菜单若要「语音+图片」，Omni 一次开齐更省事 |
| `qwen3-vl-flash` / `qwen3-vl-plus` | 若你想把「看图」和「听语音」拆成两个模型，可额外开通 VL，作对照或降本 |

**可选加强**

| 模型 ID | 何时选 |
| --- | --- |
| `qwen3.5-omni-plus` | 效果优先 |
| `qwen3-vl-flash` | 只要图片 OCR / 看图问答，成本更可控 |

**开通动作**：搜索并开通 `qwen3.5-omni-flash`；可选再开 `qwen3-vl-flash`。

**参考文档**

- [Qwen-Omni](https://help.aliyun.com/zh/model-studio/qwen-omni)
- [视觉理解](https://help.aliyun.com/zh/model-studio/vision)
- [千问 Audio（不推荐生产）](https://help.aliyun.com/zh/model-studio/audio-language-model)

---

## 3. 语音对话机器人 → `qwen3.5-omni-flash-realtime`

**场景**：对着麦克风说话，模型实时听、实时回（语音对话），接近「电话客服 / 语音助手」。

**推荐模型 ID：`qwen3.5-omni-flash-realtime`**

依据官方 [全模态](https://help.aliyun.com/zh/model-studio/omni/) / Realtime 说明：

- 走 **WebSocket** 实时多模态交互（不是普通一轮 Chat Completions）  
- 输入：文本、音频、图片等  
- 教程成本敏感时用 **flash-realtime**；要更好音质/效果再上 **plus-realtime**

**与示例二的区别**

| | 示例二 多模态 | 示例三 语音对话 |
| --- | --- | --- |
| 交互 | 上传文件 / 点发送 | 持续收音、边说边答 |
| API | HTTP（Omni） | WebSocket Realtime |
| 模型 | `qwen3.5-omni-flash` | `qwen3.5-omni-flash-realtime` |

**可选**

| 模型 ID | 何时选 |
| --- | --- |
| `qwen3.5-omni-plus-realtime` | 实时效果更好 |
| `qwen3.5-omni-flash`（HTTP） | 先做「录音上传 → 语音回复」，降低实时联调难度 |

**开通动作**：搜索并开通 `qwen3.5-omni-flash-realtime`（建议与示例二的 `qwen3.5-omni-flash` 一起开）。

**参考文档**

- [全模态模型列表](https://help.aliyun.com/zh/model-studio/omni/)
- [实时多模态交互（WebSocket）](https://help.aliyun.com/zh/model-studio/multimodal-interaction-protocol)

---

## 建议你最少开通的清单（打勾用）

按 GuideHub 三个示例，建议至少开通：

1. [ ] **`qwen-plus`**（文本对话；或同时开 `qwen-flash`）  
2. [ ] **`qwen3.5-omni-flash`**（多模态：图 + 语音理解）  
3. [ ] **`qwen3.5-omni-flash-realtime`**（语音实时对话）  

可选加开：

4. [ ] **`qwen3-vl-flash`**（只要强化看图、或与 Omni 对照）  
5. [ ] **`qwen3.5-omni-plus` / `…-plus-realtime`**（效果不够再升级）

---

## 与本项目环境变量的对应关系

当前 `backend/app/llm_util.py`：

| 环境变量 | 用途 |
| --- | --- |
| `QWEN_API_KEY` | 百炼 / MaaS API Key |
| `QWEN_BASE_URL` | OpenAI 兼容根地址（你已配北京 compatible-mode） |
| `QWEN_MODEL` | 默认文本模型，建议先保持 `qwen-plus` |

后续实现时建议扩展为按场景区分，例如：

- `QWEN_MODEL_TEXT=qwen-plus`  
- `QWEN_MODEL_MULTIMODAL=qwen3.5-omni-flash`  
- `QWEN_MODEL_VOICE=qwen3.5-omni-flash-realtime`  

（Realtime 往往还要单独的 WebSocket 地址，不完全等同于 `QWEN_BASE_URL` 的 HTTP Chat。）

---

## 注意

1. **地域与 Key**：北京与新加坡等地域的 Key / Endpoint 可能不同，你当前是北京 MaaS，请在**同一地域**控制台开通模型。  
2. **权限 ≠ Key**：Key 配好了，模型未开通仍会报无权限 / 无额度。  
3. **名称以控制台为准**：百炼会迭代型号（如 3.5 / 3.6 / 3.7），若搜索不到上表 ID，用同系列最新「商业版 / Flash」即可，并回写本文档。  
4. **成本**：Realtime、Omni-Plus、长音频/多图会明显更贵；教程优先 Flash。

开通完成后，把控制台里实际可用的三个模型 ID 发我，我可以据此改 `llm_util` 并开始接示例一。
