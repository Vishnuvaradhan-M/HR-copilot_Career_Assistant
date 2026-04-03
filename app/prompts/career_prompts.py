"""
Hardcoded role taxonomy and prompt templates for Career Assistant.

This module centralizes domain knowledge about:
1. Standard role taxonomies (canonical role names)
2. Role category mappings
3. Common role synonyms
4. Role relationships (promotions, lateral moves)
5. Prompt templates for reasoning steps

Rationale: No external APIs, all knowledge is deterministic and versioned.
"""

# ============================================================================
# ROLE TAXONOMY
# ============================================================================

# Canonical role names (source of truth)
STANDARD_ROLES = {
    "junior_software_engineer",
    "software_engineer",
    "senior_software_engineer",
    "staff_engineer",
    "principal_engineer",
    "data_analyst",
    "data_scientist",
    "senior_data_scientist",
    "ml_engineer",
    "senior_ml_engineer",
    "devops_engineer",
    "senior_devops_engineer",
    "cloud_architect",
    "product_manager",
    "senior_product_manager",
    "technical_lead",
    "engineering_manager",
    "director_of_engineering",
    "qa_engineer",
    "senior_qa_engineer",
    "ux_designer",
    "senior_ux_designer",
    "solutions_architect",
}

# Synonyms: map variations to canonical names
ROLE_SYNONYMS = {
    # Software Engineering variations
    "junior developer": "junior_software_engineer",
    "junior dev": "junior_software_engineer",
    "developer": "software_engineer",
    "dev": "software_engineer",
    "software dev": "software_engineer",
    "backend engineer": "software_engineer",
    "backend developer": "software_engineer",
    "frontend engineer": "software_engineer",
    "frontend developer": "software_engineer",
    "fullstack engineer": "software_engineer",
    "full stack developer": "software_engineer",
    "senior developer": "senior_software_engineer",
    "senior dev": "senior_software_engineer",
    "principal software engineer": "principal_engineer",
    "principal engineer": "principal_engineer",
    "staff software engineer": "staff_engineer",

    # Data roles
    "data analyst": "data_analyst",
    "analyst": "data_analyst",
    "bi analyst": "data_analyst",
    "data scientist": "data_scientist",
    "senior data scientist": "senior_data_scientist",
    "ml engineer": "ml_engineer",
    "machine learning engineer": "ml_engineer",
    "ai engineer": "ml_engineer",
    "senior ml engineer": "senior_ml_engineer",

    # DevOps/Infrastructure
    "devops": "devops_engineer",
    "devops engineer": "devops_engineer",
    "sre": "devops_engineer",
    "site reliability engineer": "devops_engineer",
    "infrastructure engineer": "devops_engineer",
    "senior devops engineer": "senior_devops_engineer",
    "cloud engineer": "cloud_architect",

    # Leadership/Management
    "tech lead": "technical_lead",
    "technical leader": "technical_lead",
    "engineering lead": "technical_lead",
    "manager": "engineering_manager",
    "engineering manager": "engineering_manager",
    "product manager": "product_manager",
    "pm": "product_manager",
    "senior pm": "senior_product_manager",
    "senior product manager": "senior_product_manager",
    "director": "director_of_engineering",
    "eng director": "director_of_engineering",

    # QA roles
    "qa": "qa_engineer",
    "qe": "qa_engineer",
    "tester": "qa_engineer",
    "quality assurance": "qa_engineer",
    "test engineer": "qa_engineer",
    "senior qa engineer": "senior_qa_engineer",
    "senior qe": "senior_qa_engineer",

    # Design roles
    "designer": "ux_designer",
    "ux designer": "ux_designer",
    "ui designer": "ux_designer",
    "ux/ui designer": "ux_designer",
    "senior ux designer": "senior_ux_designer",
    "senior designer": "senior_ux_designer",

    # Architecture roles
    "architect": "solutions_architect",
    "solutions architect": "solutions_architect",
    "enterprise architect": "solutions_architect",
}

