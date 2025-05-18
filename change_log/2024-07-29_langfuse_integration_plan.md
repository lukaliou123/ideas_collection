# Langfuse 集成计划 - 2024-07-29

本文档记录了将 Langfuse 集成到"创业产品信息收集系统"项目的计划和步骤。

## 1. 目标

集成 Langfuse 以监控、追踪和调试项目中 Langchain 和 OpenAI API 的调用，主要用于以下目的：
- 成本控制：监控 LLM API 的使用情况和相关成本。
- 调试与追踪：简化 LLM 调用链中问题的排查。
- 性能分析：监控 LLM 调用的延迟和成功率。
- 数据质量与评估：记录输入输出，用于评估和优化提示。

## 2. 集成步骤

### 2.1. 依赖与配置 (已完成)

1.  **添加 Langfuse SDK 依赖**:
    -   已将 `langfuse>=2.0.0` 添加到 `requirements.txt` 文件中。
    -   项目已包含 `python-dotenv` 用于管理环境变量。

2.  **配置 Langfuse 环境变量**:
    -   在 `app/core/config.py` 中的 `Settings` 类中添加了以下 Langfuse 相关配置项：
        -   `LANGFUSE_PUBLIC_KEY: Optional[str] = None`
        -   `LANGFUSE_SECRET_KEY: Optional[str] = None`
        -   `LANGFUSE_HOST: Optional[str] = "https://cloud.langfuse.com"`
    -   这些配置将从 `.env` 文件中读取。

3.  **更新项目文档 (`README.md`)**:
    -   已在 `README.md` 的"技术栈"部分添加了 Langfuse。
    -   已在 `README.md` 的"如何开始"/环境变量配置部分添加了 `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, 和 `LANGFUSE_HOST` 的说明。
    -   提供的密钥：
        -   Secret Key: `sk-lf-ab7ecee8-0f87-4018-b3a5-fdbfb46d1dfa`
        -   Public Key: `pk-lf-49996fcc-b4d5-42da-9114-1c869a5668d3`
        -   Host: `https://cloud.langfuse.com`
        *(注意: 密钥已由用户提供，并计划通过环境变量使用，不会硬编码到代码中)*

### 2.2. Langfuse SDK 初始化与集成 (待进行)

1.  **全局 Langfuse 客户端初始化 (可选但推荐)**:
    -   考虑在应用启动时（例如 `main.py` 或 `app/core/__init__.py`）初始化一个全局的 `Langfuse` 客户端实例。
    -   这将允许在需要手动创建 trace 或 span 的地方复用此客户端。
    -   `langfuse_client = Langfuse(public_key=settings.LANGFUSE_PUBLIC_KEY, secret_key=settings.LANGFUSE_SECRET_KEY, host=settings.LANGFUSE_HOST)`
    -   **注意**: 确保在 `settings.LANGFUSE_PUBLIC_KEY` 和 `settings.LANGFUSE_SECRET_KEY` 有值时才初始化。

2.  **集成 `LangfuseCallbackHandler` 到 Langchain 服务**:
    -   **主要目标文件**: `app/services/ai_service_langchain.py`。
    -   **次要目标文件 (如果直接使用 Langchain)**: `app/services/ai_service.py` (初步检查显示此文件不直接使用 Langchain，而是原始 OpenAI API 调用，后续可以考虑为其添加手动追踪)。

    -   **具体步骤 for `ai_service_langchain.py`**:
        -   **导入**: `from langfuse.callback import CallbackHandler as LangfuseCallbackHandler` (或最新版 Langfuse SDK 的相应导入路径) 和 `from app.core.config import settings`。
        -   **创建 Handler 实例**: 在每个需要追踪的 Langchain 调用（LLM 或 Chain 的 `invoke`, `ainvoke`, `stream`, `run` 等方法）之前或在其所属的类/方法中创建 `LangfuseCallbackHandler` 实例。
            ```python
            # 伪代码
            if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
                langfuse_handler = LangfuseCallbackHandler(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST,
                    # 可选参数，用于丰富追踪信息
                    # session_id="some_session_identifier", # 例如，基于请求或任务的唯一ID
                    user_id=post_original_id, # 例如，被处理内容的ID
                    trace_name="specific_langchain_operation", # 例如 "product_analysis_chain"
                    tags=["langchain", "product_analysis", "hackernews"] # 相关标签
                )
                callbacks_list = [langfuse_handler]
            else:
                callbacks_list = [] # 如果未配置Langfuse，则不添加回调

            # Langchain 调用
            # result = await some_chain.ainvoke(input_data, config={"callbacks": callbacks_list})
            # 或
            # result = await llm.ainvoke(prompt_data, callbacks=callbacks_list)
            ```
        -   **传递 Handler**: 将创建的 `langfuse_handler` 实例通过 `callbacks` 参数（用于 LLM 调用）或 `config={"callbacks": ...}`（用于 Runnable/Chain 调用）传递给 Langchain 的相关方法。
        -   **动态元数据**: 根据上下文动态设置 `user_id` (例如，当前处理的帖子ID), `trace_name` (例如，执行的具体链或操作名称), 和 `tags`，以便在 Langfuse UI 中更好地筛选和理解追踪。

