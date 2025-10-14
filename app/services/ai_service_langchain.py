"""
AI服务模块 - 使用LangChain框架实现与OpenAI API的交互
该模块提供产品分析和图像生成功能
"""
import time
import asyncio
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union, Tuple
import os
import uuid

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func
import backoff
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

# Langfuse 是可选依赖，如果导入失败不影响应用运行
try:
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    try:
        # 尝试旧版本的导入路径
        from langfuse import Langfuse
        from langfuse.callback import CallbackHandler as LangfuseCallbackHandler
        LANGFUSE_AVAILABLE = True
    except ImportError:
        LANGFUSE_AVAILABLE = False
        Langfuse = None
        LangfuseCallbackHandler = None
        logger.warning("Langfuse not available. AI monitoring will be disabled.")

from app.core.config import settings
from app.utils.logger import logger
from app.models.products import Product

class AIImageGenerationRecord(BaseModel):
    """图像生成记录，用于跟踪每日生成次数"""
    date: date
    count: int = 0

class AIAnalysisResult(BaseModel):
    """AI分析结果数据模型"""
    name: Optional[str] = Field(None, description="产品名称")
    description: Optional[str] = Field(None, description="产品简要描述")
    problem_solved: Optional[str] = Field(None, description="产品解决的问题")
    target_audience: Optional[str] = Field(None, description="目标受众")
    competitive_advantage: Optional[str] = Field(None, description="竞争优势")
    potential_competitors: Optional[str] = Field(None, description="潜在竞争对手")
    business_model: Optional[str] = Field(None, description="商业模式")
    tags: List[str] = Field(default_factory=list, description="相关标签（最多5个）")

