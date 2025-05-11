from sqlalchemy.orm import Session
from backend.app.services.tag_service import TagService
from backend.app.db.session import SessionLocal

def init_tags():
    db = SessionLocal()
    tag_service = TagService(db)
    
    # 创建标签分类
    categories = {
        "Tech Stack": {
            "description": "技术栈和开发工具",
            "tags": [
                "Python", "JavaScript", "React", "Vue", "Node.js", "Django", "Flask",
                "FastAPI", "PostgreSQL", "MongoDB", "Redis", "Docker", "AWS", "GCP",
                "Azure", "Kubernetes", "GraphQL", "REST API", "WebSocket", "WebRTC",
                "TypeScript", "Next.js", "Nuxt.js", "Tailwind CSS", "Bootstrap"
            ]
        },
        "Product Type": {
            "description": "产品类型和形态",
            "tags": [
                "Web App", "Mobile App", "Desktop App", "Browser Extension",
                "API Service", "SaaS", "PaaS", "IaaS", "CLI Tool", "Library",
                "Framework", "Plugin", "Theme", "Template", "Widget"
            ]
        },
        "Target Market": {
            "description": "目标市场和用户群体",
            "tags": [
                "B2B", "B2C", "B2B2C", "Enterprise", "SMB", "Startup",
                "Developer", "Designer", "Product Manager", "Marketer",
                "Student", "Educator", "Freelancer", "Agency", "Team"
            ]
        },
        "Business Model": {
            "description": "商业模式和变现方式",
            "tags": [
                "Freemium", "Subscription", "One-time Purchase", "Open Source",
                "Enterprise License", "Marketplace", "API as a Service",
                "White Label", "Affiliate", "Advertising", "Sponsorship"
            ]
        },
        "Development Stage": {
            "description": "产品开发阶段",
            "tags": [
                "MVP", "Beta", "Production", "Growth", "Mature",
                "Pre-launch", "Early Access", "Alpha", "Prototype"
            ]
        }
    }
    
    # 创建分类和标签
    for category_name, category_data in categories.items():
        # 创建分类
        category = tag_service.create_category(
            name=category_name,
            description=category_data["description"]
        )
        
        # 创建该分类下的标签
        for tag_name in category_data["tags"]:
            tag_service.create_tag(
                name=tag_name,
                category_id=category.id
            )
    
    print("标签初始化完成！")
    db.close()

if __name__ == "__main__":
    init_tags() 