# Role categories for skill grouping
ROLE_CATEGORIES = {
    "junior_software_engineer": "engineering",
    "software_engineer": "engineering",
    "senior_software_engineer": "engineering",
    "staff_engineer": "engineering",
    "principal_engineer": "engineering",
    "data_analyst": "data",
    "data_scientist": "data",
    "senior_data_scientist": "data",
    "ml_engineer": "data",
    "senior_ml_engineer": "data",
    "devops_engineer": "infrastructure",
    "senior_devops_engineer": "infrastructure",
    "cloud_architect": "infrastructure",
    "product_manager": "product",
    "senior_product_manager": "product",
    "technical_lead": "leadership",
    "engineering_manager": "leadership",
    "director_of_engineering": "leadership",
    "qa_engineer": "quality",
    "senior_qa_engineer": "quality",
    "ux_designer": "design",
    "senior_ux_designer": "design",
    "solutions_architect": "architecture",
}

# ============================================================================
# ROLE SKILL REQUIREMENTS
# ============================================================================
# Maps canonical role name -> list of required skills
# Proficiency levels: none, beginner, intermediate, advanced, expert

ROLE_SKILL_REQUIREMENTS = {
    "software_engineer": [
        ("Python", "advanced"),
        ("SQL", "intermediate"),
        ("Git", "advanced"),
        ("System Design", "intermediate"),
        ("Testing", "intermediate"),
        ("Code Review", "intermediate"),
    ],
    "senior_software_engineer": [
        ("Python", "expert"),
        ("SQL", "advanced"),
        ("Git", "expert"),
        ("System Design", "advanced"),
        ("Testing", "advanced"),
        ("Code Review", "advanced"),
        ("Mentoring", "intermediate"),
        ("Architecture", "intermediate"),
    ],
    "data_scientist": [
        ("Python", "advanced"),
        ("SQL", "advanced"),
        ("Statistics", "advanced"),
        ("Machine Learning", "advanced"),
        ("Data Visualization", "intermediate"),
        ("Linear Algebra", "intermediate"),
    ],
    "senior_data_scientist": [
        ("Python", "expert"),
        ("SQL", "expert"),
        ("Statistics", "expert"),
        ("Machine Learning", "expert"),
        ("Data Visualization", "advanced"),
        ("Linear Algebra", "advanced"),
        ("Communication", "advanced"),
        ("Project Leadership", "intermediate"),
    ],
    "ml_engineer": [
        ("Python", "advanced"),
        ("Machine Learning", "advanced"),
        ("Deep Learning", "intermediate"),
        ("Statistics", "intermediate"),
        ("Model Deployment", "intermediate"),
        ("TensorFlow/PyTorch", "intermediate"),
    ],
    "devops_engineer": [
        ("Linux", "advanced"),
        ("Docker", "advanced"),
        ("Kubernetes", "intermediate"),
        ("CI/CD", "advanced"),
        ("Infrastructure as Code", "intermediate"),
        ("AWS/Cloud", "intermediate"),
        ("Bash/Scripting", "advanced"),
    ],
    "product_manager": [
        ("Product Strategy", "advanced"),
        ("Data Analysis", "intermediate"),
        ("Communication", "advanced"),
        ("Roadmap Planning", "intermediate"),
        ("User Research", "intermediate"),
        ("Technical Understanding", "beginner"),
    ],
    "technical_lead": [
        ("Python", "advanced"),
        ("System Design", "advanced"),
        ("Code Review", "advanced"),
        ("Team Leadership", "intermediate"),
        ("Communication", "advanced"),
        ("Mentoring", "intermediate"),
    ],
    "engineering_manager": [
        ("Team Leadership", "advanced"),
        ("People Management", "advanced"),
        ("Communication", "advanced"),
        ("Hiring", "intermediate"),
        ("Performance Management", "intermediate"),
        ("Technical Understanding", "intermediate"),
    ],
    "ux_designer": [
        ("UI Design", "advanced"),
        ("User Research", "intermediate"),
        ("Prototyping", "advanced"),
        ("Figma", "advanced"),
        ("Design Systems", "intermediate"),
        ("Accessibility", "intermediate"),
    ],
    "qa_engineer": [
        ("Test Automation", "advanced"),
        ("Python", "intermediate"),
        ("SQL", "intermediate"),
        ("Testing Frameworks", "advanced"),
        ("Bug Analysis", "intermediate"),
        ("Performance Testing", "beginner"),
    ],
}

# ============================================================================
# SKILL CRITICALITY & PHASE ASSIGNMENT (Phase 2)
# ============================================================================
# Maps skill name -> (must_have: bool, primary_phase: str)
# must_have: True = critical to job function, False = nice-to-have/growth
# primary_phase: "foundation", "core", or "advanced"

