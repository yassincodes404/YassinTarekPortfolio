import asyncio
import json
import sys
import os

# Add the project root to the python path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import async_session
from app import crud

async def seed_data():
    async with async_session() as db:
        # 1. Update Home Page
        home_page = await crud.get_page_by_slug(db, "home")
        if home_page:
            home_blocks = [
                {
                    "id": "hero-1",
                    "type": "hero",
                    "props": {
                        "title": "Hi, I'm Yassin Tarek",
                        "subtitle": "A passionate Software Engineer specializing in Python, FastAPI, React, and building scalable backends with Docker & Cloud architectures.",
                        "cta": [{"label": "See My Work", "href": "/projects"}]
                    },
                    "styles": {}
                },
                {
                    "id": "text-intro-1",
                    "type": "text_block",
                    "props": {
                        "content": "### Featured Work\nHere are some of the projects I've worked on recently. From high-performance APIs to full-stack web applications, I enjoy tackling complex challenges and delivering robust solutions."
                    },
                    "styles": {}
                },
                {
                    "id": "achievements-1",
                    "type": "achievements",
                    "props": {
                        "title": "Milestones & Achievements",
                        "items": [
                            {
                                "icon": "🚀",
                                "title": "Launched 10+ Production Apps",
                                "description": "Successfully designed and deployed scalable systems serving thousands of active users.",
                                "year": "2024"
                            },
                            {
                                "icon": "⭐",
                                "title": "Open Source Contributor",
                                "description": "Active maintainer and contributor to various high-profile Python frameworks.",
                                "year": "2023"
                            },
                            {
                                "icon": "💡",
                                "title": "Tech Lead at Startup",
                                "description": "Led an engineering team to deliver a comprehensive AI pipeline in record time.",
                                "year": "2022"
                            }
                        ]
                    },
                    "styles": {}
                },
                {
                    "id": "proj-grid-1",
                    "type": "project_grid",
                    "props": {"columns": 2, "filterTags": []},
                    "styles": {}
                }
            ]
            await crud.update_page(db, home_page, {"blocks": home_blocks})
            print("Updated Home page.")

        # 2. Update About Page
        about_page = await crud.get_page_by_slug(db, "about")
        if about_page:
            about_blocks = [
                {
                    "id": "text-about-1",
                    "type": "text_block",
                    "props": {
                        "content": "# About Me\n\nI am a Full-Stack Developer with a strong focus on backend infrastructure, database design, and intuitive frontend experiences.\n\n### Core Technologies\n- **Languages**: Python, JavaScript/TypeScript, Java, C++\n- **Backend**: FastAPI, Django, Node.js\n- **Frontend**: React, Next.js, HTMX\n- **Databases**: PostgreSQL, MySQL, Redis, SQLite\n- **DevOps**: Docker, GitHub Actions, Linux Server Administration\n\nI enjoy open-source contributions, learning about distributed systems, and refining automated testing pipelines."
                    },
                    "styles": {}
                }
            ]
            await crud.update_page(db, about_page, {"blocks": about_blocks})
            print("Updated About page.")

        # 3. Update Contact Page
        contact_page = await crud.get_page_by_slug(db, "contact")
        if contact_page:
            contact_blocks = [
                {
                    "id": "text-contact-1",
                    "type": "text_block",
                    "props": {
                        "content": "# Get In Touch\n\nI'm always open to discussing new projects, creative ideas, or opportunities to be part of your visions.\n\n- **Email**: hi@yassintarek.dev\n- **Location**: Cairo, Egypt (Available Remote)\n- **LinkedIn**: [linkedin.com/in/yassin-tarek-dev](#)\n- **GitHub**: [github.com/yassintarek](#)\n\nDrop me a message and I'll get back to you as soon as possible!"
                    },
                    "styles": {}
                }
            ]
            await crud.update_page(db, contact_page, {"blocks": contact_blocks})
            print("Updated Contact page.")

        # 4. Create Demo Projects
        projects = [
            {
                "title": "Real-time AI Processing Pipeline",
                "slug": "ai-processing-pipeline",
                "short_description": "A high-throughput video processing pipeline leveraging computer vision models to track objects in real-time.",
                "full_description": "### Overview\nThis project involved creating a robust backend pipeline capable of ingesting video feeds, processing them through a series of object detection algorithms, and streaming the results via WebSockets.\n\n### Challenges Overcome\n- Handling high concurrency.\n- Optimizing GPU memory usage.\n- Ensuring zero-downtime deployments.",
                "tech_stack": ["Python", "FastAPI", "OpenCV", "PyTorch", "Redis Streams"],
                "video_embed_url": "https://www.youtube.com/embed/ScMzIvxBSi4",
                "status": "published"
            },
            {
                "title": "E-Commerce Microservices Architecture",
                "slug": "ecommerce-microservices",
                "short_description": "A scalable e-commerce platform built as a collection of decoupled microservices using Docker and Kubernetes.",
                "full_description": "### The Solution\nWe broke down a monolithic application into distinct services (Auth, Catalog, Cart, Order, Payment). Each service is independently deployable and scalable.\n\n### Key Features\n- Event-driven communication using RabbitMQ.\n- Centralized logging and monitoring with ELK stack.\n- Automated CI/CD pipelines.",
                "tech_stack": ["Node.js", "Express", "PostgreSQL", "RabbitMQ", "Docker"],
                "video_embed_url": "https://www.youtube.com/embed/1vRzBInY6zI",
                "status": "published"
            },
            {
                "title": "Interactive Data Dashboard",
                "slug": "interactive-data-dashboard",
                "short_description": "A responsive business intelligence dashboard providing real-time analytics to corporate clients.",
                "full_description": "### High-Quality Analytics\nThe dashboard aggregates millions of data points and presents them in a digestible format using complex charts, drill-down capabilities, and exportable reports.\n\nFrontend architecture was specifically designed to handle large render lists without noticeable lag.",
                "tech_stack": ["React", "D3.js", "TypeScript", "Django REST Framework"],
                "video_embed_url": "https://www.youtube.com/embed/LXb3EKWsInQ",
                "status": "published"
            }
        ]

        for p_data in projects:
            existing = await crud.get_project_by_slug(db, p_data["slug"])
            if not existing:
                await crud.create_project(db, p_data)
                print(f"Created project: {p_data['title']}")
            else:
                await crud.update_project(db, existing, p_data)
                print(f"Updated project: {p_data['title']}")

        # 5. Set Global Settings
        settings = {
            "site_title": "Yassin Tarek | Portfolio",
            "site_description": "Portfolio of Yassin Tarek - Full Stack Software Engineer",
            "social_links": json.dumps({
                "github": "https://github.com/yassintarek",
                "linkedin": "https://linkedin.com/in/yassin-tarek-dev",
                "twitter": "https://twitter.com/yassintarek"
            }),
            "contact_email": "hi@yassintarek.dev"
        }
        for k, v in settings.items():
            await crud.set_setting(db, k, v)
        
        await db.commit()
        print("Updated site settings.")

if __name__ == "__main__":
    asyncio.run(seed_data())
