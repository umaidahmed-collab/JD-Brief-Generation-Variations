"""
Prompts for JD to Brief conversion.
"""

BRIEF_GENERATION_PROMPT = """I am giving you a JD. I want you to help me create a very comprehensive brief for my recruiter, who is not technical and is an external recruiter who does not even understand the context of the company and role.

To create this brief ask me everything that you possibly want to so that I can share a very detailed brief, with my recruiter which enables him to find the best candidates.

The brief should be comprehensive, use simple language, avoid jargon, and explain any technical terms in plain English so a non-technical external recruiter can fully understand the role and find the right candidates.

---

**JOB DESCRIPTION:**

{job_description}

---

Now create the comprehensive recruiter brief:
"""