SKILL_CRITICALITY = {
    # Foundation (prerequisites, basics everyone needs)
    "Python": (True, "foundation"),
    "SQL": (True, "foundation"),
    "Git": (True, "foundation"),
    "Linux": (True, "foundation"),
    "Bash": (True, "foundation"),
    "Communication": (True, "foundation"),
    "Statistics": (True, "foundation"),

    # Core (job-critical, immediate need)
    "System Design": (True, "core"),
    "Machine Learning": (True, "core"),
    "Testing": (True, "core"),
    "Code Review": (True, "core"),
    "Docker": (True, "core"),
    "CI/CD": (True, "core"),
    "Data Visualization": (True, "core"),
    "Team Leadership": (True, "core"),
    "People Management": (True, "core"),
    "Product Strategy": (True, "core"),
    "User Research": (True, "core"),
    "Test Automation": (True, "core"),
    "Data Analysis": (True, "core"),
    "Figma": (True, "core"),
    "UI Design": (True, "core"),
    "Prototyping": (True, "core"),
    "Mentoring": (True, "core"),

    # Advanced (nice-to-have, depth & specialization)
    "Architecture": (False, "advanced"),
    "Deep Learning": (False, "advanced"),
    "Model Deployment": (False, "advanced"),
    "Kubernetes": (False, "advanced"),
    "Infrastructure as Code": (False, "advanced"),
    "AWS/Cloud": (False, "advanced"),
    "TensorFlow/PyTorch": (False, "advanced"),
    "Design Systems": (False, "advanced"),
    "Accessibility": (False, "advanced"),
    "Linear Algebra": (False, "advanced"),
    "Performance Testing": (False, "advanced"),
    "Project Leadership": (False, "advanced"),
    "Roadmap Planning": (False, "advanced"),
    "Hiring": (False, "advanced"),
    "Performance Management": (False, "advanced"),
    "Technical Understanding": (False, "advanced"),
}

# ============================================================================
# SKILL LEARNING COMPLEXITY
# ============================================================================
# Estimates how hard a skill is to learn, considering prerequisites

SKILL_COMPLEXITY = {
    # Foundational
    "Python": "moderate",
    "SQL": "easy",
    "Bash": "moderate",
    "Git": "easy",
    "Linux": "moderate",

    # Intermediate
    "System Design": "hard",
    "Machine Learning": "hard",
    "Data Visualization": "moderate",
    "Docker": "moderate",
    "Kubernetes": "hard",

    # Advanced
    "Deep Learning": "hard",
    "Model Deployment": "hard",
    "Infrastructure as Code": "moderate",
    "CI/CD": "moderate",
    "Architecture": "hard",

    # Soft skills
    "Communication": "moderate",
    "Team Leadership": "hard",
    "Mentoring": "moderate",
    "Code Review": "easy",
    "Testing": "moderate",
    "User Research": "moderate",
}

# ============================================================================
# PROMPT TEMPLATES (for reasoning steps)
# ============================================================================

ROLE_NORMALIZATION_TEMPLATE = """
Normalize the following role title to one of the standard role names.

Input: "{input_role}"
Current role: "{current_role}"

Standard roles: {standard_roles}

Rules:
1. Exact match takes priority
2. Check synonyms for fuzzy matches
3. Consider career progression (promotions are valid, lateral moves less common)
4. Assign confidence (high=clear match, low=ambiguous)

Output format:
normalized_name: <string>
confidence: <float 0-1>
reasoning: <explanation>
"""

SKILL_GAP_ANALYSIS_TEMPLATE = """
Analyze skill gaps for career transition.

Current skills: {current_skills}
Target role required skills: {target_skills}

For each gap:
1. Identify severity: critical (blocks work), high (needed immediately), medium, low
2. Assess learning complexity: easy, moderate, hard
3. List prerequisites

Output: List of (skill, current_level, required_level, severity, complexity)
"""

