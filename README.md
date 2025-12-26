# JD-Brief-Generation-Variations

Brief generated on 10 JDs based on different Temperature thresholds (0.3, 0.5, 0.7).

## Overview

This repository contains the results of an experiment testing how different temperature settings affect AI-generated recruiter briefs. 10 diverse job descriptions from various industries were processed through a brief generator at three temperature levels.

## Job Descriptions Tested

| # | Role | Domain |
|---|------|--------|
| 1 | AI Platform Engineer | Technology/AI |
| 2 | Head of Applications Service Management | IT Management |
| 3 | QA Engineer | Quality Assurance |
| 4 | Senior Marketing Manager | Marketing/CPG |
| 5 | Senior Data Scientist | Data Science/FinTech |
| 6 | Registered Nurse - Emergency | Healthcare |
| 7 | Senior Financial Analyst | Finance/FP&A |
| 8 | Senior Project Manager | Construction |
| 9 | HR Business Partner | Human Resources |
| 10 | Enterprise Sales Representative | Sales/Cybersecurity |

## Temperature Settings

- **0.3 (Low)**: More focused, consistent, deterministic output
- **0.5 (Medium)**: Balanced creativity and consistency
- **0.7 (High)**: More creative, varied output

## Repository Structure

```
├── jds/                                    # Original Job Descriptions (10 files)
│   ├── 01_ai_platform_engineer.txt
│   ├── 02_head_of_applications.txt
│   ├── 03_qa_engineer.txt
│   ├── 04_marketing_manager.txt
│   ├── 05_data_scientist.txt
│   ├── 06_registered_nurse.txt
│   ├── 07_financial_analyst.txt
│   ├── 08_project_manager.txt
│   ├── 09_hr_business_partner.txt
│   └── 10_sales_representative.txt
│
├── outputs/                                # Generated Briefs (30 files total)
│   ├── temp_0.3/                          # 10 briefs at temperature 0.3
│   ├── temp_0.5/                          # 10 briefs at temperature 0.5
│   └── temp_0.7/                          # 10 briefs at temperature 0.7
│
├── JD_Brief_Comprehensive_Results.docx    # Full detailed results document
├── JD_Brief_Summary_Analysis.docx         # Summary and analysis document
└── README.md
```

## Documents

### JD_Brief_Comprehensive_Results.docx
Contains:
- All 10 original job descriptions
- All 30 generated briefs organized by JD and temperature
- Full detailed output for each combination

### JD_Brief_Summary_Analysis.docx
Contains:
- Executive summary
- Methodology overview
- Word count statistics table
- Key observations about temperature impact
- Recommendations for different use cases
- Brief excerpts comparison

## Key Findings

1. **Lower temperatures (0.3)** produce more structured, consistent outputs with standard formatting
2. **Medium temperatures (0.5)** provide a balance between consistency and natural variation
3. **Higher temperatures (0.7)** may introduce more creative phrasing and varied explanations
4. All temperature settings produce comprehensive briefs suitable for external recruiters

## Usage

The briefs are designed to help non-technical external recruiters understand complex job requirements in simple language, enabling them to find the best candidates for each role.
