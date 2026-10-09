from datetime import datetime
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project


def create_sample_data():
    """
    Idempotent sample data generator:
    Creates 6 groups, members, and projects for testing and public browsing.
    Returns the number of groups created.
    """
    if Group.query.first():
        print("[SAMPLE DATA] Sample data already present — skipping.")
        return 0

    sample_groups_defs = [
        {
            "name": "Acme Devs",
            "slug": "acme-devs",
            "tagline": "Full-stack cloud architectures and modern distributed web platforms.",
            "description": "Acme Devs is an elite student engineering squad specializing in cloud-native application development, serverless orchestration, and scalable microservices.\n\nFormed by top students across computer science and systems engineering, the crew focuses on developer ergonomics, automated CI/CD pipelines, and bulletproof infrastructure.",
            "founded_year": 2021,
            "tech_tags": ["python", "flask", "docker", "aws", "postgresql"],
            "featured": True,
            "members": [
                {
                    "name": "Alex Vance",
                    "role": "Team Lead & Cloud Architect",
                    "bio": "Specializes in Kubernetes, AWS Terraform modules, and backend API performance.",
                    "skill_tags": ["python", "docker", "terraform"],
                    "resume_pdf": "uploads/resumes/alex-vance.pdf",
                    "github_url": "https://github.com/example/alex",
                    "linkedin_url": "https://linkedin.com/in/example-alex",
                },
                {
                    "name": "Maya Lin",
                    "role": "Frontend Specialist",
                    "bio": "Passionate about responsive web design, accessible UX components, and high-performance JS.",
                    "skill_tags": ["javascript", "react", "css3"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/maya",
                    "linkedin_url": "https://linkedin.com/in/example-maya",
                },
                {
                    "name": "Chris Taylor",
                    "role": "Backend Developer",
                    "bio": "Enjoys relational database query optimization and event-driven architectures.",
                    "skill_tags": ["python", "postgresql", "redis"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/chris",
                    "linkedin_url": "https://linkedin.com/in/example-chris",
                },
            ],
            "projects": [
                {
                    "title": "CloudPulse Monitoring",
                    "slug": "cloudpulse-monitoring",
                    "summary": "Real-time microservice latency and uptime dashboard.",
                    "description": "An end-to-end telemetry collector featuring sub-second metric visualizers and webhook alerting.",
                    "tech_tags": ["python", "docker", "postgresql"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/cloudpulse",
                    "github_url": "https://github.com/example/cloudpulse",
                },
                {
                    "title": "EdgeCache Proxy",
                    "slug": "edgecache-proxy",
                    "summary": "High-throughput reverse proxy with local memory caching.",
                    "description": "Lightweight reverse proxy built to minimize latency for distributed static media deliveries.",
                    "tech_tags": ["python", "flask", "redis"],
                    "featured": False,
                    "demo_url": "https://example.com/demo/edgecache",
                    "github_url": "https://github.com/example/edgecache",
                },
            ],
        },
        {
            "name": "Apex Labs",
            "slug": "apex-labs",
            "tagline": "AI-powered tools, machine learning pipelines, and predictive interfaces.",
            "description": "Apex Labs pushes the boundary between artificial intelligence research and practical web applications.\n\nThe team builds clean, reliable tools for natural language understanding, automated classification, and conversational agent workflows.",
            "founded_year": 2022,
            "tech_tags": ["python", "pytorch", "fastapi", "docker"],
            "featured": True,
            "members": [
                {
                    "name": "Elena Rostova",
                    "role": "ML Engineer & Lead",
                    "bio": "Focuses on neural fine-tuning, embeddings search, and vector databases.",
                    "skill_tags": ["python", "pytorch", "nlp"],
                    "resume_pdf": "uploads/resumes/elena-rostova.pdf",
                    "github_url": "https://github.com/example/elena",
                    "linkedin_url": "https://linkedin.com/in/example-elena",
                },
                {
                    "name": "David Kim",
                    "role": "Data Engineer",
                    "bio": "Expert in streaming data transformation pipelines and feature extraction.",
                    "skill_tags": ["python", "pandas", "sql"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/david",
                    "linkedin_url": "https://linkedin.com/in/example-david",
                },
            ],
            "projects": [
                {
                    "title": "SemanticSense Search",
                    "slug": "semanticsense-search",
                    "summary": "Vector-indexed search engine for unstructured documentation.",
                    "description": "Transforms large PDF and Markdown corpora into instantly queryable semantic vectors.",
                    "tech_tags": ["python", "pytorch", "fastapi"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/semanticsense",
                    "github_url": "https://github.com/example/semanticsense",
                },
            ],
        },
        {
            "name": "Binary Brains",
            "slug": "binary-brains",
            "tagline": "Systems programming, low-latency backends, and networking protocols.",
            "description": "Binary Brains is dedicated to robust systems infrastructure, network security, and high-efficiency backends.\n\nTheir portfolio spans custom binary protocols, concurrent processing servers, and memory-safe service daemons.",
            "founded_year": 2020,
            "tech_tags": ["c++", "rust", "python", "linux"],
            "featured": True,
            "members": [
                {
                    "name": "Marcus Stone",
                    "role": "Systems Engineer",
                    "bio": "Deep understanding of Linux kernel primitives, epoll sockets, and threading.",
                    "skill_tags": ["rust", "linux", "c++"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/marcus",
                    "linkedin_url": "https://linkedin.com/in/example-marcus",
                },
            ],
            "projects": [
                {
                    "title": "NetMesh Tunnel",
                    "slug": "netmesh-tunnel",
                    "summary": "Encrypted P2P network overlay for developer clusters.",
                    "description": "Enables zero-configuration encrypted mesh networks between development servers.",
                    "tech_tags": ["rust", "networking"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/netmesh",
                    "github_url": "https://github.com/example/netmesh",
                },
            ],
        },
        {
            "name": "Cloud Crafters",
            "slug": "cloud-crafters",
            "tagline": "Reliable enterprise backends and container automation.",
            "description": "Cloud Crafters bridges developer productivity with rock-solid server architectures.\n\nFrom microservice mesh implementations to automated zero-downtime rollouts, they craft dependable web services.",
            "founded_year": 2023,
            "tech_tags": ["python", "django", "docker", "kubernetes"],
            "featured": False,
            "members": [
                {
                    "name": "Sarah Connor",
                    "role": "DevOps Engineer",
                    "bio": "Automates everything with Docker, Ansible, and GitHub Actions.",
                    "skill_tags": ["docker", "ci/cd", "python"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/sarah",
                    "linkedin_url": "https://linkedin.com/in/example-sarah",
                },
            ],
            "projects": [
                {
                    "title": "KubeDeployer CLI",
                    "slug": "kubedeployer-cli",
                    "summary": "Single-command deployment CLI for ephemeral test environments.",
                    "description": "CLI tool generating preview URLs for pull requests with zero manual cluster configuration.",
                    "tech_tags": ["python", "kubernetes"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/kubedeployer",
                    "github_url": "https://github.com/example/kubedeployer",
                },
            ],
        },
        {
            "name": "Data Dragons",
            "slug": "data-dragons",
            "tagline": "Big data analytics, ETL pipelines, and interactive BI dashboards.",
            "description": "Data Dragons transforms messy raw datasets into actionable executive insights.\n\nThey specialize in scalable aggregation, analytical data warehousing, and modern reactive dashboards.",
            "founded_year": 2019,
            "tech_tags": ["python", "sql", "spark", "postgres"],
            "featured": False,
            "members": [
                {
                    "name": "Rohan Patel",
                    "role": "Data Architect",
                    "bio": "Enjoys dimensional modeling, query profiling, and distributed pipelines.",
                    "skill_tags": ["sql", "python", "spark"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/rohan",
                    "linkedin_url": "https://linkedin.com/in/example-rohan",
                },
            ],
            "projects": [
                {
                    "title": "MetricsForge Warehouse",
                    "slug": "metricsforge-warehouse",
                    "summary": "Automated data warehousing tool for SaaS billing analytics.",
                    "description": "Extracts, transforms, and indexes recurring revenue metrics for instant querying.",
                    "tech_tags": ["python", "postgres", "sql"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/metricsforge",
                    "github_url": "https://github.com/example/metricsforge",
                },
            ],
        },
        {
            "name": "Echo Engineers",
            "slug": "echo-engineers",
            "tagline": "Audio processing, streaming servers, and WebRTC collaboration.",
            "description": "Echo Engineers creates next-generation media tools for interactive web experiences.\n\nSpecialized in real-time streaming audio, signal DSP, and low-latency group voice protocols.",
            "founded_year": 2024,
            "tech_tags": ["python", "webrtc", "javascript", "ffmpeg"],
            "featured": False,
            "members": [
                {
                    "name": "Chloe Bennett",
                    "role": "Media Systems Developer",
                    "bio": "Passionate about audio codecs, low-latency streaming, and sound synthesis.",
                    "skill_tags": ["webrtc", "javascript", "python"],
                    "resume_pdf": None,
                    "github_url": "https://github.com/example/chloe",
                    "linkedin_url": "https://linkedin.com/in/example-chloe",
                },
            ],
            "projects": [
                {
                    "title": "SonicStream Server",
                    "slug": "sonicstream-server",
                    "summary": "Sub-50ms latency audio broadcast gateway for online workshops.",
                    "description": "Peer-assisted audio distribution gateway capable of serving hundreds of concurrent listeners.",
                    "tech_tags": ["python", "webrtc"],
                    "featured": True,
                    "demo_url": "https://example.com/demo/sonicstream",
                    "github_url": "https://github.com/example/sonicstream",
                },
            ],
        },
    ]

    count = 0
    for g_def in sample_groups_defs:
        group = Group(
            name=g_def["name"],
            slug=g_def["slug"],
            tagline=g_def["tagline"],
            description=g_def["description"],
            founded_year=g_def["founded_year"],
            tech_tags=g_def["tech_tags"],
            featured=g_def["featured"],
            logo="images/placeholder-logo.png",
            cover_image="images/placeholder-cover.png",
        )
        db.session.add(group)
        db.session.flush()

        for idx, m_def in enumerate(g_def["members"]):
            member = Member(
                group_id=group.id,
                name=m_def["name"],
                role=m_def["role"],
                bio=m_def["bio"],
                skill_tags=m_def["skill_tags"],
                resume_pdf=m_def["resume_pdf"],
                github_url=m_def["github_url"],
                linkedin_url=m_def["linkedin_url"],
                display_order=idx,
                photo="images/placeholder-photo.png",
            )
            db.session.add(member)

        for p_def in g_def["projects"]:
            project = Project(
                group_id=group.id,
                title=p_def["title"],
                slug=p_def["slug"],
                summary=p_def["summary"],
                description=p_def["description"],
                tech_tags=p_def["tech_tags"],
                featured=p_def["featured"],
                demo_url=p_def["demo_url"],
                github_url=p_def["github_url"],
                screenshot="images/placeholder-shot.png",
            )
            db.session.add(project)

        count += 1

    db.session.commit()
    print(f"[SAMPLE DATA] Successfully created {count} sample groups.")
    return count