LEARNING_PHASE_TEMPLATE = """
Design a phased learning path for skill acquisition.

Skill gaps (sorted by severity): {skill_gaps}
Weekly hours available: {hours_per_week}
Learning style: {learning_style}

Requirements:
1. Phase 1: Foundations (critical skills + easy prerequisites)
2. Phase 2: Core (job-critical technical skills)
3. Phase 3: Advanced (growth and specialization)

For each phase:
- List skills to learn
- Estimate duration in weeks
- Recommend resources (courses, projects, books)
- Define milestone checklist

Output: Structured phases with timelines
"""

FEASIBILITY_ASSESSMENT_TEMPLATE = """
Assess career transition feasibility.

Current state:
- Experience: {years_experience} years
- Current role category: {current_category}

Target state:
- Target role category: {target_category}
- Skill gaps: {num_gaps}
- Critical gaps: {critical_gaps}
- Estimated timeline: {total_weeks} weeks

Feasibility factors:
1. Experience fit (more experience = higher feasibility)
2. Skill continuity (related skills transfer)
3. Timeline realism (given hours per week)
4. Learning burden (total skills to learn)

Output: feasibility_score (0-1), rating (high/medium/low), reasoning
"""

# ============================================================================
# PHASE 3: EFFORT ESTIMATION & LEARNING TASK ASSIGNMENT
# ============================================================================
# Maps proficiency jumps to base hours (before complexity/severity multipliers)
# These are estimates based on industry standards

PROFICIENCY_JUMP_HOURS = {
    "none_to_beginner": 40,           # Learning basics (1-2 weeks at 20h/week)
    "beginner_to_intermediate": 60,   # Building competency (2-3 weeks)
    "intermediate_to_advanced": 80,   # Mastery & depth (3-4 weeks)
    "advanced_to_expert": 100,        # Expertise (4-5 weeks)
}

# Complexity multipliers (applied to base hours)
COMPLEXITY_MULTIPLIERS = {
    "easy": 1.0,       # Standard learning curve
    "moderate": 1.5,   # Additional depth/breadth
    "hard": 3.0,       # Steep learning curve, many prerequisites
}

# Severity multipliers (applied to base hours)
# Critical gaps require faster completion but same total effort
SEVERITY_MULTIPLIERS = {
    "critical": 1.0,   # Must learn, standard effort
    "high": 0.8,       # Important, but slightly less pressure
    "medium": 0.6,     # Nice to have soon
    "low": 0.4,        # Optional, lower urgency
}

# Resource type recommendations based on gap severity + complexity
RESOURCE_TYPE_MAPPING = {
    ("critical", "hard"): "course",      # Structured guidance needed
    ("critical", "moderate"): "course",
    ("critical", "easy"): "book",        # Can self-study easily
    ("high", "hard"): "project",         # Learn by doing
    ("high", "moderate"): "course",
    ("high", "easy"): "practice",
    ("medium", "hard"): "project",
    ("medium", "moderate"): "book",
    ("medium", "easy"): "practice",
    ("low", "hard"): "project",          # Optional, advanced track
    ("low", "moderate"): "book",
    ("low", "easy"): "practice",
}

# Recommended weekly effort by learning phase
# (as percentage of available hours)
PHASE_INTENSITY = {
    "foundation": 0.8,    # Focus heavily on foundation
    "core": 0.7,          # Core skills important
    "advanced": 0.5,      # Nice-to-have, can go slower
}

# ============================================================================
# LEARNING RESOURCES
# ============================================================================