class LangChainAIService:
    """使用LangChain框架的AI服务类，提供产品分析和图像生成功能"""
    
    # 图像生成每日限制
    IMAGE_GENERATION_DAILY_LIMIT = 3
    
    # 图像生成记录，用于跟踪每日生成次数
    # 格式: {日期字符串: 当日生成次数}
    image_generation_records: Dict[str, int] = {}
    
    def __init__(self, db: Optional[Session] = None):
        """
        初始化LangChain AI服务
        
        Args:
            db: 数据库会话，用于存储分析结果和图像
        """
        self.db = db
        self.langfuse_client = None # Langfuse client for manual tracing
        
        # 验证API密钥是否已设置
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
            logger.warning("OpenAI API密钥未设置，LangChain AI功能将不可用")
            self.is_available = False
        else:
            self.is_available = True
            
            # 初始化LangChain LLM
            # GPT-5模型不支持temperature参数，需要根据模型类型决定
            if settings.OPENAI_MODEL and settings.OPENAI_MODEL.startswith("gpt-5"):
                # GPT-5模型不支持temperature参数
                self.llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL or "gpt-4.1-nano"
                )
            else:
                # 其他模型支持temperature参数
                self.llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL or "gpt-4.1-nano",
                    temperature=0.2
                )
            
            # 初始化各种Chain
            self._init_chains()

            # 初始化 Langfuse 客户端 (用于手动追踪)
            if LANGFUSE_AVAILABLE and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
                try:
                    self.langfuse_client = Langfuse(
                        public_key=settings.LANGFUSE_PUBLIC_KEY,
                        secret_key=settings.LANGFUSE_SECRET_KEY,
                        host=settings.LANGFUSE_HOST,
                        # release="your_app_version", # 可选: 应用版本
                        debug=settings.DEBUG # 可选: 调试模式
                    )
                    logger.info("Langfuse client initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize Langfuse client: {e}")
                    self.langfuse_client = None # Ensure it's None if init fails
            else:
                if not LANGFUSE_AVAILABLE:
                    logger.info("Langfuse package not available. Manual tracing will be disabled.")
                else:
                    logger.info("Langfuse public/secret keys not configured. Manual tracing will be disabled.")
    
    def _get_langfuse_callback_handler(self, trace_name: str, user_id: Optional[str] = None, tags: Optional[List[str]] = None, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[LangfuseCallbackHandler]:
        """辅助函数，用于创建LangfuseCallbackHandler实例"""
        if not LANGFUSE_AVAILABLE:
            return None
            
        if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
            try:
                # 直接使用密钥和主机名创建 Handler，让其内部管理SDK实例
                return LangfuseCallbackHandler(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST,
                    trace_name=trace_name,
                    user_id=user_id,
                    session_id=session_id or str(uuid.uuid4()), # Ensure a session_id
                    tags=tags or ["langchain_service"],
                    metadata=metadata
                    # debug=settings.DEBUG # 考虑是否需要，根据LangfuseCallbackHandler是否支持
                )
            except Exception as e:
                logger.error(f"Failed to create LangfuseCallbackHandler for trace '{trace_name}': {e}")
                return None
        else:
            return None

    def _init_chains(self):
        """初始化各种LangChain链"""
        self._init_product_analysis_chain()
        self._init_image_generation_chain()
    
    def _init_product_analysis_chain(self):
        """初始化产品分析链"""
        # 系统提示模板
        system_template = """
        你是一个专业的创业产品分析师，负责从互联网上的帖子中提取产品信息。
        你的任务是仔细分析帖子内容，提取关于产品的以下信息：
        1. 产品名称
        2. 产品描述
        3. 解决的问题
        4. 目标受众
        5. 竞争优势
        6. 潜在竞争对手
        7. 商业模式
        8. 相关标签（最多5个）
        
        如果某项信息不存在，请将该字段设为null。请确保你的分析客观、精确，并基于提供的信息。
        你必须以指定的JSON格式返回结果。
        """
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        
        # 人类提示模板
        human_template = """
        请分析以下帖子中的产品信息：
        
        标题: {title}
        
        内容: {content}
        
        URL: {url}
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        
        # 创建聊天提示模板
        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt, 
            human_message_prompt
        ])
        
        # 创建结构化输出链
        self.product_analysis_chain = (
            chat_prompt 
            | self.llm.with_structured_output(AIAnalysisResult)
        )
    
    def _init_image_generation_chain(self):
        """初始化图像生成提示词链"""
        # 创建提示模板
        template = """
        为以下产品创建一个简洁、视觉化的图像提示词，用于AI图像生成:
        
        产品名称: {product_name}
        产品描述: {product_description}
        解决的问题: {problem_solved}
        
        提示词应该:
        1. 简洁明了，不超过50个词
        2. 突出产品的核心功能和视觉特点
        3. 描述一个能代表产品价值和使用场景的图像
        4. 不要使用文字或标签
        5. 适合创建一个专业、现代的产品概念图
        
        仅返回提示词本身，不要包含解释或其他内容。
        """
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template(template)
        
        # 创建链
        self.image_prompt_chain = prompt | self.llm | StrOutputParser()
    
    async def analyze_product(self, title: str, content: str, url: str = "", post_id: Optional[str] = None) -> Optional[AIAnalysisResult]:
        """
        分析帖子内容，提取产品信息
        
        Args:
            title: 帖子标题
            content: 帖子内容
            url: 帖子URL（可选）
            post_id: 帖子的原始ID (用于Langfuse user_id)
            
        Returns:
            产品分析结果对象
        """
        if not self.is_available:
            logger.warning("LangChain AI服务不可用，无法执行产品分析")
            return None
        
        callbacks_list = []
        langfuse_handler = self._get_langfuse_callback_handler(
            trace_name="product_analysis_chain",
            user_id=post_id or title, # Use post_id if available, else title
            tags=["product_analysis", "langchain"],
            metadata={"title": title, "url": url, "content_length": len(content)}
        )
        if langfuse_handler:
            callbacks_list.append(langfuse_handler)
            
        try:
            # 使用产品分析链分析内容
            result = await self.product_analysis_chain.ainvoke({
                "title": title,
                "content": content,
                "url": url
            }, config={"callbacks": callbacks_list})
            
            # 确保处理"未提及"的情况
            for field in result.model_fields:
                if getattr(result, field) == "未提及":
                    setattr(result, field, None)
            
            return result
            
        except Exception as e:
            logger.error(f"产品分析过程中出错: {e}")
            return None
    
    async def generate_tags(self, text: str, max_tags: int = 5, context_id: Optional[str] = None) -> List[str]:
        """
        生成与文本相关的标签
        
        Args:
            text: 输入文本
            max_tags: 最大标签数量
            context_id: 相关上下文ID (如帖子ID，用于Langfuse user_id)
            
        Returns:
            标签列表
        """
        if not self.is_available:
            logger.warning("LangChain AI服务不可用，无法生成标签")
            return []
        
        callbacks_list = []
        langfuse_handler = self._get_langfuse_callback_handler(
            trace_name="generate_tags_llm",
            user_id=context_id or f"text_hash_{hash(text[:100])}", # Use context_id or hash of text
            tags=["tag_generation", "langchain"],
            metadata={"max_tags": max_tags, "text_length": len(text)}
        )
        if langfuse_handler:
            callbacks_list.append(langfuse_handler)

        try:
            # 创建提示
            prompt = f"""
            请为以下文本生成最多{max_tags}个相关标签。标签应该简洁、准确，并与创业产品相关。
            每个标签最好是1-3个单词，清晰地表达产品类别、功能或目标市场。
            仅返回用逗号分隔的标签列表。
            
            文本: {text}
            """
            
            # 使用LLM生成标签
            message = await self.llm.ainvoke(
                [{"role": "user", "content": prompt}],
                callbacks=callbacks_list # Pass handler to LLM invoke
            )
            result = message.content
            
            # 处理结果
            if not result:
                return []
            
            # 分割标签
            tags = [tag.strip() for tag in result.split(',')]
            
            # 过滤空标签并限制数量
            tags = [tag for tag in tags if tag][:max_tags]
            
            return tags
            
        except Exception as e:
            logger.error(f"生成标签过程中出错: {e}")
            return []
    
    async def can_generate_image(self) -> bool:
        """
        检查是否可以生成图像(基于每日限制)
        
        Returns:
            是否可以生成图像
        """
        today_str = datetime.now().date().isoformat()
        
        # 获取今日生成次数
        today_count = self.image_generation_records.get(today_str, 0)
        
        # 检查是否超过限制
        return today_count < self.IMAGE_GENERATION_DAILY_LIMIT
    
    def _increment_image_generation_count(self):
        """递增图像生成计数"""
        today_str = datetime.now().date().isoformat()
        
        # 获取并更新计数
        current_count = self.image_generation_records.get(today_str, 0)
        self.image_generation_records[today_str] = current_count + 1
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3
    )
    async def generate_image(self, product_id: int) -> Optional[str]:
        """
        为产品生成概念图像
        
        Args:
            product_id: 产品ID
            
        Returns:
            图像URL(如果成功)
        """
        if not self.is_available:
            logger.warning("LangChain AI服务不可用，无法生成图像")
            return None
        
        if not self.db:
            logger.error("数据库会话未提供，无法生成图像")
            return None
        
        # 检查日限制
        if not await self.can_generate_image():
            logger.warning("已达到每日图像生成限制")
            return None

        trace = None
        generation = None
        product_name_for_trace = "unknown_product"

        try:
            # 获取产品
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"未找到ID为 {product_id} 的产品")
                return None
            product_name_for_trace = product.name or f"product_id_{product_id}"

            if self.langfuse_client:
                trace = self.langfuse_client.trace(
                    name="generate_product_image_process",
                    user_id=str(product_id),
                    metadata={"product_name": product_name_for_trace, "product_id": product_id},
                    tags=["image_generation", "dall-e"]
                )

            # 生成图像提示词
            callbacks_list = []
            image_prompt_handler = self._get_langfuse_callback_handler(
                trace_name="image_prompt_generation_chain",
                user_id=str(product_id), # Link to the product
                tags=["image_prompt", "langchain"],
                metadata={"product_name": product.name, "product_description_length": len(product.description or "")}
            )
            if image_prompt_handler:
                if trace: # If manual trace exists, associate handler with it
                    image_prompt_handler.trace_id = trace.id
                callbacks_list.append(image_prompt_handler)

            prompt_result = await self.image_prompt_chain.ainvoke({
                "product_name": product.name or "创新产品",
                "product_description": product.description or "一个解决特定问题的产品",
                "problem_solved": product.problem_solved or "提升用户体验的问题"
            }, config={"callbacks": callbacks_list})
            
            # 清理提示词
            prompt = prompt_result.strip().replace("\\n", " ")
            logger.info(f"为产品 {product.name} 生成的图像提示词: {prompt}")

            if trace: # Create generation under the manual trace
                generation = trace.generation(
                    name="dall-e_image_api_call",
                    model="dall-e-2",
                    prompt=prompt,
                    model_parameters={"size": "512x512", "n": 1, "response_format": "url"}
                )
            
            # 调用DALL-E API生成图像
            client = httpx.AsyncClient(timeout=60.0)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
            }
            
            payload = {
                "model": "dall-e-2",  # 使用较低成本的模型
                "prompt": prompt,
                "n": 1,
                "size": "512x512",  # 较小尺寸以控制成本
                "response_format": "url"
            }
            
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取图像URL
            if result and "data" in result and len(result["data"]) > 0:
                dalle_image_url = result["data"][0]["url"]
                
                if generation: # End generation successfully
                    generation.end(output={"image_url": dalle_image_url})

                # 下载图片
                logger.info(f"Downloading image from DALL-E URL: {dalle_image_url}")
                async with httpx.AsyncClient(timeout=60.0) as download_client:
                    image_response = await download_client.get(dalle_image_url)
                    image_response.raise_for_status()
                
                image_data = image_response.content
                file_extension = os.path.splitext(dalle_image_url)[1].split('?')[0]
                if not file_extension:
                    file_extension = ".png"
                
                image_filename = f"{uuid.uuid4()}{file_extension}"
                image_dir = os.path.join("static", "product_images")
                os.makedirs(image_dir, exist_ok=True)
                local_image_path = os.path.join(image_dir, image_filename)
                
                with open(local_image_path, "wb") as f:
                    f.write(image_data)
                
                logger.info(f"Image saved locally to: {local_image_path}")
                
                # 更新产品记录
                product.image_url = f"/static/product_images/{image_filename}"
                self.db.commit()
                
                # 递增计数
                self._increment_image_generation_count()
                
                if trace: # End trace successfully
                    trace.update(metadata={"final_image_url": product.image_url})
                
                return product.image_url
            else:
                logger.warning("图像生成API返回了无效的响应格式")
                if generation: # End generation with an error
                    generation.end(level="ERROR", status_message="Invalid API response format")
                if trace:
                    trace.update(metadata={"error": "Invalid API response format"})
                return None
                
        except Exception as e:
            logger.error(f"生成图像过程中出错: {e}")
            if generation: # End generation with an error
                generation.end(level="ERROR", status_message=str(e))
            if trace: # End trace with error (or update with error info)
                trace.update(metadata={"error": str(e), "status": "ERROR"})
            return None
        finally:
            if self.langfuse_client: # Ensure shutdown if client was created
                 # self.langfuse_client.shutdown() # Consider if shutdown is needed per call or at app level
                 pass # Langfuse client usually handles flushing on its own or on shutdown()

    async def analyze_featured_products(self, limit: int = 3) -> List[Tuple[Product, str]]:
        """
        分析并为精选产品生成图像
        
        Args:
            limit: 要处理的产品数量
            
        Returns:
            产品和图像URL的元组列表
        """
        if not self.db:
            logger.error("数据库会话未提供，无法分析精选产品")
            return []
        
        try:
            # 获取最近的高评分产品
            today = datetime.now().date()
            featured_products = self.db.query(Product).join(Product.post).filter(
                func.date(Product.post.collected_at) == today
            ).order_by(Product.post.points.desc()).limit(limit).all()
            
            result = []
            for product in featured_products:
                # 检查产品是否已有图像
                if not product.image_url and await self.can_generate_image():
                    # 生成图像
                    image_url = await self.generate_image(product.id)
                    if image_url:
                        result.append((product, image_url))
                elif product.image_url:
                    result.append((product, product.image_url))
            
            return result
            
        except Exception as e:
            logger.error(f"分析精选产品过程中出错: {e}")
            return []

    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3
    )
    async def generate_product_image(self, product_name: str, product_description: str) -> Optional[str]:
        """
        为产品生成概念图
        
        Args:
            product_name: 产品名称
            product_description: 产品描述
            
        Returns:
            生成的图片URL或None（如果生成失败）
        """
        if not self.is_available:
            logger.warning("LangChain AI服务不可用，无法生成图像")
            return None
        
        # 检查日限制
        if not await self.can_generate_image():
            logger.warning("已达到每日图像生成限制")
            return None

        # 用于 Langfuse 追踪的 product_name 或唯一标识符
        trace_user_id = product_name or f"unknown_product_{str(uuid.uuid4())[:8]}"

        try:
            # 为 image_prompt_chain 调用创建 Langfuse 回调
            callbacks_list = []
            image_prompt_handler = self._get_langfuse_callback_handler(
                trace_name="concept_image_prompt_chain_v2", # 使用不同的追踪名称以区分
                user_id=trace_user_id,
                tags=["image_prompt", "langchain", "concept", "no_context_id_version"],
                metadata={"product_name": product_name, "product_description_length": len(product_description or "")}
            )
            if image_prompt_handler:
                callbacks_list.append(image_prompt_handler)
            
            # 生成图像提示词
            prompt_result = await self.image_prompt_chain.ainvoke({
                "product_name": product_name,
                "product_description": product_description[:200] if product_description else "创新产品", # 限制描述长度
                "problem_solved": "提升用户体验的问题" # 保持与另一个版本一致或使其动态化
            }, config={"callbacks": callbacks_list}) # <--- 添加了 callbacks
            
            # 清理提示词
            prompt = prompt_result.strip().replace("\\n", " ")
            logger.info(f"为产品 {product_name} 生成的图像提示词: {prompt}")
            
            # 调用DALL-E API生成图像
            # 注意：直接的API调用 (非Langchain LLM调用) 不会自动通过CallbackHandler追踪。
            # 如果需要追踪这部分，需要像另一个 generate_product_image 方法那样使用手动的 trace.generation()。
            # 为了当前问题的修复，我们主要关注 Langchain 链的追踪。
            client = httpx.AsyncClient(timeout=60.0)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
            }
            
            payload = {
                "model": "dall-e-2",  # 使用DALL-E 2模型
                "prompt": prompt,
                "n": 1,
                "size": "512x512",  # 使用512x512尺寸
                "response_format": "url"
            }
            
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取图像URL
            if result and "data" in result and len(result["data"]) > 0:
                dalle_image_url = result["data"][0]["url"]
                
                # 下载图片
                logger.info(f"Downloading image from DALL-E URL: {dalle_image_url}")
                async with httpx.AsyncClient(timeout=60.0) as download_client:
                    image_response = await download_client.get(dalle_image_url)
                    image_response.raise_for_status()
                
                image_data = image_response.content
                file_extension = os.path.splitext(dalle_image_url)[1].split('?')[0]
                if not file_extension:
                    file_extension = ".png"
                
                image_filename = f"{uuid.uuid4()}{file_extension}"
                image_dir = os.path.join("static", "product_images")
                os.makedirs(image_dir, exist_ok=True)
                local_image_path = os.path.join(image_dir, image_filename)
                
                with open(local_image_path, "wb") as f:
                    f.write(image_data)
                
                logger.info(f"Image saved locally to: {local_image_path}")
                
                # 递增计数
                self._increment_image_generation_count()
                
                logger.info(f"成功为产品 '{product_name}' 生成概念图并保存到本地")
                return f"/static/product_images/{image_filename}"
            else:
                logger.warning("图像生成API返回了无效的响应格式")
                return None
                
        except Exception as e:
            logger.error(f"生成产品概念图失败: {e}")
            return None
        finally:
            if self.langfuse_client:
                # self.langfuse_client.shutdown() # Consider if shutdown is needed per call or at app level
                pass 