3.  **处理图像生成 (DALL-E)**:
    -   `ai_service_langchain.py` 中包含直接调用 DALL-E API (`httpx.post`) 的逻辑。
    -   这些非 Langchain 的 LLM 调用需要手动使用 Langfuse SDK 的 `langfuse.generation()` 方法进行追踪，将其包裹在一个 `langfuse.trace()` 中。
        ```python
        # 伪代码，用于追踪 generate_image 中的 httpx 调用
        # from langfuse import Langfuse # 假设 langfuse_client 已全局初始化

        # if langfuse_client: # 检查客户端是否已初始化
        #     trace = langfuse_client.trace(
        #         name="dall-e-image-generation",
        #         user_id=str(product_id),
        #         metadata={"product_name": product.name},
        #         tags=["dall-e", "image_generation"]
        #     )
        #     generation = trace.generation(
        #         name="dall-e-api-call",
        #         model="dall-e-2", # 或实际使用的模型
        #         model_parameters={"size": "512x512", "n": 1},
        #         prompt=prompt, # 发送给DALL-E的提示
        #         # usage={...} # 如果可以获取token使用量
        #     )

        # # ... 执行 httpx.post 调用 ...

        # if langfuse_client and generation:
        #     if success:
        #         generation.end(output={"image_url": dalle_image_url})
        #     else:
        #         generation.end(level='ERROR', status_message=str(error_details))
        ```

## 3. 验证

-   在本地开发环境中配置好 Langfuse 环境变量并运行应用。
-   执行触发 Langchain AI 服务（如产品分析、标签生成）和图像生成的操作。
-   登录 Langfuse UI (例如 `https://cloud.langfuse.com`)，检查是否能看到相应的追踪 (Traces) 和生成 (Generations) 数据。
-   验证追踪数据中是否包含预期的元数据、输入、输出和标签。

## 4. 注意事项

-   **错误处理**: 确保 Langfuse 的集成代码包含适当的错误处理，例如，如果 Langfuse SDK 初始化失败或追踪调用失败，不应中断核心应用逻辑。
-   **异步兼容性**: 由于项目使用 `async/await`，确保 Langfuse 的使用方式（特别是 `LangfuseCallbackHandler` 和手动追踪）与异步代码兼容。Langfuse SDK 通常支持异步操作。
-   **敏感数据**: 确保在发送到 Langfuse 的数据中没有意外包含过多的敏感信息。虽然 Langfuse 用于调试和监控，但仍需注意数据隐私。
-   **性能影响**: 监控 Langfuse 回调和追踪对应用性能的潜在影响，尤其是在高并发场景下。Langfuse 通常设计为轻量级，但仍需关注。

## 5. 未来考虑 (针对 `ai_service.py`)

-   `app/services/ai_service.py` 文件直接使用 `httpx` 调用 OpenAI Chat API。如果需要对此进行监控，可以采用与上述 DALL-E 调用类似的手动追踪方法，使用 `langfuse.trace()` 和 `langfuse.generation()`。 

## 6. API 密钥安全性

-   **最佳实践**: 所有API密钥（OpenAI和Langfuse）都应从环境变量获取，而不是硬编码在代码库中。
-   **配置方法**:
    -   在本地开发环境中，使用 `.env` 文件存储密钥，确保该文件在 `.gitignore` 中被忽略。
    -   提供一个不包含实际密钥的 `.env.example` 文件，作为配置模板。
    -   在生产环境中，通过环境变量、密钥管理服务或容器编排平台的密钥管理功能提供这些密钥。
-   **安全警告**:
    -   避免将API密钥提交到代码仓库中，即使是在配置文件或注释中。
    -   GitHub和其他代码托管平台有密钥扫描功能，会阻止包含API密钥的提交。
    -   如果密钥被意外提交，应立即在相应服务中轮换（更新）密钥。
  
-   **2024-07-29更新**: 已将硬编码在 `app/core/config.py` 中的API密钥移除，改为从环境变量读取，并更新了 `.env.example` 文件作为配置指南。 