SKILL_RESOURCES = {
    "Python": [
        {
            "name": "Python for Everybody - Coursera",
            "url": "https://www.coursera.org/specializations/python",
            "type": "course"
        },
        {
            "name": "Automate the Boring Stuff with Python (Free Book)",
            "url": "https://automatetheboringstuff.com",
            "type": "book"
        },
        {
            "name": "Kaggle Python Course (Free)",
            "url": "https://www.kaggle.com/learn/python",
            "type": "practice"
        }
    ],
    "SQL": [
        {
            "name": "SQL Tutorial - Mode Analytics",
            "url": "https://mode.com/sql-tutorial/",
            "type": "course"
        },
        {
            "name": "SQL Cookbook on GitHub",
            "url": "https://github.com/franzinc/sqlcookbook",
            "type": "book"
        },
        {
            "name": "LeetCode SQL Practice",
            "url": "https://leetcode.com/problemset/database/",
            "type": "practice"
        }
    ],
    "Statistics": [
        {
            "name": "Statistics with Python - Coursera",
            "url": "https://www.coursera.org/learn/statistics-python",
            "type": "course"
        },
        {
            "name": "Think Stats (Free Book)",
            "url": "http://greenteapress.com/thinkstats/",
            "type": "book"
        },
        {
            "name": "Khan Academy Statistics",
            "url": "https://www.khanacademy.org/math/statistics-probability",
            "type": "practice"
        }
    ],
    "Machine Learning": [
        {
            "name": "Machine Learning Basics - Coursera (Andrew Ng)",
            "url": "https://www.coursera.org/learn/machine-learning",
            "type": "course"
        },
        {
            "name": "Hands-on Machine Learning (Free chapters)",
            "url": "https://github.com/ageron/handson-ml2",
            "type": "book"
        },
        {
            "name": "Kaggle Machine Learning Competitions",
            "url": "https://www.kaggle.com/competitions",
            "type": "practice"
        }
    ],
    "Data Visualization": [
        {
            "name": "Data Visualization with Tableau - Coursera",
            "url": "https://www.coursera.org/learn/data-visualization",
            "type": "course"
        },
        {
            "name": "Storytelling with Data (Book summary)",
            "url": "https://www.oreilly.com/library/view/storytelling-with-data/9781119055259/",
            "type": "book"
        },
        {
            "name": "Matplotlib & Seaborn Tutorial",
            "url": "https://matplotlib.org/stable/tutorials/index.html",
            "type": "practice"
        }
    ],
    "Linear Algebra": [
        {
            "name": "3Blue1Brown Essence of Linear Algebra",
            "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
            "type": "course"
        },
        {
            "name": "Introduction to Linear Algebra (Book)",
            "url": "http://math.mit.edu/~gs/linearalgebra/",
            "type": "book"
        },
        {
            "name": "Khan Academy Linear Algebra",
            "url": "https://www.khanacademy.org/math/linear-algebra",
            "type": "practice"
        }
    ],
    "Deep Learning": [
        {
            "name": "Deep Learning Specialization - Coursera",
            "url": "https://www.coursera.org/specializations/deep-learning",
            "type": "course"
        },
        {
            "name": "Deep Learning Book (Free Online)",
            "url": "https://www.deeplearningbook.org/",
            "type": "book"
        },
        {
            "name": "Fast.ai Practical Deep Learning",
            "url": "https://www.fast.ai/",
            "type": "practice"
        }
    ],
    "NLP": [
        {
            "name": "Natural Language Processing with Python",
            "url": "https://www.coursera.org/learn/natural-language-processing",
            "type": "course"
        },
        {
            "name": "NLTK Book (Free Online)",
            "url": "https://www.nltk.org/book/",
            "type": "book"
        },
        {
            "name": "Hugging Face NLP Course",
            "url": "https://huggingface.co/course",
            "type": "practice"
        }
    ],
    "Excel": [
        {
            "name": "Excel Skills for Data Analysis - Coursera",
            "url": "https://www.coursera.org/learn/excel-data-analysis",
            "type": "course"
        },
        {
            "name": "Excel Bible (Microsoft Learn)",
            "url": "https://support.microsoft.com/en-us/excel",
            "type": "book"
        },
        {
            "name": "Chandoo Excel Tutorials",
            "url": "https://chandoo.org/",
            "type": "practice"
        }
    ],
    "Power BI": [
        {
            "name": "Microsoft Power BI Desktop for Data Analysis",
            "url": "https://www.coursera.org/learn/microsoft-power-bi-desktop",
            "type": "course"
        },
        {
            "name": "Power BI Documentation (Official)",
            "url": "https://docs.microsoft.com/en-us/power-bi/",
            "type": "book"
        },
        {
            "name": "Guy in a Cube Power BI Tutorials",
            "url": "https://www.youtube.com/channel/UCFp1vaKzpfqULLeGZF5lWXw",
            "type": "practice"
        }
    ],
    "Tableau": [
        {
            "name": "Tableau Desktop Specialist Certification",
            "url": "https://www.tableau.com/learn/public/getting-started",
            "type": "course"
        },
        {
            "name": "Tableau Official Documentation",
            "url": "https://help.tableau.com/current/public/en-us/",
            "type": "book"
        },
        {
            "name": "Tableau Public Gallery",
            "url": "https://public.tableau.com/app/discover",
            "type": "practice"
        }
    ],
    "R": [
        {
            "name": "R Programming for Data Science",
            "url": "https://www.coursera.org/learn/r-programming",
            "type": "course"
        },
        {
            "name": "R for Data Science (Free Book)",
            "url": "https://r4ds.had.co.nz/",
            "type": "book"
        },
        {
            "name": "Posit Tutorials for R",
            "url": "https://posit.co/resources/webinars/",
            "type": "practice"
        }
    ],
    "Spark": [
        {
            "name": "Apache Spark Essential Training",
            "url": "https://www.linkedin.com/learning/apache-spark-essential-training",
            "type": "course"
        },
        {
            "name": "Spark Official Documentation",
            "url": "https://spark.apache.org/docs/latest/",
            "type": "book"
        },
        {
            "name": "Spark by Examples",
            "url": "https://sparkbyexamples.com/",
            "type": "practice"
        }
    ],
    "Hadoop": [
        {
            "name": "Hadoop Essentials - Coursera",
            "url": "https://www.coursera.org/learn/hadoop-ecosystem",
            "type": "course"
        },
        {
            "name": "Hadoop Official Documentation",
            "url": "https://hadoop.apache.org/docs/stable/",
            "type": "book"
        },
        {
            "name": "MapReduce Tutorial",
            "url": "https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html",
            "type": "practice"
        }
    ],
    "Docker": [
        {
            "name": "Docker Basics - Udemy (Free)",
            "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
            "type": "course"
        },
        {
            "name": "Docker Official Documentation",
            "url": "https://docs.docker.com/",
            "type": "book"
        },
        {
            "name": "Docker Hub Tutorials",
            "url": "https://hub.docker.com/",
            "type": "practice"
        }
    ],
    "Git": [
        {
            "name": "Git & GitHub Crash Course - YouTube",
            "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
            "type": "course"
        },
        {
            "name": "Pro Git (Free Book)",
            "url": "https://git-scm.com/book/en/v2",
            "type": "book"
        },
        {
            "name": "GitHub Learning Lab",
            "url": "https://github.com/skills",
            "type": "practice"
        }
    ],
    "Communication": [
        {
            "name": "Effective Communication for Career Success",
            "url": "https://www.coursera.org/learn/communicate-successfully-at-work",
            "type": "course"
        },
        {
            "name": "Crucial Conversations (Book Summary)",
            "url": "https://www.goodreads.com/book/show/15014.Crucial_Conversations",
            "type": "book"
        },
        {
            "name": "Toastmasters Speaking Practice",
            "url": "https://www.toastmasters.org/",
            "type": "practice"
        }
    ],
    "Leadership": [
        {
            "name": "Modern Leadership - Coursera",
            "url": "https://www.coursera.org/learn/modern-leadership",
            "type": "course"
        },
        {
            "name": "The First 90 Days (Book)",
            "url": "https://www.goodreads.com/book/show/15824358-the-first-90-days",
            "type": "book"
        },
        {
            "name": "MIT Leadership Center",
            "url": "https://mitsloan.mit.edu/about/leadership",
            "type": "practice"
        }
    ],
}

# ============================================================================
# SKILL DESCRIPTIONS (for UI tooltips)
# ============================================================================

SKILL_DESCRIPTIONS = {
    "python": "Core language for all data science workflows and ML libraries",
    "sql": "Essential for querying, joining and managing large datasets",
    "machine learning": "The primary technical requirement for the role",
    "statistics": "Foundational for model evaluation and result interpretation",
    "data visualization": "Required to communicate insights to non-technical stakeholders",
    "linear algebra": "Needed to deeply understand how ML algorithms work",
    "deep learning": "Powers modern AI applications including NLP and computer vision",
    "r": "Statistical computing language widely used in research roles",
    "excel": "Standard tool for business-side data analysis and reporting",
    "power bi": "Enterprise BI tool for dashboard creation and data storytelling",
    "tableau": "Industry-standard visualization platform for analysts",
    "nlp": "Enables processing and understanding of unstructured text data",
    "docker": "Packages models into portable containers for deployment",
    "git": "Version control — mandatory for any collaborative technical role",
    "spark": "Handles large-scale distributed data processing",
    "communication": "Critical for translating technical findings to business teams",
    "leadership": "Required for senior and lead-level roles across all functions",
}

