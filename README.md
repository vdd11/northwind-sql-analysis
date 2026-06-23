# Northwind Analytics: Automated BI & Corporate Risk Pipeline

An end-to-end, engineering-first data pipeline that transforms relational database schemas into production-grade business intelligence assets. This system automates quantitative RFM customer segmentation, detects supply chain bottlenecks, and calculates market concentration risks using corporate portfolio models.

---

## 🚀 Key Features

* **Database Lifecycle Management:** Features an automated ingestion routine (`load_northwind.py`) to handle target database seeding and initial schema construction.
* **Quantitative RFM Segmentation Engine:** Extracts raw customer order frequencies, spending patterns, and recency timelines using advanced SQL window functions (`NTILE(5)`), mapping accounts into actionable business segments.
* **Advanced Visualization Suite:**
  * *RFM Scatter Map:* Features a custom inverted X-axis (most recent buyers on the right) and log-scaled monetary Y-axis to clearly reveal account distributions without "whale account" scale compression. Includes pixel-offset pointer annotations to prevent text overlap.
  * *Behavioral Heatmap:* Quantifies core operational metrics (averages across spend, count, and recency) for seamless executive assessment.
* **Automated Corporate Risk Assessment Module:** Calculates the Herfindahl-Hirschman Index (HHI) for both revenue streams and product catalogs to instantly flag portfolio vulnerabilities, "Whale account" exposures (inflows crossing >10%), and international shipping corridor latency hotspots.

---

## 📁 Repository Architecture

```text
northwind-sql-analysis-/
│
├── .env.example              # Template configuration for database credentials
├── .gitignore                # Production rules to block credential leaks
├── README.md                 # System overview and deployment documentation
├── requirements.txt          # Python ecosystem package dependencies
│
├── notebooks/                # Exploratory research & prototype code
│   └── 01_exploration.ipynb  # Initial database exploration and insight mapping
│
├── scripts/                  # Executable pipeline modules
│   ├── load_northwind.py     # Database initialization and raw data ingestion script
│   └── generate_report.py    # Production orchestration script (ETL, Viz, Risk Engine)
│
└── outputs/                  # Auto-generated analytical assets
    └── .gitkeep              # Tracking placeholder for the local output disk
