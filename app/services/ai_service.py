"""
AI服务模块 - 负责与OpenAI API交互并提供AI分析能力
"""
import time
import asyncio
from typing import Dict, Any, List, Optional, Union
import httpx
import json
import backoff
from pydantic import BaseModel
import openai

from app.core.config import settings
from app.utils.logger import logger

class AIAnalysisResult(BaseModel):
    """AI分析结果数据模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    problem_solved: Optional[str] = None
    target_audience: Optional[str] = None
    competitive_advantage: Optional[str] = None
    potential_competitors: Optional[str] = None
    business_model: Optional[str] = None
    tags: List[str] = []

class AIService:
    """AI服务类，负责与OpenAI API交互并提供分析功能"""
    
    # OpenAI API URL
    API_URL = "https://api.openai.com/v1/chat/completions"
    
    # 默认模型
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    # 重试次数和延迟
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒
    
    def __init__(self):
        """初始化AI服务"""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or self.DEFAULT_MODEL
        
        # 验证API密钥是否已设置
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            logger.warning("OpenAI API密钥未设置，AI功能将不可用")
        
        # 设置OpenAI API密钥
        openai.api_key = self.api_key
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=MAX_RETRIES
    )
    async def call_openai_api(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Dict[str, Any]:
        """
        调用OpenAI API
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数，控制输出随机性（GPT-5模型不支持此参数）
            
        Returns:
            API响应
        """
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API密钥未设置")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建payload，GPT-5模型不支持temperature参数
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        # 只有非GPT-5模型才添加temperature参数
        if not self.model.startswith("gpt-5"):
            payload["temperature"] = temperature
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # 限流错误，等待后重试
                logger.warning("OpenAI API限流，正在重试...")
                time.sleep(self.RETRY_DELAY)
                raise
            else:
                logger.error(f"OpenAI API调用失败: {e}")
                logger.error(f"错误详情: {e.response.text if hasattr(e, 'response') else 'No response'}")
                raise
                
        except Exception as e:
            logger.error(f"调用OpenAI API时出错: {e}")
            raise
    
    async def analyze_product(self, title: str, content: str, url: str = "") -> Optional[AIAnalysisResult]:
        """
        分析帖子内容，提取产品信息
        
        Args:
            title: 帖子标题
            content: 帖子内容
            url: 帖子URL（可选）
            
        Returns:
            产品分析结果对象
        """
        try:
            prompt = self._generate_product_analysis_prompt(title, content, url)
            
            messages = [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ]
            
            # 调用API
            response = await self.call_openai_api(messages)
            
            # 提取结果
            if response and "choices" in response and len(response["choices"]) > 0:
                result_text = response["choices"][0]["message"]["content"]
                return self._parse_analysis_result(result_text)
            else:
                logger.warning("OpenAI API返回了无效的响应格式")
                return None
                
        except ValueError as e:
            logger.warning(f"分析失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"产品分析过程中出错: {e}")
            return None
    
    def _generate_product_analysis_prompt(self, title: str, content: str, url: str) -> Dict[str, str]:
        """
        生成产品分析提示
        
        Args:
            title: 帖子标题
            content: 帖子内容
            url: 帖子URL
            
        Returns:
            包含system和user提示的字典
        """
        system_prompt = """
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
        
        如果某项信息不存在，请回答"未提及"。请确保你的分析客观、精确，并基于提供的信息。
        请以JSON格式返回结果，确保格式正确可解析。
        """
        
        user_prompt = f"""
        请分析以下帖子中的产品信息：
        
        标题: {title}
        
        内容: {content}
        
        URL: {url}
        
        请以下面的JSON格式返回结果:
        {{
            "name": "产品名称",
            "description": "产品简要描述",
            "problem_solved": "产品解决的问题",
            "target_audience": "目标受众",
            "competitive_advantage": "竞争优势",
            "potential_competitors": "潜在竞争对手",
            "business_model": "商业模式",
            "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"]
        }}
        """
        
        return {
            "system": system_prompt.strip(),
            "user": user_prompt.strip()
        }
    
    def _parse_analysis_result(self, result_text: str) -> AIAnalysisResult:
        """
        解析AI分析结果
        
        Args:
            result_text: AI返回的文本内容
            
        Returns:
            解析后的结构化数据
        """
        try:
            # 尝试提取JSON部分
            json_text = result_text
            
            # 如果文本包含多余内容，尝试只提取JSON部分
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
            
            # 解析JSON
            data = json.loads(json_text)
            
            # 创建结果对象
            result = AIAnalysisResult(
                name=data.get("name", None),
                description=data.get("description", None),
                problem_solved=data.get("problem_solved", None),
                target_audience=data.get("target_audience", None),
                competitive_advantage=data.get("competitive_advantage", None),
                potential_competitors=data.get("potential_competitors", None),
                business_model=data.get("business_model", None),
                tags=data.get("tags", [])
            )
            
            # 处理"未提及"的情况
            for field in result.model_fields:
                if getattr(result, field) == "未提及":
                    setattr(result, field, None)
            
            return result
            
        except json.JSONDecodeError:
            logger.error(f"无法解析AI返回的JSON: {result_text}")
            # 返回空结果
            return AIAnalysisResult()
        
        except Exception as e:
            logger.error(f"解析分析结果时出错: {e}")
            return AIAnalysisResult()
    
    async def generate_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """
        为给定文本生成标签
        
        Args:
            text: 要分析的文本
            max_tags: 最大标签数量
            
        Returns:
            标签列表
        """
        try:
            prompt = f"""
            根据以下文本，生成最多{max_tags}个相关的标签：
            
            {text}
            
            请以JSON数组格式返回标签，例如 ["标签1", "标签2", "标签3"]
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的内容分析系统，擅长为文本生成精确的标签。请只返回JSON格式的标签列表，不要有额外的说明。"},
                {"role": "user", "content": prompt}
            ]
            
            # 调用API
            response = await self.call_openai_api(messages)
            
            # 提取结果
            if response and "choices" in response and len(response["choices"]) > 0:
                result_text = response["choices"][0]["message"]["content"]
                
                # 提取JSON数组
                try:
                    # 尝试直接解析
                    tags = json.loads(result_text)
                    
                    # 如果结果不是列表，尝试提取JSON部分
                    if not isinstance(tags, list):
                        json_start = result_text.find('[')
                        json_end = result_text.rfind(']') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            tags = json.loads(result_text[json_start:json_end])
                    
                    # 确保结果是字符串列表
                    if isinstance(tags, list):
                        tags = [str(tag) for tag in tags if tag]
                        return tags[:max_tags]  # 限制最大数量
                    
                except json.JSONDecodeError:
                    # 如果无法解析JSON，尝试简单拆分
                    potential_tags = result_text.replace('[', '').replace(']', '').replace('"', '').replace("'", '').split(',')
                    tags = [tag.strip() for tag in potential_tags if tag.strip()]
                    return tags[:max_tags]
            
            return []
                
        except Exception as e:
            logger.error(f"生成标签时出错: {e}")
            return []
    
    async def generate_product_image(self, product_name: str, product_description: str) -> Optional[str]:
        """
        为产品生成概念图
        
        Args:
            product_name: 产品名称
            product_description: 产品描述
            
        Returns:
            生成的图片URL或None（如果生成失败）
        """
        try:
            # 创建提示词
            prompt = f"A clean, modern product concept image for '{product_name}': {product_description[:200]}. Minimal, professional design."
            
            # 调用DALL-E API（直接使用httpx而不是openai库）
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "dall-e-2",
                "prompt": prompt,
                "n": 1,
                "size": "512x512",
                "response_format": "url"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            # 提取图片URL
            if result and "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                logger.info(f"成功为产品 '{product_name}' 生成概念图")
                return image_url
            else:
                logger.warning("图像生成API返回了无效的响应格式")
                return None
        except Exception as e:
            logger.error(f"生成产品概念图失败: {e}")
            return None 